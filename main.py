import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Form, HTTPException, Cookie, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
import firebase_admin
from firebase_admin import credentials, auth
from utils.firestore import FirestoreService

# Load environment variables
load_dotenv()

# Environment Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "config/firebase-credentials.json")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
ADK_BUCKET_NAME = os.getenv("ADK_BUCKET_NAME")

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

# Get project ID from web config
web_config = load_firebase_web_config()
PROJECT_ID = web_config.get('projectId')

if not PROJECT_ID:
    logger.error("Firebase project ID not found in web config")
    raise ValueError("Firebase project ID not found in web config")

logger.info(f"Using Firebase project ID: {PROJECT_ID}")

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
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

# Initialize templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Get ADK app and mount it under /adk path
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
adk_app = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_db_url="sqlite:///./sessions.db",
    allow_origins=["*"] if ENVIRONMENT == "development" else [],
    web=True,  # This enables the dev UI at /adk/dev-ui
    trace_to_cloud=False
)

# Mount ADK app under /adk prefix
app.mount("/adk", adk_app)

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
    """Handle registration with Firebase"""
    try:
        data = await request.json()
        id_token = data.get('idToken')
        user_type = data.get('userType')
        email = data.get('email')
        
        logger.info(f"Registration attempt - Email: {email}, User Type: {user_type}")
        
        if not id_token or user_type not in ['company', 'talent']:
            raise HTTPException(status_code=400, detail="Invalid registration data")
        
        # Verify the ID token
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
            logger.info(f"Token verified - UID: {user_id}")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # Create user profile in Firestore
        profile_created = await firestore_service.create_user_profile(user_id, email, user_type)
        if not profile_created:
            raise HTTPException(status_code=500, detail="Failed to create user profile")
        
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
        
        logger.info(f"Registration successful for user: {email}")
        return response
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

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
            logger.info(f"Login successful - UID: {decoded_token.get('uid')}")
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
        
        # Import the agent from the job_matching_agent module
        from job_matching_agent.agent import root_agent
        
        # Create a runner for this chat session
        session_service = InMemorySessionService()
        runner = Runner(
            app_name="job-matching-chat",
            agent=root_agent,
            session_service=session_service
        )
        
        # Create user context for the agent
        user_context = {
            "user_type": user_profile.get("user_type", "talent"),
            "email": user.get("email", ""),
            "user_id": user["uid"]
        }
        
        # Run the agent with user context
        session_id = f"session_{user['uid']}"
        response = await runner.run_async(
            user_id=user["uid"],
            session_id=session_id,
            message=message,
            context=user_context
        )
        
        # Extract the response text
        response_text = response.get("response", "I'm sorry, I couldn't process that request.")
        
        # Return HTMX partial template
        return templates.TemplateResponse("components/chat_message.html", {
            "request": request,
            "user_message": message,
            "agent_response": response_text,
            "timestamp": datetime.now()
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return templates.TemplateResponse("components/chat_error.html", {
            "request": request,
            "error": "Failed to process message. Please try again."
        })

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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "firebase_project": PROJECT_ID,
        "adk_mounted": True
    }

# Debug route to test ADK integration
@app.get("/debug/adk")
async def debug_adk():
    """Debug endpoint to check ADK integration"""
    try:
        from job_matching_agent.agent import root_agent
        return {
            "agent_name": root_agent.name,
            "agent_model": root_agent.model,
            "adk_dev_ui": "/adk/dev-ui",
            "agent_endpoint": f"/adk/apps/{root_agent.name}/users/test/sessions/test"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)