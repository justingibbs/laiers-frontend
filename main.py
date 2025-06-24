import os
import json
import logging
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

import httpx
from fastapi import FastAPI, Request, Form, HTTPException, Cookie, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.adk.cli.fast_api import get_fast_api_app
import firebase_admin
from firebase_admin import credentials, auth
from utils.firestore import FirestoreService
from utils.middleware import MaintenanceModeMiddleware

# Load environment variables
load_dotenv()

# Environment Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "config/firebase-credentials.json")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
ADK_BUCKET_NAME = os.getenv("ADK_BUCKET_NAME")
PORT = int(os.getenv("PORT", 8000))  # Cloud Run uses PORT env var

# Dynamic base URL for ADK endpoints - works in both local and Cloud Run
def get_base_url():
    if ENVIRONMENT == "production":
        # In Cloud Run, use localhost with the actual port
        return f"http://localhost:{PORT}"
    else:
        # In development, use the standard localhost:8000
        return "http://localhost:8000"

BASE_URL = get_base_url()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if ENVIRONMENT == "development" else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load Firebase Web Config
def load_firebase_web_config():
    # In production, try Secret Manager first
    if ENVIRONMENT == "production":
        try:
            from utils.secrets import load_firebase_config_from_secrets
            config = load_firebase_config_from_secrets()
            if config:
                logger.info("Web Config loaded successfully from Secret Manager")
                return config
        except ImportError:
            logger.warning("Secret Manager utilities not available")
        except Exception as e:
            logger.error(f"Error loading from Secret Manager: {e}")
    
    # Fallback 1: Try to load from file (for local development)
    try:
        with open("config/firebase-web-config.json", "r") as f:
            config = json.load(f)
            logger.debug("Web Config loaded successfully from file")
            return config
    except FileNotFoundError:
        logger.info("firebase-web-config.json not found, trying environment variables...")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing web config file: {e}")
    
    # Fallback 2: Try environment variables
    try:
        config = {
            "apiKey": os.getenv("FIREBASE_API_KEY"),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
            "projectId": os.getenv("GOOGLE_CLOUD_PROJECT"),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.getenv("FIREBASE_APP_ID")
        }
        
        # Check if all required fields are present
        if all(config.values()):
            logger.info("Web Config loaded successfully from environment variables")
            return config
        else:
            missing_vars = [k for k, v in config.items() if not v]
            logger.warning(f"Missing Firebase environment variables: {missing_vars}")
    except Exception as e:
        logger.error(f"Error loading web config from environment: {e}")
    
    logger.warning("Firebase client authentication will not work - no valid config found")
    return {}

# Get project ID from web config or environment
web_config = load_firebase_web_config()
PROJECT_ID = web_config.get('projectId') or GOOGLE_CLOUD_PROJECT

if not PROJECT_ID:
    logger.error("Firebase project ID not found in web config or GOOGLE_CLOUD_PROJECT environment variable")
    logger.error(f"web_config: {web_config}")
    logger.error(f"GOOGLE_CLOUD_PROJECT: {GOOGLE_CLOUD_PROJECT}")
    raise ValueError("Firebase project ID not found. Set GOOGLE_CLOUD_PROJECT environment variable.")

logger.info(f"Using Firebase project ID: {PROJECT_ID}")

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    try:
        if ENVIRONMENT == "production":
            # Use Application Default Credentials in production
            cred = credentials.ApplicationDefault()
            logger.info("Using Application Default Credentials for Firebase")
        else:
            # Use service account file in development
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            logger.info(f"Using service account file: {FIREBASE_CREDENTIALS_PATH}")
        
        firebase_admin.initialize_app(cred, {'projectId': PROJECT_ID})
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Firebase Admin SDK: {e}")
        raise

# Initialize Firestore Service
try:
    firestore_service = FirestoreService()
    logger.info("Firestore service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firestore service: {e}")
    raise

# Create the main FastAPI app for your custom routes
app = FastAPI(title="Job Matching App")

# Add maintenance mode middleware
app.add_middleware(MaintenanceModeMiddleware)

# Add custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.url}: {exc.errors()}")
    return HTMLResponse(content=f"""
    <div style="color: red; padding: 1rem; border: 1px solid red; border-radius: 0.25rem; margin: 1rem 0;">
        <p><strong>❌ Form Validation Error</strong></p>
        <p>Please check your form data. Details: {exc.errors()}</p>
    </div>
    """, status_code=422)

# Initialize templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount three independent ADK agents
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logger.info(f"Looking for agents in directory: {BASE_DIR}")

try:
    # Mount dashboard agent (job_matching_agent)
    dashboard_app = get_fast_api_app(
        agents_dir=os.path.join(BASE_DIR, "job_matching_agent"),
        allow_origins=["*"] if ENVIRONMENT == "development" else [],
        web=True,  # This enables the dev UI for dashboard agent
        trace_to_cloud=False
    )
    app.mount("/adk/dashboard", dashboard_app, name="adk-dashboard")
    logger.info("Dashboard agent mounted under /adk/dashboard")
    
    # Mount job posting agent
    posting_app = get_fast_api_app(
        agents_dir=os.path.join(BASE_DIR, "job_posting_agent"),
        allow_origins=["*"] if ENVIRONMENT == "development" else [],
        web=False,  # No dev UI for specialized agents
        trace_to_cloud=False
    )
    app.mount("/adk/posting", posting_app, name="adk-posting")
    logger.info("Job posting agent mounted under /adk/posting")
    
    # Mount assessment agent
    assessment_app = get_fast_api_app(
        agents_dir=os.path.join(BASE_DIR, "assessment_agent"),
        allow_origins=["*"] if ENVIRONMENT == "development" else [],
        web=False,  # No dev UI for specialized agents
        trace_to_cloud=False
    )
    app.mount("/adk/assessment", assessment_app, name="adk-assessment")
    logger.info("Assessment agent mounted under /adk/assessment")
    
    # For backward compatibility, also mount the dashboard agent under /adk
    app.mount("/adk", dashboard_app, name="adk-legacy")
    logger.info("Legacy ADK mount maintained for backward compatibility")
    
