import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException, Request, Form, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response, HTMLResponse
from fasthtml.common import *
import firebase_admin
from firebase_admin import credentials, auth
from google.cloud import firestore
from pydantic import BaseModel, EmailStr

# Load environment variables
load_dotenv()

# Environment Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
ADK_BUCKET_NAME = os.getenv("ADK_BUCKET_NAME")

# Validation for required variables
required_vars = {
    "GOOGLE_CLOUD_PROJECT": GOOGLE_CLOUD_PROJECT,
    "ADK_BUCKET_NAME": ADK_BUCKET_NAME
}

for var_name, var_value in required_vars.items():
    if not var_value:
        raise ValueError(f"Required environment variable {var_name} is not set")

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred, {'projectId': GOOGLE_CLOUD_PROJECT})

# Initialize Firestore
db = firestore.Client(project=GOOGLE_CLOUD_PROJECT)

# Initialize FastAPI
app = FastAPI(title="Job Matching App")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic Models
class UserProfile(BaseModel):
    name: str | None = None
    company: str | None = None
    skills: list[str] = []
    experience_level: str | None = None

class User(BaseModel):
    uid: str
    email: EmailStr
    user_type: str  # "company" or "talent"
    created_at: datetime
    profile: UserProfile
    is_active: bool = True

# Auth Helper Functions
async def get_current_user(session_token: str = Cookie(None)) -> dict | None:
    """Get current user from session token"""
    if not session_token:
        return None
    
    try:
        decoded_token = auth.verify_session_cookie(session_token, check_revoked=True)
        return decoded_token
    except Exception:
        return None

