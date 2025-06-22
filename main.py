import os
import json
import logging
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

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if ENVIRONMENT == "development" else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load Firebase Web Config
def load_firebase_web_config():
    try:
        with open("config/firebase-web-config.json", "r") as f:
            config = json.load(f)
            logger.debug("Web Config loaded successfully")
            return config
    except FileNotFoundError:
        logger.warning("firebase-web-config.json not found. Firebase client authentication will not work.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing web config: {e}")
        return {}

# Get project ID from web config or environment
web_config = load_firebase_web_config()
PROJECT_ID = web_config.get('projectId') or GOOGLE_CLOUD_PROJECT

if not PROJECT_ID:
    logger.error("Firebase project ID not found in web config or GOOGLE_CLOUD_PROJECT environment variable")
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

# Get ADK app and mount it under /adk path
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
logger.info(f"Looking for agents in directory: {AGENT_DIR}")

try:
    adk_app = get_fast_api_app(
        agents_dir=AGENT_DIR,
        session_db_url="sqlite:///./sessions.db",
        allow_origins=["*"] if ENVIRONMENT == "development" else [],
        web=True,  # This enables the dev UI
        trace_to_cloud=False
    )
    logger.info("ADK app created successfully")
    logger.info(f"ADK app routes: {[route.path for route in adk_app.routes if hasattr(route, 'path')]}")
    
    # Mount ADK app under /adk prefix
    app.mount("/adk", adk_app, name="adk")
    logger.info("ADK app mounted under /adk")
    
