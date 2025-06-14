# /Users/justingibbs/Projects/laiers/main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app

app = FastAPI()

# Load environment variables
load_dotenv()

# Initialize Firebase using the JSON file
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
initialize_app(cred)

# Define the landing page route
@app.get("/", response_class=HTMLResponse)
async def landing_page():
    # Simple HTML content for the landing page
    # This aligns with the goal of testing a simple page load.
    # FastHTML components would be integrated here later.
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Matching App - Landing</title>
</head>
<body>
    <h1>Welcome to the Job Matching App!</h1>
    <p>This is the MVP landing page.</p>
    <p>Please <a href="/login">Login</a> or Sign Up.</p>
    <p><em>(Backend: FastAPI, Frontend to be: FastHTML, Agent: Google ADK)</em></p>
</body>
</html>"""

# Define the health check route as specified in gemini.md
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Healthy"}

# Placeholder comments for other routes as per gemini.md, to be implemented later:
# @app.get("/login")               # Auth page
# @app.get("/dashboard")           # Main chat interface (auth required)
# @app.post("/api/chat")           # Agent communication (auth required)

# To run this application (as per gemini.md):
# uvicorn main:app --reload --port 8000