except Exception as e:
    logger.error(f"Failed to create/mount ADK apps: {e}")
    raise

# Utility Functions
def parse_opportunity_from_response(response_text: str) -> dict:
    """Parse structured opportunity data from agent response"""
    try:
        # Extract the structured data between OPPORTUNITY_READY markers
        pattern = r'OPPORTUNITY_READY\s*(.*?)(?=```|$)'
        match = re.search(pattern, response_text, re.DOTALL)
        
        if not match:
            raise ValueError("No OPPORTUNITY_READY section found")
        
        data_section = match.group(1).strip()
        
        # Parse each field
        result = {}
        
        # Extract title
        title_match = re.search(r'Title:\s*(.+)', data_section)
        result['title'] = title_match.group(1).strip() if title_match else ""
        
        # Extract description
        desc_match = re.search(r'Description:\s*(.+?)(?=\nRequirements:|$)', data_section, re.DOTALL)
        result['description'] = desc_match.group(1).strip() if desc_match else ""
        
        # Extract requirements
        req_match = re.search(r'Requirements:\s*(.+?)(?=\nLocation:|$)', data_section, re.DOTALL)
        result['requirements'] = req_match.group(1).strip() if req_match else ""
        
        # Extract location
        loc_match = re.search(r'Location:\s*(.+)', data_section)
        result['location'] = loc_match.group(1).strip() if loc_match else ""
        
        # Extract employment type
        emp_match = re.search(r'Employment Type:\s*(.+)', data_section)
        result['employment_type'] = emp_match.group(1).strip() if emp_match else "full-time"
        
        # Extract salary range
        sal_match = re.search(r'Salary Range:\s*(.+)', data_section)
        salary = sal_match.group(1).strip() if sal_match else ""
        if salary and salary.lower() != "not specified":
            result['salary_range'] = salary
        
        # Extract survey questions
        questions = []
        question_pattern = r'(\d+)\.\s*(.+?)(?=\n\d+\.|$)'
        question_matches = re.findall(question_pattern, data_section, re.DOTALL)
        
        for _, question_text in question_matches:
            questions.append({
                "question": question_text.strip(),
                "type": "text",
                "required": True
            })
        
        result['survey_questions'] = questions
        
        # Validate required fields
        required_fields = ['title', 'description', 'requirements', 'location', 'employment_type']
        missing_fields = [field for field in required_fields if not result.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        if len(questions) < 2:
            raise ValueError("At least 2 survey questions are required")
        
        return result
        
    except Exception as e:
        logger.error(f"Error parsing opportunity data: {e}")
        raise ValueError(f"Failed to parse opportunity: {str(e)}")

# Auth Helper Functions
async def get_current_user(session_token: str = Cookie(None)) -> dict | None:
    """Get current user from session token"""
    if not session_token:
        return None
    
    try:
        decoded_token = auth.verify_session_cookie(session_token, check_revoked=True)
        return decoded_token
    except Exception as e:
        logger.error(f"Error verifying session cookie: {e}")
        return None

async def require_auth(session_token: str = Cookie(None)) -> dict:
    """Require authentication, redirect to login if not authenticated"""
    user = await get_current_user(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def optional_auth(session_token: str = Cookie(None)) -> dict | None:
    """Optional authentication for pages that work with or without login"""
    return await get_current_user(session_token)

# Custom Routes - Your main application interface
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request, user = Depends(optional_auth)):
    """Landing page - redirect to dashboard if logged in, otherwise show landing"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    try:
        return templates.TemplateResponse("landing.html", {
            "request": request,
            "firebase_config": web_config
        })
    except Exception as e:
        logger.error(f"Error loading landing page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user_type: str = "talent", user = Depends(optional_auth)):
    """Registration page - redirect if already logged in"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    if user_type not in ["company", "talent"]:
        user_type = "talent"
    return templates.TemplateResponse("register.html", {
        "request": request,
        "user_type": user_type,
        "firebase_config": web_config
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user = Depends(optional_auth)):
    """Login page - redirect if already logged in"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "firebase_config": web_config
    })

@app.post("/api/register")
async def register(request: Request):
    """Handle registration with Firebase - supports both JSON and Form data"""
    try:
        # Check content type to determine how to parse data
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # Handle JSON data from landing page (talent users only)
            data = await request.json()
            user_type = data.get('userType')  # Note: camelCase from JavaScript
            email = data.get('email')
            id_token = data.get('idToken')
            company_id = None
            
            logger.info(f"JSON Registration attempt - Email: {email}, User Type: {user_type}")
            
            if not id_token or user_type not in ['company', 'talent']:
                raise HTTPException(status_code=400, detail="Invalid registration data")
                
            # Company users from landing page should be redirected, not processed here
            if user_type == 'company':
                raise HTTPException(status_code=400, detail="Company registration requires company selection")
                
            # Verify the ID token
            try:
                decoded_token = auth.verify_id_token(id_token)
                user_id = decoded_token['uid']
                logger.info(f"Token verified - UID: {user_id}")
            except Exception as e:
                logger.error(f"Token verification error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        else:
            # Handle form data from registration page
            form_data = await request.form()
            user_type = form_data.get('user_type')
            email = form_data.get('email')
            password = form_data.get('password')
            confirm_password = form_data.get('confirm_password')
            name = form_data.get('name')
            company_id = form_data.get('company_id')
            
            logger.info(f"Form Registration attempt - Email: {email}, User Type: {user_type}, Company ID: {company_id}")
            
            if user_type not in ['company', 'talent']:
                logger.error(f"Invalid user type: {user_type}")
                return HTMLResponse(content=f"""
                <div style="color: red; padding: 1rem; border: 1px solid red; border-radius: 0.25rem; margin: 1rem 0;">
                    <p><strong>❌ Registration Failed</strong></p>
                    <p>Invalid user type</p>
                </div>
                """, status_code=200)
            
            # For company users, validate company selection
            if user_type == 'company' and not company_id:
                logger.error(f"Missing company_id for company user. Received: {company_id}")
                return HTMLResponse(content=f"""
                <div style="color: red; padding: 1rem; border: 1px solid red; border-radius: 0.25rem; margin: 1rem 0;">
                    <p><strong>❌ Registration Failed</strong></p>
                    <p>Company selection is required</p>
                </div>
                """, status_code=200)
            
            try:
                # Create the user in Firebase Auth
                user_record = auth.create_user(
                    email=email,
                    password=password,
                    display_name=name
                )
                user_id = user_record.uid
                logger.info(f"Created Firebase user - UID: {user_id}")
            except Exception as e:
                logger.error(f"Firebase user creation error: {e}")
                # Return HTML error response for form requests (status 200 so HTMX processes it)
                error_message = str(e)
                if "EMAIL_EXISTS" in error_message:
                    error_message = "An account with this email already exists. Please use a different email or try signing in."
                
                return HTMLResponse(content=f"""
                <div style="color: red; padding: 1rem; border: 1px solid red; border-radius: 0.25rem; margin: 1rem 0;">
                    <p><strong>❌ Registration Failed</strong></p>
                    <p>{error_message}</p>
                </div>
                """, status_code=200)
        
        # Create user profile in Firestore
        profile_created = await firestore_service.create_user_profile(user_id, email, user_type, company_id)
        if not profile_created:
            # If Firestore profile creation fails, delete the Firebase user
            try:
                auth.delete_user(user_id)
            except Exception as e:
                logger.error(f"Failed to clean up Firebase user after Firestore error: {e}")
            # Return HTML error response for form requests (status 200 so HTMX processes it)
            return HTMLResponse(content=f"""
            <div style="color: red; padding: 1rem; border: 1px solid red; border-radius: 0.25rem; margin: 1rem 0;">
                <p><strong>❌ Registration Failed</strong></p>
                <p>Failed to create user profile. Please try again.</p>
            </div>
            """, status_code=200)
        
        logger.info(f"Registration successful for user: {email}")
        
        # Return appropriate response based on request type
        if "application/json" in content_type:
            # JSON response for Firebase Auth flow (talent users)
            # Create session cookie for JSON requests
            if 'id_token' in locals():
                expires_in = timedelta(days=14)
                session_cookie = auth.create_session_cookie(id_token, expires_in=expires_in)
                
                response = Response(content='{"success": true, "redirect": "/dashboard"}', media_type="application/json")
                response.set_cookie(
                    key="session_token",
                    value=session_cookie,
                    max_age=int(expires_in.total_seconds()),
                    httponly=True,
                    secure=ENVIRONMENT == "production"
                )
                return response
            else:
                return {"success": True, "redirect": "/dashboard"}
        else:
            # HTML response for HTMX form flow (company users)
            return HTMLResponse(content=f"""
            <div style="color: green; padding: 1rem; border: 1px solid green; border-radius: 0.25rem; margin: 1rem 0;">
                <p><strong>✅ Registration Successful!</strong></p>
                <p>Account created for {email}. You can now <a href="/login">sign in</a>.</p>
            </div>
            """)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        logger.error(f"Exception type: {type(e)}")
        
        # Return appropriate error response based on request type
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            raise HTTPException(status_code=400, detail=str(e))
        else:
            return HTMLResponse(content=f"""
            <div style="color: red; padding: 1rem; border: 1px solid red; border-radius: 0.25rem; margin: 1rem 0;">
                <p><strong>❌ Registration Failed</strong></p>
                <p>{str(e)}</p>
            </div>
            """)

@app.post("/api/login")
async def login(request: Request):
    """Handle login with Firebase"""
    try:
        data = await request.json()
        id_token = data.get('idToken')
        
        if not id_token:
            raise HTTPException(status_code=400, detail="No ID token provided")
        
        # Verify the ID token
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token.get('uid')
            logger.info(f"Login successful - UID: {user_id}")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # Create session cookie
        expires_in = timedelta(days=14)
        session_cookie = auth.create_session_cookie(id_token, expires_in=expires_in)
        
        response = Response(content='{"success": true, "redirect": "/dashboard"}', media_type="application/json")
        response.set_cookie(
            key="session_token",
            value=session_cookie,
            max_age=int(expires_in.total_seconds()),
            httponly=True,
            secure=ENVIRONMENT == "production"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user = Depends(require_auth)):
    """Dashboard page with chat interface"""
    # Get user profile from Firestore
    user_profile = await firestore_service.get_user_profile(user['uid'])
    if not user_profile:
        logger.error(f"No profile found for user: {user['uid']}")
        return RedirectResponse(url="/register", status_code=302)
    
    logger.info(f"Dashboard accessed by user: {user.get('email')}")
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "user_profile": user_profile,
        "firebase_config": web_config
    })

@app.get("/company/{company_id}", response_class=HTMLResponse)
async def company_page(request: Request, company_id: str, user = Depends(require_auth)):
    """Company page - only accessible to users affiliated with the company"""
    # Get user profile to check company affiliation
    user_profile = await firestore_service.get_user_profile(user['uid'])
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Check if user is affiliated with this company
    if user_profile.get('user_type') != 'company' or user_profile.get('company_id') != company_id:
        raise HTTPException(status_code=403, detail="You don't have access to this company page")
    
    # Get company information
    company_info = await firestore_service.get_company_info(company_id)
    if not company_info:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get opportunities for this company
    opportunities = await firestore_service.get_opportunities_by_company(company_id)
    
    logger.info(f"Company page accessed: {company_id} by user: {user.get('email')}")
    return templates.TemplateResponse("company.html", {
        "request": request,
        "user": user,
        "user_profile": user_profile,
        "company": company_info,
        "opportunities": opportunities,
        "firebase_config": web_config
    })

@app.get("/company/{company_id}/opportunities/create", response_class=HTMLResponse)
async def create_opportunity_page(request: Request, company_id: str, user = Depends(require_auth)):
    """Opportunity creation page - chat interface for creating opportunities"""
    # Get user profile to check company affiliation
    user_profile = await firestore_service.get_user_profile(user['uid'])
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Check if user is affiliated with this company
    if user_profile.get('user_type') != 'company' or user_profile.get('company_id') != company_id:
        raise HTTPException(status_code=403, detail="You don't have access to create opportunities for this company")
    
    # Get company information
    company_info = await firestore_service.get_company_info(company_id)
    if not company_info:
        raise HTTPException(status_code=404, detail="Company not found")
    
    logger.info(f"Opportunity creation page accessed for company: {company_id} by user: {user.get('email')}")
    return templates.TemplateResponse("create_opportunity.html", {
        "request": request,
        "user": user,
        "user_profile": user_profile,
        "company": company_info,
        "firebase_config": web_config
    })

@app.get("/opportunities/{opportunity_id}", response_class=HTMLResponse)
async def opportunity_detail(request: Request, opportunity_id: str, user = Depends(require_auth)):
    """Opportunity detail page with application form for talent users and assessment for company users"""
    # Get opportunity
    opportunity = await firestore_service.get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Get user profile
    user_profile = await firestore_service.get_user_profile(user['uid'])
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Check if user has already applied (for talent users)
    has_applied = False
    if user_profile.get('user_type') == 'talent':
        has_applied = await firestore_service.check_existing_application(opportunity_id, user['uid'])
    
    # Get applications count for company users who own this opportunity
    applications_count = 0
    if user_profile.get('user_type') == 'company' and user_profile.get('company_id') == opportunity.get('company_id'):
        applications = await firestore_service.get_applications_by_opportunity(opportunity_id)
        applications_count = len(applications)
    
    logger.info(f"Opportunity detail accessed: {opportunity_id} by user: {user.get('email')}")
    return templates.TemplateResponse("opportunity_detail.html", {
        "request": request,
        "user": user,
        "user_profile": user_profile,
        "opportunity": opportunity,
        "has_applied": has_applied,
        "applications_count": applications_count,
        "firebase_config": web_config
    })

@app.get("/opportunities", response_class=HTMLResponse)
async def opportunities_list(request: Request, user = Depends(require_auth)):
    """List all available opportunities for talent users to browse"""
    # Get user profile
    user_profile = await firestore_service.get_user_profile(user['uid'])
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Get all active opportunities
    all_opportunities = await firestore_service.get_all_opportunities()
    
    logger.info(f"Opportunities list accessed by user: {user.get('email')} (found {len(all_opportunities)} opportunities)")
    return templates.TemplateResponse("opportunities_list.html", {
        "request": request,
        "user": user,
        "user_profile": user_profile,
        "opportunities": all_opportunities,
        "firebase_config": web_config
    })

@app.post("/api/chat")
async def chat_with_agent(
    request: Request,
    message: str = Form(...),
    user = Depends(require_auth)
):
    """Chat with the job matching agent via HTMX"""
    try:
        user_profile = await firestore_service.get_user_profile(user['uid'])
        if not user_profile:
            raise HTTPException(status_code=400, detail="User profile not found")
        
        # Get agent name from the mounted ADK app
        from job_matching_agent.agent import root_agent
        agent_name = root_agent.name
        
        # Prepare session and user IDs
        session_id = f"session_{user['uid']}"
        user_id = user["uid"]
        
        # Add context about user type to the message
        user_type = user_profile.get("user_type", "talent")
        contextual_message = f"[User type: {user_type}] {message}"
        
        # First, create or ensure session exists (call ADK endpoint directly)
        async with httpx.AsyncClient(timeout=30.0) as client:  # Increased timeout to 30 seconds
            # Create session first - this is required before sending messages
            session_url = f"{BASE_URL}/adk/apps/{agent_name}/users/{user_id}/sessions/{session_id}"
            try:
                session_response = await client.post(session_url, 
                    json={"state": {}}
                )
                logger.debug(f"Session creation response: {session_response.status_code}")
                
                # If session creation fails (and it's not because it already exists), handle the error
                if session_response.status_code not in [200, 400]:  # 400 might mean session already exists
                    logger.error(f"Session creation failed: {session_response.text}")
                    
            except Exception as e:
                logger.debug(f"Session creation note: {e}")
                # Continue - session might already exist
            
            # Send message to agent via ADK's /run endpoint
            run_url = f"{BASE_URL}/adk/run"
            run_payload = {
                "appName": agent_name,        # camelCase, not snake_case
                "userId": user_id,            # camelCase, not snake_case  
                "sessionId": session_id,      # camelCase, not snake_case
                "newMessage": {               # camelCase, not snake_case
                    "role": "user",
                    "parts": [{"text": contextual_message}]
                },
                "streaming": False            # Add required streaming field
            }
            
            logger.debug(f"Sending payload to {run_url}: {run_payload}")
            
            run_response = await client.post(run_url, json=run_payload)
            
            # Log the error details if request fails
            if run_response.status_code != 200:
                error_details = run_response.text
                logger.error(f"ADK run endpoint error {run_response.status_code}: {error_details}")
                # Try to get more details from the response
                try:
                    error_json = run_response.json()
                    logger.error(f"Error JSON: {error_json}")
                except:
                    pass
                raise httpx.HTTPStatusError(f"ADK endpoint error: {error_details}", request=run_response.request, response=run_response)
            
            # Parse the response events
            events = run_response.json()
            logger.debug(f"ADK response events: {events}")
            
            final_response = "I'm sorry, I couldn't process that request."
            
            # Look for the final response in the events
            if isinstance(events, list):
                for event in events:
                    logger.debug(f"Processing event: {event}")
                    if event.get("turnComplete") and event.get("content"):
                        content = event["content"]
                        if content.get("parts"):
                            for part in content["parts"]:
                                if part.get("text"):
                                    final_response = part["text"]
                                    break
                            if final_response != "I'm sorry, I couldn't process that request.":
                                break
                    # Also check for other possible response formats
                    elif event.get("content") and event.get("content", {}).get("parts"):
                        content = event["content"]
                        for part in content["parts"]:
                            if part.get("text"):
                                final_response = part["text"]
                                break
        
        # Return HTMX partial template
        return templates.TemplateResponse("components/chat_message.html", {
            "request": request,
            "user_message": message,
            "agent_response": final_response,
            "timestamp": datetime.now()
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return templates.TemplateResponse("components/chat_error.html", {
            "request": request,
            "error": "Failed to process message. Please try again."
        })

@app.post("/api/opportunities/create")
async def create_opportunity_chat(
    request: Request,
    message: str = Form(...),
    company_id: str = Form(...),
    user = Depends(require_auth)
):
    """Chat with agent for opportunity creation via HTMX"""
    try:
        user_profile = await firestore_service.get_user_profile(user['uid'])
        if not user_profile:
            raise HTTPException(status_code=400, detail="User profile not found")
        
        # Verify user has access to this company
        if user_profile.get('user_type') != 'company' or user_profile.get('company_id') != company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Use dedicated job posting agent
        agent_name = "job_posting_agent"
        
        # Prepare session and user IDs
        session_id = f"posting_session_{user['uid']}_{company_id}"
        user_id = user["uid"]
        
        # Get company info for context
        company_info = await firestore_service.get_company_info(company_id)
        company_name = company_info.get('name', 'Unknown Company') if company_info else 'Unknown Company'
        
        # Send message to job posting agent via ADK
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create session with context
            session_url = f"{BASE_URL}/adk/posting/apps/{agent_name}/users/{user_id}/sessions/{session_id}"
            session_headers = {
                "X-User-Type": "company",
                "X-User-ID": user_id,
                "X-Company-ID": company_id,
                "X-Company-Name": company_name,
                "Content-Type": "application/json"
            }
            
            try:
                session_response = await client.post(session_url, 
                    json={"state": {"company_id": company_id, "company_name": company_name, "created_by": user_id}}, 
                    headers=session_headers)
                logger.debug(f"Posting session creation response: {session_response.status_code}")
            except Exception as e:
                logger.debug(f"Posting session creation note: {e}")
            
            # Send message to agent
            run_url = f"{BASE_URL}/adk/posting/run"
            run_payload = {
                "appName": agent_name,
                "userId": user_id,
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": message}]
                },
                "streaming": False
            }
            
            logger.debug(f"Sending job posting payload: {run_payload}")
            run_response = await client.post(run_url, json=run_payload, headers=session_headers)
            
            if run_response.status_code != 200:
                error_details = run_response.text
                logger.error(f"Job posting ADK error {run_response.status_code}: {error_details}")
                raise httpx.HTTPStatusError(f"ADK endpoint error: {error_details}", request=run_response.request, response=run_response)
            
            # Parse the response
            events = run_response.json()
            final_response = "Hello! I'm your specialized job posting assistant. Let's create an amazing opportunity together!"
            
            if isinstance(events, list):
                for event in events:
                    if event.get("turnComplete") and event.get("content"):
                        content = event["content"]
                        if content.get("parts"):
                            for part in content["parts"]:
                                if part.get("text"):
                                    final_response = part["text"]
                                    break
                            if final_response != "I'm ready to help you create an opportunity. Please provide details about the job position.":
                                break
                    elif event.get("content") and event.get("content", {}).get("parts"):
                        content = event["content"]
                        for part in content["parts"]:
                            if part.get("text"):
                                final_response = part["text"]
                                break
        
        # Check if agent provided structured opportunity data
        if "OPPORTUNITY_READY" in final_response:
            try:
                opportunity_data = parse_opportunity_from_response(final_response)
                opportunity_data.update({
                    "company_id": company_id,
                    "company_name": company_name,
                    "created_by": user_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "status": "active"
                })
                
                # Create opportunity in Firestore
                opportunity_id = await firestore_service.create_opportunity(opportunity_data)
                
                if opportunity_id:
                    logger.info(f"Successfully created opportunity {opportunity_id} from agent response")
                    final_response = f"""🎉 **Opportunity Created Successfully!**

**"{opportunity_data.get('title')}"** has been posted and is now live on your company page.

**Opportunity ID:** `{opportunity_id}`

**Next Steps:**
• [View your opportunity](/opportunities/{opportunity_id}) 
• [Go to company dashboard](/company/{company_id})
• [Create another opportunity](/company/{company_id}/opportunities/create)

Candidates can now discover and apply to this position!"""
                else:
                    final_response = "❌ **Creation Failed**: Unable to save opportunity to database. Please try again."
                    
            except Exception as parse_error:
                logger.error(f"Failed to parse opportunity data: {parse_error}")
                final_response = f"❌ **Parsing Error**: {final_response}\n\n*Note: Please try rephrasing your request.*"
        
        logger.debug(f"Job posting agent response: {final_response[:200]}...")
        
        # Return HTMX partial template
        return templates.TemplateResponse("components/chat_message.html", {
            "request": request,
            "user_message": message,
            "agent_response": final_response,
            "timestamp": datetime.now()
        })
        
    except Exception as e:
        logger.error(f"Opportunity creation chat error: {e}")
        return templates.TemplateResponse("components/chat_error.html", {
            "request": request,
            "error": "Failed to process opportunity creation message. Please try again."
        })

@app.post("/api/opportunities/{opportunity_id}/apply")
async def submit_application(
    request: Request,
    opportunity_id: str,
    user = Depends(require_auth)
):
    """Submit application for an opportunity via HTMX"""
    try:
        # Get form data
        form_data = await request.form()
        
        # Get user profile
        user_profile = await firestore_service.get_user_profile(user['uid'])
        if not user_profile or user_profile.get('user_type') != 'talent':
            raise HTTPException(status_code=403, detail="Only talent users can apply to opportunities")
        
        # Get opportunity
        opportunity = await firestore_service.get_opportunity(opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Check if already applied
        has_applied = await firestore_service.check_existing_application(opportunity_id, user['uid'])
        if has_applied:
            return HTMLResponse(content="""
                <div class="application-result already-applied">
                    <p><strong>❌ Already Applied</strong></p>
                    <p>You have already submitted an application for this opportunity.</p>
                    <div class="opportunity-actions">
                        <a href="/dashboard" class="action-button secondary-button">Return to Dashboard</a>
                    </div>
                </div>
            """)
        
        # Collect survey responses
        survey_responses = {}
        survey_questions = opportunity.get('survey_questions', [])
        
        for i, question in enumerate(survey_questions):
            question_key = f"question_{i}"
            response = form_data.get(question_key, "").strip()
            if question.get('required', True) and not response:
                raise HTTPException(status_code=400, detail=f"Required question not answered: {question.get('question', f'Question {i+1}')}")
            survey_responses[question_key] = response
        
        # Create application data
        application_data = {
            "opportunity_id": opportunity_id,
            "applicant_id": user['uid'],
            "applicant_email": user.get('email'),
            "applicant_name": user_profile.get('profile', {}).get('name') or user.get('email', '').split('@')[0],
            "survey_responses": survey_responses
        }
        
        # Submit application
        application_id = await firestore_service.submit_application(application_data)
        
        if application_id:
            logger.info(f"Application submitted: {application_id} for opportunity: {opportunity_id} by user: {user.get('email')}")
            return HTMLResponse(content=f"""
                <div class="application-result success">
                    <p><strong>🎉 Application Submitted Successfully!</strong></p>
                    <p>Thank you for your interest in <strong>{opportunity.get('title', 'this position')}</strong>!</p>
                    <p>We've received your application and will review it carefully. You'll hear back from us soon.</p>
                    
                    <div class="opportunity-actions">
                        <a href="/dashboard" class="action-button secondary-button">Return to Dashboard</a>
                        <a href="/opportunities" class="action-button primary-button">Browse More Opportunities</a>
                    </div>
                </div>
            """)
        else:
            raise Exception("Failed to create application")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Application submission error: {e}")
        return HTMLResponse(content="""
            <div class="application-result error">
                <p><strong>❌ Application Failed</strong></p>
                <p>There was an error submitting your application. Please try again.</p>
            </div>
        """)

@app.post("/api/logout")
async def logout(request: Request):
    """Logout a user"""
    try:
        session_token = request.cookies.get("session_token")
        if session_token:
            decoded_token = auth.verify_session_cookie(session_token)
            user_id = decoded_token.get('uid')
            if user_id:
                auth.revoke_refresh_tokens(user_id)
                logger.info(f"Firebase tokens revoked for user: {user_id}")
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
    
    response = Response(content='{"success": true, "redirect": "/"}', media_type="application/json")
    response.delete_cookie("session_token")
    return response

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "environment": ENVIRONMENT,
            "firebase_project": PROJECT_ID,
            "adk_mounted": True,
            "maintenance_mode": os.getenv("MAINTENANCE_MODE", "false"),
            "services": {
                "firebase": "ok" if firebase_admin._apps else "not_initialized",
                "firestore": "ok" if firestore_service else "not_initialized"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/_ah/health")
async def app_engine_health():
    """App Engine/Cloud Run health check endpoint"""
    return {"status": "ok"}

@app.get("/api/health")
async def api_health():
    """Alternative health check endpoint"""
    return await health_check()

# Debug route to test ADK integration
@app.get("/debug/adk")
async def debug_adk():
    """Debug endpoint to check ADK integration"""
    try:
        from job_matching_agent.agent import root_agent
        return {
            "agent_name": root_agent.name,
            "agent_model": root_agent.model,
            "adk_dev_ui_url": f"{BASE_URL}/adk/dev-ui/",
            "agent_endpoint": f"/adk/apps/{root_agent.name}/users/test/sessions/test",
            "status": "ADK mounted successfully under /adk"
        }
    except Exception as e:
        return {"error": str(e), "note": "Make sure job_matching_agent directory exists with proper structure"}

@app.get("/debug/secrets")
async def debug_secrets():
    """Debug endpoint to check Secret Manager configuration"""
    try:
        from utils.secrets import get_secret, load_firebase_config_from_secrets
        
        # Test individual secret access
        api_key = get_secret("firebase-api-key")
        auth_domain = get_secret("firebase-auth-domain")
        
        # Test complete config loading
        config = load_firebase_config_from_secrets()
        
        return {
            "status": "ok",
            "environment": ENVIRONMENT,
            "project_id": PROJECT_ID,
            "secret_manager_available": True,
            "api_key_available": bool(api_key),
            "auth_domain_available": bool(auth_domain),
            "complete_config_available": bool(config),
            "config_keys": list(config.keys()) if config else [],
            "timestamp": datetime.now().isoformat()
        }
    except ImportError as e:
        return {
            "status": "error",
            "error": "Secret Manager utilities not available",
            "details": str(e),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Debug secrets error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to see all available routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": getattr(route, 'methods', None),
                "name": getattr(route, 'name', None)
            })
    return {"routes": routes}

@app.get("/debug/adk-docs")
async def debug_adk_docs():
    """Check ADK's API documentation"""
    try:
        async with httpx.AsyncClient() as client:
            # Check what endpoints ADK provides
            docs_response = await client.get(f"{BASE_URL}/adk/docs")
            openapi_response = await client.get(f"{BASE_URL}/adk/openapi.json")
            
            return {
                "docs_status": docs_response.status_code,
                "openapi_status": openapi_response.status_code,
                "openapi_content": openapi_response.json() if openapi_response.status_code == 200 else None
            }
    except Exception as e:
        return {"error": str(e)}

# Test agent discovery
@app.get("/test/agent-discovery")
async def test_agent_discovery():
    """Test if ADK can discover and list our agent"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if ADK can list our agent
            list_apps_url = f"{BASE_URL}/adk/list-apps"
            response = await client.get(list_apps_url)
            
            return {
                "list_apps_status": response.status_code,
                "available_apps": response.json() if response.status_code == 200 else None,
                "response_text": response.text,
                "job_matching_agent_found": "job_matching_agent" in (response.json() if response.status_code == 200 else [])
            }
    except Exception as e:
        return {"error": str(e)}

# Test company functionality
@app.get("/test/companies")
async def test_companies():
    """Test endpoint to see available companies and create test data"""
    companies = firestore_service.get_available_companies()
    
    # Also test getting company info
    company_info = {}
    for company in companies:
        company_data = await firestore_service.get_company_info(company["id"])
        company_info[company["id"]] = company_data
    
    return {
        "available_companies": companies,
        "company_details": company_info,
        "registration_example": {
            "talent_registration": "/register?user_type=talent",
            "company_registration": "/register?user_type=company"
        }
    }

# Test Firestore data
@app.get("/test/firestore-users")
async def test_firestore_users():
    """Debug endpoint to see what users are in Firestore"""
    try:
        # Get all users from Firestore
        users_ref = firestore_service.users_collection
        all_users = []
        
        for doc in users_ref.stream():
            user_data = doc.to_dict()
            all_users.append({
                "id": doc.id,
                "email": user_data.get("email"),
                "user_type": user_data.get("user_type"),
                "company_id": user_data.get("company_id"),
                "company_name": user_data.get("company_name"),
                "created_at": str(user_data.get("created_at"))
            })
        
        return {
            "total_users": len(all_users),
            "users": all_users
        }
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return {"error": str(e)}

# HTMX endpoints for dynamic form fields
@app.get("/api/form-fields/{user_type}")
async def get_form_fields(request: Request, user_type: str):
    """Return form fields based on user type selection"""
    if user_type == "company":
        return HTMLResponse(content="""
        <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" name="email" required>
        </div>
        
        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required>
        </div>
        
        <div class="form-group">
            <label for="confirm_password">Confirm Password</label>
            <input type="password" id="confirm_password" name="confirm_password" required>
        </div>
        
        <div class="form-group">
            <label for="company_id">Select Your Company</label>
            <select name="company_id" required>
                <option value="">Choose a company...</option>
                <option value="company_1">Horizon_Health_Network</option>
                <option value="company_2">BuildWell_Construction_Group</option>
                <option value="company_3">Sparkly_Studios</option>
            </select>
        </div>
        
        <input type="hidden" name="user_type" value="company">
        """)
    else:  # talent
        return HTMLResponse(content="""
        <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" name="email" required>
        </div>
        
        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required>
        </div>
        
        <div class="form-group">
            <label for="confirm_password">Confirm Password</label>
            <input type="password" id="confirm_password" name="confirm_password" required>
        </div>
        
        <div class="form-group">
            <label for="name">Full Name</label>
            <input type="text" name="name" required>
        </div>
        
        <input type="hidden" name="user_type" value="talent">
        """)

# Test page for company flow
@app.get("/test/company-flow")
async def test_company_flow(request: Request):
    """Test page showing the complete company registration flow"""
    return templates.TemplateResponse("test_company_flow.html", {"request": request})

# Test registration form directly
@app.get("/test/register-form")
async def test_register_form():
    """Test endpoint to show a working registration form"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Registration</title>
        <script src="https://unpkg.com/htmx.org@1.9.10"></script>
        <link rel="stylesheet" href="/static/css/styles.css">
    </head>
    <body>
        <div class="auth-container">
            <div class="auth-form">
                <h2>Test Company Registration</h2>
                <form hx-post="/api/register" hx-target="#result" hx-swap="innerHTML">
                    <input type="hidden" name="user_type" value="company">
                    
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input type="email" name="email" value="testuser@example.com" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" name="password" value="test123" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="confirm_password">Confirm Password</label>
                        <input type="password" name="confirm_password" value="test123" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="company_id">Select Your Company</label>
                        <select name="company_id" required>
                            <option value="">Choose a company...</option>
                            <option value="company_1">Company_1</option>
                            <option value="company_2" selected>Company_2</option>
                            <option value="company_3">Company_3</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn-primary">Create Account</button>
                </form>
                <div id="result"></div>
            </div>
        </div>
    </body>
    </html>
    """)

# Test complete ADK flow
@app.get("/test/adk-complete-flow")
async def test_adk_complete_flow():
    """Test the complete ADK flow: create session -> send message"""
    try:
        # Mock data for testing
        agent_name = "job_matching_agent"
        user_id = "test_user_123"
        session_id = "test_session_123"
        message = "Hello, test message"
        
        async with httpx.AsyncClient() as client:
            # Step 1: Create session first
            session_url = f"{BASE_URL}/adk/apps/{agent_name}/users/{user_id}/sessions/{session_id}"
            session_payload = {"state": {}}
            
            logger.info(f"Creating session at: {session_url}")
            session_response = await client.post(session_url, json=session_payload)
            
            session_result = {
                "status_code": session_response.status_code,
                "text": session_response.text
            }
            
            # 400 means session already exists, which is fine - continue with message sending
            if session_response.status_code not in [200, 400]:
                return {
                    "step": "session_creation_failed",
                    "session_result": session_result
                }
            
            # Step 2: Send message to the session
            run_url = f"{BASE_URL}/adk/run"
            run_payload = {
                "appName": agent_name,
                "userId": user_id,
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": message}]
                },
                "streaming": False
            }
            
            logger.info(f"Sending message to: {run_url}")
            run_response = await client.post(run_url, json=run_payload)
            
            return {
                "session_creation": session_result,
                "message_send": {
                    "status_code": run_response.status_code,
                    "payload_sent": run_payload,
                    "response_text": run_response.text,
                    "success": run_response.status_code == 200
                },
                "overall_success": (session_response.status_code in [200, 400]) and run_response.status_code == 200
            }
            
    except Exception as e:
        return {
            "error": str(e),
            "step": "exception_occurred"
        }

@app.get("/test/opportunities/{company_id}")
async def test_opportunities(company_id: str):
    """Debug endpoint to test opportunity retrieval"""
    try:
        opportunities = await firestore_service.get_opportunities_by_company(company_id)
        return {
            "company_id": company_id,
            "opportunities_count": len(opportunities),
            "opportunities": opportunities
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/opportunities/{opportunity_id}/assess")
async def assess_candidates(
    request: Request,
    opportunity_id: str,
    message: str = Form(...),
    user = Depends(require_auth)
):
    """Chat with assessment agent for candidate evaluation via HTMX"""
    try:
        user_profile = await firestore_service.get_user_profile(user['uid'])
        if not user_profile:
            raise HTTPException(status_code=400, detail="User profile not found")
        
        # Get opportunity and verify ownership
        opportunity = await firestore_service.get_opportunity(opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Verify user has access to assess candidates for this opportunity
        if user_profile.get('user_type') != 'company' or user_profile.get('company_id') != opportunity.get('company_id'):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get applications for this opportunity
        applications = await firestore_service.get_applications_by_opportunity(opportunity_id)
        
        # Use dedicated assessment agent
        agent_name = "assessment_agent"
        
        # Prepare session and user IDs
        session_id = f"assessment_session_{user['uid']}_{opportunity_id}"
        user_id = user["uid"]
        
        # Get company info for context
        company_info = await firestore_service.get_company_info(user_profile.get('company_id'))
        company_name = company_info.get('name', 'Unknown Company') if company_info else 'Unknown Company'
        
        # Send message to assessment agent via ADK
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create session with context
            session_url = f"{BASE_URL}/adk/assessment/apps/{agent_name}/users/{user_id}/sessions/{session_id}"
            session_headers = {
                "X-User-Type": "company",
                "X-User-ID": user_id,
                "X-Company-ID": user_profile.get('company_id'),
                "X-Opportunity-ID": opportunity_id,
                "Content-Type": "application/json"
            }
            
            try:
                session_response = await client.post(session_url, 
                    json={"state": {"opportunity_id": opportunity_id, "company_id": user_profile.get('company_id')}}, 
                    headers=session_headers)
                logger.debug(f"Assessment session creation response: {session_response.status_code}")
            except Exception as e:
                logger.debug(f"Assessment session creation note: {e}")
            
            # Send message to agent
            run_url = f"{BASE_URL}/adk/assessment/run"
            run_payload = {
                "appName": agent_name,
                "userId": user_id,
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": message}]
                },
                "streaming": False
            }
            
            logger.debug(f"Sending assessment payload: {run_payload}")
            run_response = await client.post(run_url, json=run_payload, headers=session_headers)
            
            if run_response.status_code != 200:
                error_details = run_response.text
                logger.error(f"Assessment ADK error {run_response.status_code}: {error_details}")
                raise httpx.HTTPStatusError(f"ADK endpoint error: {error_details}", request=run_response.request, response=run_response)
            
            # Parse the response
            events = run_response.json()
            final_response = f"Hello! I'm your candidate assessment specialist. I'm ready to help you evaluate applicants for this opportunity."
            
            if isinstance(events, list):
                for event in events:
                    if event.get("turnComplete") and event.get("content"):
                        content = event["content"]
                        if content.get("parts"):
                            for part in content["parts"]:
                                if part.get("text"):
                                    final_response = part["text"]
                                    break
                            if final_response != f"Hello! I'm your candidate assessment specialist. I'm ready to help you evaluate applicants for this opportunity.":
                                break
                    elif event.get("content") and event.get("content", {}).get("parts"):
                        content = event["content"]
                        for part in content["parts"]:
                            if part.get("text"):
                                final_response = part["text"]
                                break
        
        # Return HTMX partial template
        return templates.TemplateResponse("components/chat_message.html", {
            "request": request,
            "user_message": message,
            "agent_response": final_response,
            "timestamp": datetime.now()
        })
        
    except Exception as e:
        logger.error(f"Assessment chat error: {e}")
        return templates.TemplateResponse("components/chat_error.html", {
            "request": request,
            "error": "Failed to process assessment message. Please try again."
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)