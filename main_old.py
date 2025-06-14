# /Users/justingibbs/Projects/laiers/main.py
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fasthtml import FastHTML, html, head, body, div, h1, h2, p, a, form, input, button
import os
from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app, auth, firestore
from firebase_admin.exceptions import FirebaseError

# Load environment variables
load_dotenv()

# Initialize Firebase
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
initialize_app(cred)

# User Models
class UserProfile(BaseModel):
    name: str
    company_name: str | None = None  # For Company users
    title: str | None = None         # For Talent users
    skills: list[str] | None = None  # For Talent users
    industry: str | None = None      # For Company users

class User(BaseModel):
    uid: str
    email: str
    user_type: Literal["company", "talent"]
    created_at: datetime
    profile: UserProfile

# Firebase Auth Dependency
async def get_current_user(token: str = Depends(get_token)):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

def landing_page_html():
    return html(
        head(
            title("Laiers - AI-Powered Job Matching"),
            link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css")
        ),
        body(
            div(class_="min-h-screen flex flex-col")(
                # Header
                div(class_="bg-white shadow-sm")(
                    div(class_="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4")(
                        div(class_="flex justify-between items-center")(
                            h1(class_="text-2xl font-bold text-gray-900")("Laiers"),
                            div(class_="space-x-4")(
                                a(href="/login", class_="text-gray-600 hover:text-gray-900")("Login"),
                                a(href="/register", class_="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700")("Sign Up")
                            )
                        )
                    )
                ),
                # Hero Section
                div(class_="flex-grow")(
                    div(class_="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12")(
                        div(class_="text-center")(
                            h2(class_="text-4xl font-extrabold text-gray-900 sm:text-5xl")(
                                "Find Your Perfect Match"
                            ),
                            p(class_="mt-4 text-xl text-gray-600")(
                                "AI-powered job matching that focuses on what matters most - your unique human capabilities."
                            )
                        ),
                        # User Type Selection
                        div(class_="mt-12 grid grid-cols-1 gap-8 sm:grid-cols-2")(
                            # Company Card
                            div(class_="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow")(
                                h3(class_="text-2xl font-bold text-gray-900 mb-4")("For Companies"),
                                p(class_="text-gray-600 mb-6")(
                                    "Find talent with the essential soft skills needed to excel in your AI-transformed workplace."
                                ),
                                a(href="/register?type=company", class_="block w-full bg-blue-600 text-white text-center px-4 py-2 rounded-md hover:bg-blue-700")(
                                    "Register as Company"
                                )
                            ),
                            # Talent Card
                            div(class_="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow")(
                                h3(class_="text-2xl font-bold text-gray-900 mb-4")("For Talent"),
                                p(class_="text-gray-600 mb-6")(
                                    "Showcase your unique human capabilities and find opportunities that value your potential."
                                ),
                                a(href="/register?type=talent", class_="block w-full bg-blue-600 text-white text-center px-4 py-2 rounded-md hover:bg-blue-700")(
                                    "Register as Talent"
                                )
                            )
                        )
                    )
                ),
                # Footer
                div(class_="bg-white border-t")(
                    div(class_="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6")(
                        p(class_="text-center text-gray-500")(
                            "© 2024 Laiers. All rights reserved."
                        )
                    )
                )
            )
        )
    )

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    return str(landing_page_html())

@app.get("/register", response_class=HTMLResponse)
async def register_page(type: str | None = None):
    if type not in ["company", "talent"]:
        return RedirectResponse(url="/")
    
    return str(register_page_html(type))

@app.post("/register")
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    user_type: Literal["company", "talent"] = Form(...),
    company_name: str | None = Form(None),
    title: str | None = Form(None),
    industry: str | None = Form(None)
):
    try:
        # Create Firebase user
        user = auth.create_user(
            email=email,
            password=password
        )
        
        # Create user profile in Firestore
        profile = UserProfile(
            name=name,
            company_name=company_name if user_type == "company" else None,
            title=title if user_type == "talent" else None,
            industry=industry if user_type == "company" else None
        )
        
        user_data = User(
            uid=user.uid,
            email=email,
            user_type=user_type,
            created_at=datetime.utcnow(),
            profile=profile
        )
        
        # Store in Firestore
        db = firestore.client()
        db.collection("users").document(user.uid).set(user_data.dict())
        
        return RedirectResponse(url="/dashboard", status_code=303)
    except FirebaseError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return str(login_page_html())