async def require_auth(session_token: str = Cookie(None)) -> dict:
    """Require authentication, redirect to login if not authenticated"""
    user = await get_current_user(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

# Firestore Helper Functions
async def create_user_profile(user_data: User) -> bool:
    """Create user profile in Firestore"""
    try:
        doc_ref = db.collection("users").document(user_data.uid)
        doc_ref.set(user_data.model_dump())
        return True
    except Exception as e:
        print(f"Error creating user profile: {e}")
        return False

async def get_user_profile(uid: str) -> User | None:
    """Get user profile from Firestore"""
    try:
        doc = db.collection("users").document(uid).get()
        if doc.exists:
            return User(**doc.to_dict())
        return None
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return None

# FastHTML Components
def create_base_page(title: str, content: any):
    """Base page template with common head elements"""
    return str(Html(
        Head(
            Title(title),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Link(rel="stylesheet", href="/static/css/styles.css"),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
            # Firebase Auth SDK
            Script(src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"),
            Script(src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth-compat.js"),
            Script(f"""
                // Firebase config - replace with your actual config
                const firebaseConfig = {{
                    projectId: "{GOOGLE_CLOUD_PROJECT}",
                    // Add other Firebase config values as needed
                }};
                firebase.initializeApp(firebaseConfig);
            """)
        ),
        Body(content)
    ))

def create_landing_page():
    """Landing page with role selection"""
    return create_base_page(
        "Job Matching App",
        Div(
            Header(
                H1("Find Your Perfect Match", cls="hero-title"),
                P("Connect job seekers with recruiters through AI-powered conversations", cls="hero-subtitle")
            ),
            Main(
                Div(
                    H2("Choose Your Path"),
                    Div(
                        Div(
                            H3("I'm Looking for Talent"),
                            P("Post jobs, find candidates, streamline hiring"),
                            A("Sign Up as Company", href="/register?type=company", cls="btn btn-primary")
                        ),
                        Div(
                            H3("I'm Looking for Work"),
                            P("Find opportunities, get matched, advance your career"),
                            A("Sign Up as Job Seeker", href="/register?type=talent", cls="btn btn-secondary")
                        ),
                        cls="role-cards"
                    ),
                    P(
                        "Already have an account? ",
                        A("Sign In", href="/login")
                    ),
                    cls="landing-content"
                )
            ),
            cls="landing-page"
        )
    )

def create_register_page(user_type: str):
    """Registration page for specific user type"""
    type_label = "Company" if user_type == "company" else "Job Seeker"
    
    return create_base_page(
        f"Register as {type_label}",
        Div(
            Header(
                H1(f"Register as {type_label}"),
                A("← Back to Home", href="/", cls="back-link")
            ),
            Main(
                Form(
                    Div(
                        Label("Email Address", for_="email"),
                        Input(type="email", id="email", name="email", required=True)
                    ),
                    Div(
                        Label("Password", for_="password"),
                        Input(type="password", id="password", name="password", required=True, minlength="6")
                    ),
                    Div(
                        Label("Confirm Password", for_="confirm_password"),
                        Input(type="password", id="confirm_password", name="confirm_password", required=True)
                    ),
                    Input(type="hidden", name="user_type", value=user_type),
                    Button(f"Create {type_label} Account", type="submit", cls="btn btn-primary"),
                    Div(id="error-message", cls="error-message"),
                    id="register-form",
                    cls="auth-form"
                ),
                P(
                    "Already have an account? ",
                    A("Sign In", href="/login")
                ),
                cls="auth-container"
            ),
            Script("""
                document.getElementById('register-form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const formData = new FormData(e.target);
                    const email = formData.get('email');
                    const password = formData.get('password');
                    const confirmPassword = formData.get('confirm_password');
                    const userType = formData.get('user_type');
                    
                    if (password !== confirmPassword) {
                        document.getElementById('error-message').textContent = 'Passwords do not match';
                        return;
                    }
                    
                    try {
                        const userCredential = await firebase.auth().createUserWithEmailAndPassword(email, password);
                        const idToken = await userCredential.user.getIdToken();
                        
                        // Send registration data to server
                        const response = await fetch('/api/register', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                idToken: idToken, 
                                userType: userType,
                                email: email 
                            })
                        });
                        
                        if (response.ok) {
                            window.location.href = '/dashboard';
                        } else {
                            const error = await response.json();
                            document.getElementById('error-message').textContent = error.detail || 'Registration failed';
                        }
                    } catch (error) {
                        document.getElementById('error-message').textContent = error.message;
                    }
                });
            """),
            cls="register-page"
        )
    )

def create_login_page():
    """Login page"""
    return create_base_page(
        "Sign In",
        Div(
            Header(
                H1("Sign In"),
                A("← Back to Home", href="/", cls="back-link")
            ),
            Main(
                Form(
                    Div(
                        Label("Email Address", for_="email"),
                        Input(type="email", id="email", name="email", required=True)
                    ),
                    Div(
                        Label("Password", for_="password"),
                        Input(type="password", id="password", name="password", required=True)
                    ),
                    Button("Sign In", type="submit", cls="btn btn-primary"),
                    Div(id="error-message", cls="error-message"),
                    id="login-form",
                    cls="auth-form"
                ),
                P(
                    "Don't have an account? ",
                    A("Get Started", href="/")
                ),
                cls="auth-container"
            ),
            Script("""
                document.getElementById('login-form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const formData = new FormData(e.target);
                    const email = formData.get('email');
                    const password = formData.get('password');
                    
                    try {
                        const userCredential = await firebase.auth().signInWithEmailAndPassword(email, password);
                        const idToken = await userCredential.user.getIdToken();
                        
                        const response = await fetch('/api/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ idToken: idToken })
                        });
                        
                        if (response.ok) {
                            window.location.href = '/dashboard';
                        } else {
                            const error = await response.json();
                            document.getElementById('error-message').textContent = error.detail || 'Login failed';
                        }
                    } catch (error) {
                        document.getElementById('error-message').textContent = error.message;
                    }
                });
            """),
            cls="login-page"
        )
    )

def create_dashboard_page(user_data: dict, user_profile: User):
    """Dashboard page for authenticated users"""
    user_type_label = "Company User" if user_profile.user_type == "company" else "Talent User"
    
    return create_base_page(
        f"{user_type_label} Dashboard",
        Div(
            Header(
                H1(f"Welcome, {user_type_label}"),
                Div(
                    P(f"Logged in as: {user_data['email']}"),
                    Button("Sign Out", onclick="signOut()", cls="btn btn-outline"),
                    cls="header-actions"
                ),
                cls="dashboard-header"
            ),
            Main(
                Div(
                    H2("AI Assistant Chat"),
                    P(f"Chat with our AI assistant specialized for {user_profile.user_type} users"),
                    Div(id="chat-messages", cls="chat-container"),
                    Form(
                        Input(
                            type="text",
                            name="message",
                            placeholder=f"Ask me anything about {'hiring and recruitment' if user_profile.user_type == 'company' else 'job searching and career development'}...",
                            required=True,
                            autocomplete="off"
                        ),
                        Button("Send", type="submit"),
                        hx_post="/api/chat",
                        hx_target="#chat-messages",
                        hx_swap="beforeend",
                        hx_trigger="submit",
                        cls="chat-form"
                    ),
                    cls="chat-section"
                ),
                cls="dashboard-content"
            ),
            Script("""
                function signOut() {
                    firebase.auth().signOut().then(() => {
                        document.cookie = 'session_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
                        window.location.href = '/';
                    });
                }
            """),
            cls="dashboard-page"
        )
    )

def create_chat_message(message: str, response: str):
    """Create chat message component"""
    return Div(
        Div(message, cls="user-message"),
        Div(response, cls="assistant-message"),
        cls="message-pair"
    )

# Routes
@app.get("/", response_class=HTMLResponse)
def landing_page():
    """Landing page with role selection"""
    page = create_landing_page()
    return HTMLResponse(content=page)

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    """Registration page"""
    user_type = request.query_params.get("type", "talent")
    if user_type not in ["company", "talent"]:
        user_type = "talent"
    page = create_register_page(user_type)
    return HTMLResponse(content=page)

@app.get("/login", response_class=HTMLResponse)
def login_page():
    """Login page"""
    page = create_login_page()
    return HTMLResponse(content=page)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(user = Depends(require_auth)):
    """Dashboard page for authenticated users"""
    # Get user profile from Firestore
    user_profile = await get_user_profile(user['uid'])
    
    if not user_profile:
        # If no profile exists, redirect to registration
        return RedirectResponse(url="/register", status_code=302)
    
    page = create_dashboard_page(user, user_profile)
    return HTMLResponse(content=page)

@app.post("/api/register")
async def register_user(request: Request):
    """Handle user registration"""
    try:
        data = await request.json()
        id_token = data.get('idToken')
        user_type = data.get('userType')
        email = data.get('email')
        
        if not id_token or user_type not in ['company', 'talent']:
            raise HTTPException(status_code=400, detail="Invalid registration data")
        
        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Create user profile
        user_profile = User(
            uid=uid,
            email=email,
            user_type=user_type,
            created_at=datetime.utcnow(),
            profile=UserProfile()
        )
        
        # Save to Firestore
        success = await create_user_profile(user_profile)
        if not success:
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
        
        return response
        
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/login")
async def login_user(request: Request):
    """Handle user login"""
    try:
        data = await request.json()
        id_token = data.get('idToken')
        
        if not id_token:
            raise HTTPException(status_code=400, detail="No ID token provided")
        
        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)
        
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
        print(f"Login error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(request: Request, user = Depends(require_auth)):
    """Handle chat messages - placeholder for now"""
    try:
        form_data = await request.form()
        message = form_data.get("message", "")
        
        # Get user profile to customize response
        user_profile = await get_user_profile(user['uid'])
        user_type = user_profile.user_type if user_profile else "user"
        
        # Placeholder response - will integrate with ADK later
        if user_type == "company":
            response = f"As a company user, I can help you with hiring, candidate screening, and recruitment strategies. You asked: '{message}'"
        else:
            response = f"As a talent user, I can help you with job searching, resume optimization, and career development. You asked: '{message}'"
        
        chat_component = create_chat_message(message, response)
        return HTMLResponse(content=chat_component)
        
    except Exception as e:
        print(f"Chat error: {e}")
        error_component = create_chat_message("Error", "Sorry, something went wrong. Please try again.")
        return HTMLResponse(content=error_component)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "environment": ENVIRONMENT}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)