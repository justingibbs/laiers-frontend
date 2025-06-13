---> This is captured in `gemini.md`

# Technical Requirements Document - Job Matching Prototype

## Project Overview

Building a simple job matching prototype where Job Seekers and Recruiters interact with AI agents through a chat interface. The application uses a single FastAPI service with FastHTML frontend, Firebase Authentication, and Google ADK for agent orchestration.

## Tech Stack

### Core Technologies
- **UV** - Python dependency management
- **FastAPI** - Backend API framework
- **FastHTML** - Python-based frontend for chat interface
- **Google ADK** ([https://google.github.io/adk-docs/](https://google.github.io/adk-docs/)) - Agent orchestration
- **Vertex AI** - LLM backend for agents

### Cloud Infrastructure
- **Google Cloud Platform** - Primary cloud provider
- **Cloud Run** - Serverless container deployment
- **Firebase Authentication** - User authentication
- **Firestore** - User data and chat history storage

## Architecture Requirements

### Single Service Architecture

The application uses one FastAPI service with simple route separation:

#### Route Structure
```
/                     # Landing page
/login               # Login/signup page
/dashboard           # Main chat interface (auth required)
/api/chat            # Chat endpoint for agents (auth required)
/health              # Health check
```

### User Flow
1. **Landing Page** (`/`) - Simple welcome page with login/signup options
2. **Authentication** (`/login`) - Firebase Auth with user type selection (Job Seeker/Recruiter)
3. **Dashboard** (`/dashboard`) - Main chat interface with agent interaction
4. **API Layer** (`/api/chat`) - Backend endpoint for agent communication

### Authentication & User Management

#### Firebase Authentication
- **Providers**: Google OAuth and email/password
- **User Types**: Store user type (Job Seeker/Recruiter) in Firestore after signup
- **Protection**: Only `/dashboard` and `/api/*` routes require authentication
- **Implementation**: FastAPI dependency for token verification

#### User Data Structure
```python
# Python dataclass/Pydantic model for user data
from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class UserProfile(BaseModel):
    name: str
    # Additional profile fields as needed

class User(BaseModel):
    uid: str
    email: str
    user_type: Literal["job_seeker", "recruiter"]
    created_at: datetime
    profile: UserProfile

# Firestore document structure will mirror this model
```

### Data Storage

#### Firestore Collections
- **users** - User profiles and type information
- **conversations** - Chat history between users and agents
- **sessions** - Simple session management for ongoing chats

#### Session Management
- **All Environments**: Firestore for consistency and simplicity
- **Benefits**: Same storage layer locally and in production, no migration needed

### Agent Configuration

#### Google ADK Setup
- **Single Agent Type**: Job matching agent that adapts behavior based on user type
- **Context Awareness**: Agent receives user type and profile in conversation context
- **Vertex AI Integration**: Use Gemini or other Vertex AI models as the LLM backend

#### Agent Capabilities
- **Job Seekers**: Resume assistance, job search guidance, interview prep
- **Recruiters**: Candidate sourcing advice, job posting optimization, screening assistance

### Application Structure

#### Simple FastAPI App
```python
# main.py - single file for prototype
from fastapi import FastAPI
from google_adk import get_fast_api_app

# Create ADK-enabled FastAPI app
app = get_fast_api_app()

@app.get("/")                    # Landing page
@app.get("/login")               # Auth page  
@app.get("/dashboard")           # Main chat interface
@app.post("/api/chat")           # Agent communication
@app.get("/health")              # Health check
```

#### FastHTML Interface
- **Single Page Chat**: Simple chat interface with message history
- **User Context**: Display user type and basic profile info
- **Mobile Responsive**: Basic responsive design for mobile use

### Deployment Configuration

#### Environment Variables
```bash
# Required for all environments
GOOGLE_CLOUD_PROJECT=your-project-id
FIREBASE_PROJECT_ID=your-firebase-project
VERTEX_AI_LOCATION=us-central1

# Development
ENVIRONMENT=development

# Production
ENVIRONMENT=production
```

#### Cloud Run Configuration
- **Single service** deployment
- **Automatic scaling** with reasonable limits
- **Environment secrets** for Firebase service account

### Security (Minimal for Prototype)

#### Authentication Only
- Firebase ID token verification on protected routes
- Basic CORS configuration for browser requests
- HTTPS enforcement (automatic with Cloud Run)

#### Data Security
- Basic Firestore security rules based on user authentication
- No complex authorization rules initially
- Standard GCP encryption at rest/transit

### Development Workflow

#### Local Development
```bash
# Setup
uv sync
export ENVIRONMENT=development

# Run
uvicorn main:app --reload --port 8000
```

#### Testing Access
- **Local Chat Interface**: `http://localhost:8000/dashboard`
- **API Docs**: `http://localhost:8000/docs`

#### Agent File Handling

ADK provides built-in **Artifacts** for file management:
- **File Uploads**: Users can upload files (resumes, job descriptions) directly in chat
- **Storage Options**: 
  - Development: `InMemoryArtifactService` for local testing
  - Production: `GcsArtifactService` for persistent Google Cloud Storage
- **File Types**: Supports any binary data (PDFs, images, documents, etc.)
- **Scoping**: Files can be session-specific or user-persistent across sessions

#### File Upload Integration
```python
# Configure ADK Runner with artifact service
from google.adk.artifacts import GcsArtifactService

artifact_service = GcsArtifactService(bucket_name="job-matching-files")
runner = Runner(
    agent=job_matching_agent,
    artifact_service=artifact_service,
    session_service=session_service
)

# In your agent tools - handle uploaded resume
def analyze_resume(tool_context: ToolContext, filename: str):
    """Analyze uploaded resume file"""
    resume_artifact = tool_context.load_artifact(f"user:{filename}")
    if resume_artifact:
        # Process resume bytes - extract text, analyze skills, etc.
        resume_bytes = resume_artifact.inline_data.data
        # Agent can now analyze resume content and provide feedback
```

### What's Simplified from Original Spec

#### Removed Complexity
- **No ADK Web UI** - Focus on user-facing interface only  
- **No IP whitelisting** - Environment gating only
- **No complex session management** - Basic Firestore storage
- **No vector storage** - Start without advanced search
- **No monitoring/observability** - Use basic Cloud Run metrics
- **No development/production route separation** - Simple environment config

#### Future Considerations
- Vector storage for semantic resume/job matching (once you have file uploads working)
- Advanced monitoring as usage grows
- Complex authorization when adding team features
- File processing pipelines for resume parsing and job description analysis

### Next Steps for Implementation

1. **Setup GCP Project** with Firebase, Firestore, and Vertex AI
2. **Create Firebase Auth** configuration with custom claims for user types
3. **Build FastAPI app** with basic routes and ADK integration
4. **Implement FastHTML chat interface** with Firebase Auth
5. **Configure and deploy** to Cloud Run
6. **Test end-to-end** user registration and chat flow

This simplified approach gets you to MVP quickly while maintaining the flexibility to add complexity as your prototype evolves.