@app.post("/login")
async def login_user(email: str = Form(...), password: str = Form(...)):
    try:
        # Sign in with Firebase
        user = auth.get_user_by_email(email)
        # Note: Firebase handles password verification internally
        return RedirectResponse(url="/dashboard", status_code=303)
    except FirebaseError as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(user: dict = Depends(get_current_user)):
    return str(dashboard_html(user))

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Healthy"}

# Placeholder comments for other routes as per gemini.md, to be implemented later:
# @app.get("/login")               # Auth page
# @app.get("/dashboard")           # Main chat interface (auth required)
# @app.post("/api/chat")           # Agent communication (auth required)

def register_page_html(user_type: str):
    return html(
        head(
            title("Register as " + user_type.title() + " - Laiers"),
            link(href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css", rel="stylesheet")
        ),
        body(
            div(class_="min-h-screen flex flex-col")(
                # Header
                div(class_="bg-white shadow-sm")(
                    div(class_="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4")(
                        div(class_="flex justify-between items-center")(
                            a("Laiers", href="/", class_="text-2xl font-bold text-gray-900")
                        )
                    )
                ),
                # Registration Form
                div(class_="flex-grow flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8")(
                    div(class_="max-w-md w-full space-y-8")(
                        div(
                            h2("Register as " + user_type.title(), class_="mt-6 text-center text-3xl font-extrabold text-gray-900")
                        ),
                        form(action="/register", method="POST", class_="mt-8 space-y-6")(
                            input(value=user_type, type="hidden", name="user_type"),
                            div(class_="rounded-md shadow-sm -space-y-px")(
                                div(
                                    input(placeholder="Email address", id="email", name="email", type="email", required,
                                        class_="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm")
                                ),
                                div(
                                    input(placeholder="Password", id="password", name="password", type="password", required,
                                        class_="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm")
                                ),
                                div(
                                    input(placeholder="Full Name", id="name", name="name", type="text", required,
                                        class_="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm")
                                ),
                                # Conditional fields based on user type
                                div(
                                    input(placeholder="Company Name" if user_type == "company" else "Current Title",
                                        id="company_name" if user_type == "company" else "title",
                                        name="company_name" if user_type == "company" else "title",
                                        type="text", required,
                                        class_="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm")
                                ) if user_type == "company" else div(
                                    input(placeholder="Industry", id="industry", name="industry", type="text", required,
                                        class_="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm")
                                )
                            ),
                            div(
                                button("Register", type="submit",
                                    class_="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500")
                            )
                        ),
                        div(class_="text-center")(
                            p(class_="text-sm text-gray-600")(
                                "Already have an account? ",
                                a("Sign in", href="/login", class_="font-medium text-blue-600 hover:text-blue-500")
                            )
                        )
                    )
                ),
                # Footer
                div(class_="bg-white border-t")(
                    div(class_="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6")(
                        p("© 2024 Laiers. All rights reserved.", class_="text-center text-gray-500")
                    )
                )
            )
        )
    )

def login_page_html():
    return html(
        head(
            title("Login - Laiers"),
            link(href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css", rel="stylesheet")
        ),
        body(
            div(class_="min-h-screen flex flex-col")(
                # Header
                div(class_="bg-white shadow-sm")(
                    div(class_="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4")(
                        div(class_="flex justify-between items-center")(
                            a("Laiers", href="/", class_="text-2xl font-bold text-gray-900")
                        )
                    )
                ),
                # Login Form
                div(class_="flex-grow flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8")(
                    div(class_="max-w-md w-full space-y-8")(
                        div(
                            h2("Sign in to your account", class_="mt-6 text-center text-3xl font-extrabold text-gray-900")
                        ),
                        form(action="/login", method="POST", class_="mt-8 space-y-6")(
                            div(class_="rounded-md shadow-sm -space-y-px")(
                                div(
                                    input(placeholder="Email address", id="email", name="email", type="email", required,
                                        class_="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm")
                                ),
                                div(
                                    input(placeholder="Password", id="password", name="password", type="password", required,
                                        class_="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm")
                                )
                            ),
                            div(
                                button("Sign in", type="submit",
                                    class_="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500")
                            )
                        ),
                        div(class_="text-center")(
                            p(class_="text-sm text-gray-600")(
                                "Don't have an account? ",
                                a("Register now", href="/", class_="font-medium text-blue-600 hover:text-blue-500")
                            )
                        )
                    )
                ),
                # Footer
                div(class_="bg-white border-t")(
                    div(class_="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6")(
                        p("© 2024 Laiers. All rights reserved.", class_="text-center text-gray-500")
                    )
                )
            )
        )
    )

# To run this application (as per gemini.md):
# uvicorn main:app --reload --port 8000