except Exception as e:
    logger.error(f"Failed to create/mount ADK app: {e}")
    raise

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
            session_url = f"http://localhost:8000/adk/apps/{agent_name}/users/{user_id}/sessions/{session_id}"
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
            run_url = "http://localhost:8000/adk/run"
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
        
        # Get agent name from the mounted ADK app
        from job_matching_agent.agent import root_agent
        agent_name = root_agent.name
        
        # Prepare session and user IDs
        session_id = f"opportunity_session_{user['uid']}_{company_id}"
        user_id = user["uid"]
        
        # Add context for opportunity creation
        company_info = await firestore_service.get_company_info(company_id)
        company_name = company_info.get('name', 'Unknown Company') if company_info else 'Unknown Company'
        
        contextual_message = f"[User type: company, Task: create_opportunity, Company: {company_name}, Company ID: {company_id}] {message}"
        
        # Send message to agent via ADK
        async with httpx.AsyncClient(timeout=30.0) as client:  # Increased timeout to 30 seconds
            # Create session first
            session_url = f"http://localhost:8000/adk/apps/{agent_name}/users/{user_id}/sessions/{session_id}"
            try:
                session_response = await client.post(session_url, json={"state": {}})
                logger.debug(f"Opportunity session creation response: {session_response.status_code}")
            except Exception as e:
                logger.debug(f"Opportunity session creation note: {e}")
            
            # Send message to agent
            run_url = "http://localhost:8000/adk/run"
            run_payload = {
                "appName": agent_name,
                "userId": user_id,
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": contextual_message}]
                },
                "streaming": False
            }
            
            logger.debug(f"Sending opportunity creation payload: {run_payload}")
            run_response = await client.post(run_url, json=run_payload)
            
            if run_response.status_code != 200:
                error_details = run_response.text
                logger.error(f"ADK opportunity creation error {run_response.status_code}: {error_details}")
                raise httpx.HTTPStatusError(f"ADK endpoint error: {error_details}", request=run_response.request, response=run_response)
            
            # Parse the response
            events = run_response.json()
            final_response = "I'm ready to help you create an opportunity. Please provide details about the job position."
            
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
        
        # Check if the agent response contains a structured opportunity
        if "OPPORTUNITY_READY:" in final_response:
            try:
                # Parse the structured opportunity data
                lines = final_response.split('\n')
                opportunity_data = {
                    "company_id": company_id,
                    "company_name": company_name,
                    "created_by": user['uid']
                }
                
                survey_questions = []
                current_section = None
                inside_code_block = False
                
                for line in lines:
                    line = line.strip()
                    
                    # Handle code block markers
                    if line.startswith("```"):
                        inside_code_block = not inside_code_block
                        continue
                    
                    # Skip lines outside the code block if we found one
                    if "```" in final_response and not inside_code_block:
                        continue
                    
                    if line.startswith("Title:"):
                        opportunity_data["title"] = line.replace("Title:", "").strip()
                    elif line.startswith("Description:"):
                        # Handle multi-line descriptions
                        desc = line.replace("Description:", "").strip()
                        opportunity_data["description"] = desc
                    elif line.startswith("Requirements:") or line.startswith("Required Skills") or line.startswith("Key Responsibilities:"):
                        # Handle various requirement formats
                        reqs = line.replace("Requirements:", "").replace("Required Skills", "").replace("Key Responsibilities:", "").strip()
                        opportunity_data["requirements"] = reqs
                    elif line.startswith("Location:"):
                        opportunity_data["location"] = line.replace("Location:", "").strip()
                    elif line.startswith("Employment Type:"):
                        opportunity_data["employment_type"] = line.replace("Employment Type:", "").strip()
                    elif line.startswith("Salary Range:") or "salary range:" in line.lower():
                        salary = line.replace("Salary Range:", "").replace("salary range:", "").strip()
                        if salary.lower() not in ["not specified", "n/a", ""]:
                            opportunity_data["salary_range"] = salary
                    elif line.startswith("Survey Questions:"):
                        current_section = "survey"
                    elif current_section == "survey" and line and (line[0].isdigit() or line.startswith("-")):
                        # Extract question text (remove numbering)
                        question_text = line
                        if ". " in question_text:
                            question_text = question_text.split(". ", 1)[1]
                        elif "- " in question_text:
                            question_text = question_text.replace("- ", "")
                        
                        if question_text.strip():  # Only add non-empty questions
                            survey_questions.append({
                                "question": question_text.strip(),
                                "type": "text",
                                "required": True
                            })
                
                # Add survey questions
                opportunity_data["survey_questions"] = survey_questions
                
                # Log for debugging
                logger.info(f"Parsed opportunity data: title='{opportunity_data.get('title')}', questions={len(survey_questions)}")
                
                # Create the opportunity
                opportunity_id = await firestore_service.create_opportunity(opportunity_data)
                
                if opportunity_id:
                    logger.info(f"Opportunity created successfully: {opportunity_id}")
                    # Return success message with link to view the created opportunity
                    final_response = f"""🎉 **Opportunity Created Successfully!**

Your job opportunity "{opportunity_data.get('title', 'New Position')}" has been published and is now live!

**Next Steps:**
- [View the opportunity](/opportunities/{opportunity_id}) to see how it looks to applicants
- [Return to company page](/company/{company_id}) to see it in your opportunities list
- Share the opportunity link with your network

The opportunity includes {len(survey_questions)} screening questions to help you find the best candidates. Applications will be collected and you can review them through your company dashboard."""
                else:
                    final_response = "❌ Sorry, there was an error creating the opportunity. Please try again or contact support."
                    
            except Exception as e:
                logger.error(f"Error parsing/creating opportunity: {e}")
                logger.error(f"Full agent response was: {final_response[:500]}...")
                final_response = "❌ There was an error processing the opportunity data. Let's try again - please provide the job details once more."
        
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
            "adk_dev_ui_url": "http://localhost:8000/adk/dev-ui/",
            "agent_endpoint": f"/adk/apps/{root_agent.name}/users/test/sessions/test",
            "status": "ADK mounted successfully under /adk"
        }
    except Exception as e:
        return {"error": str(e), "note": "Make sure job_matching_agent directory exists with proper structure"}

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
            docs_response = await client.get("http://localhost:8000/adk/docs")
            openapi_response = await client.get("http://localhost:8000/adk/openapi.json")
            
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
            list_apps_url = "http://localhost:8000/adk/list-apps"
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
                <option value="company_1">Company_1</option>
                <option value="company_2">Company_2</option>
                <option value="company_3">Company_3</option>
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
            session_url = f"http://localhost:8000/adk/apps/{agent_name}/users/{user_id}/sessions/{session_id}"
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
            run_url = "http://localhost:8000/adk/run"
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
        
        # Get agent name from the mounted ADK app
        from job_matching_agent.agent import root_agent
        agent_name = root_agent.name
        
        # Prepare session and user IDs
        session_id = f"assessment_session_{user['uid']}_{opportunity_id}"
        user_id = user["uid"]
        
        # Add context for assessment task
        company_info = await firestore_service.get_company_info(user_profile.get('company_id'))
        company_name = company_info.get('name', 'Unknown Company') if company_info else 'Unknown Company'
        
        # Create rich context message with opportunity and applications data
        # Format data properly for the assessment agent tool
        opportunity_data = {
            "title": opportunity.get('title', ''),
            "description": opportunity.get('description', ''),
            "requirements": opportunity.get('requirements', ''),
            "survey_questions": opportunity.get('survey_questions', []),
            "company_name": company_name,
            "company_id": user_profile.get('company_id'),
            "opportunity_id": opportunity_id
        }
        
        # Format applications data
        applications_data = []
        for app in applications:
            applications_data.append({
                "applicant_name": app.get('applicant_name', 'Unknown'),
                "applicant_email": app.get('applicant_email', 'Unknown'),
                "applied_at": str(app.get('applied_at', 'Unknown')),
                "survey_responses": app.get('survey_responses', {})
            })
        
        # Create structured request for assessment agent
        assessment_request = f"""Assess candidates for this position:

**Job Opportunity:** {opportunity_data['title']}
**Company:** {opportunity_data['company_name']}
**Description:** {opportunity_data['description']}
**Requirements:** {opportunity_data.get('requirements', 'No specific requirements listed')}

**Survey Questions:**
{chr(10).join([f"{i+1}. {q.get('question', '')}" for i, q in enumerate(opportunity_data['survey_questions'])])}

**Candidates to Evaluate:** {len(applications_data)} applicant(s)
{chr(10).join([f"- {app['applicant_name']} ({app['applicant_email']})" for app in applications_data])}

**User Request:** {message}

Please provide a comprehensive assessment including candidate ranking, strengths/weaknesses, and interview recommendations."""

        contextual_message = f"[User type: company, Task: assess_candidates, Opportunity ID: {opportunity_id}] {assessment_request}"
        
        # Send message to agent via ADK
        async with httpx.AsyncClient(timeout=30.0) as client:  # Increased timeout to 30 seconds
            # Create session first
            session_url = f"http://localhost:8000/adk/apps/{agent_name}/users/{user_id}/sessions/{session_id}"
            try:
                session_response = await client.post(session_url, json={"state": {}})
                logger.debug(f"Assessment session creation response: {session_response.status_code}")
            except Exception as e:
                logger.debug(f"Assessment session creation note: {e}")
            
            # Send message to agent
            run_url = "http://localhost:8000/adk/run"
            run_payload = {
                "appName": agent_name,
                "userId": user_id,
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": contextual_message}]
                },
                "streaming": False
            }
            
            logger.debug(f"Sending assessment payload: {run_payload}")
            run_response = await client.post(run_url, json=run_payload)
            
            if run_response.status_code != 200:
                error_details = run_response.text
                logger.error(f"ADK assessment error {run_response.status_code}: {error_details}")
                raise httpx.HTTPStatusError(f"ADK endpoint error: {error_details}", request=run_response.request, response=run_response)
            
            # Parse the response
            events = run_response.json()
            final_response = f"I'm ready to help you assess the {len(applications_data)} candidate{'s' if len(applications_data) != 1 else ''} for this position. What would you like to know?"
            
            if isinstance(events, list):
                for event in events:
                    if event.get("turnComplete") and event.get("content"):
                        content = event["content"]
                        if content.get("parts"):
                            for part in content["parts"]:
                                if part.get("text"):
                                    final_response = part["text"]
                                    break
                            if final_response != f"I'm ready to help you assess the {len(applications_data)} candidate{'s' if len(applications_data) != 1 else ''} for this position. What would you like to know?":
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