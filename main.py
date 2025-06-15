import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Form, HTTPException, Cookie, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import firebase_admin
from firebase_admin import credentials, auth
from utils.firestore import FirestoreService

# Load environment variables
load_dotenv()

# Environment Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "config/firebase-credentials.json")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if ENVIRONMENT == "development" else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Debug logging for environment variables
logger.debug("=== Environment Variables ===")
logger.debug(f"ENVIRONMENT: {ENVIRONMENT}")
logger.debug(f"FIREBASE_CREDENTIALS_PATH: {FIREBASE_CREDENTIALS_PATH}")
logger.debug(f"GOOGLE_CLOUD_PROJECT: {GOOGLE_CLOUD_PROJECT}")
logger.debug("===========================")

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
        with open(FIREBASE_CREDENTIALS_PATH, 'r') as f:
            cred_data = json.load(f)
            logger.debug("Admin SDK credentials loaded successfully")
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

# Initialize FastAPI
app = FastAPI(title="Job Matching App")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Simple welcome page"""
    return templates.TemplateResponse("landing.html", {
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
        
        response = Response(content='{"success": true}', media_type="application/json")
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
        
        response = Response(content='{"success": true}', media_type="application/json")
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

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user_type: str = "talent"):
    """Registration page"""
    if user_type not in ["company", "talent"]:
        user_type = "talent"
    return templates.TemplateResponse("register.html", {
        "request": request,
        "user_type": user_type,
        "firebase_config": web_config
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user = Depends(require_auth)):
    """Dashboard page"""
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)