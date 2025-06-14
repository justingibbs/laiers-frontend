# Job Matching App - Development Context

## Project Overview

You are helping build a job matching prototype where Companies and Talent interact with AI agents through a chat interface. This is a minimum viable product (MVP) focused on validating core user interactions before adding complexity.

### Core User Flow
1. Users create an account as either "Company" or "Talent"
2. After login, users land on a dashboard with a chat interface
3. Users interact with AI agents through natural language conversation
4. All app functionality is accessed through agent conversations (job search, posting, matching, etc.)

## Technical Architecture

### Tech Stack (DO NOT MODIFY - These are fixed requirements)
- **UV** - Python dependency management
- **FastAPI** - Backend API framework  
- **FastHTML** - Python-based frontend for chat interface
- **Google ADK** - Agent orchestration and LLM integration
- **Vertex AI** - LLM backend (Gemini models)
- **Firebase Authentication** - User authentication
- **Firestore** - User data and chat history storage
- **Cloud Run** - Serverless container deployment
- **Google Cloud Storage** - File storage via ADK Artifacts

### Application Structure

#### Single FastAPI Service
```python
# main.py - single file for prototype
from fastapi import FastAPI
from google_adk import get_fast_api_app

app = get_fast_api_app()

@app.get("/")                    # Landing page
@app.get("/login")               # Auth page  
@app.get("/dashboard")           # Main chat interface (auth required)
@app.post("/api/chat")           # Agent communication (auth required)
@app.get("/health")              # Health check for Cloud Run
```

#### Route Structure
- `/` - Landing page with signup/login options
- `/login` - Firebase Authentication with user type selection
- `/dashboard` - Main chat interface (requires authentication)
- `/api/chat` - Backend endpoint for agent communication (requires authentication)
- `/health` - Cloud Run health check

### Data Models

#### User Data Structure (Python/Pydantic)
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class UserProfile(BaseModel):
    name: str
    # Additional profile fields as needed

class User(BaseModel):
    uid: str  # Firebase user ID
    email: str
    user_type: Literal["company", "talent"]
    created_at: datetime
    profile: UserProfile

# Firestore collections:
# - users: User profiles and type information
# - conversations: Chat history between users and agents  
# - sessions: Simple session management for ongoing chats
```

### Authentication & Authorization

#### Firebase Authentication
- **Providers**: Google OAuth and email/password
- **User Types**: Stored in Firestore after signup with custom claims
- **Protected Routes**: `/dashboard` and `/api/*` require valid Firebase ID token
- **Implementation**: FastAPI dependency injection for token verification

```python
# Example auth dependency
from fastapi import Depends, HTTPException
from firebase_admin import auth

async def get_current_user(token: str = Depends(get_token)):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Agent Configuration

#### Google ADK Setup
```python
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.artifacts import GcsArtifactService
from google.adk.sessions import InMemorySessionService

# Single job matching agent that adapts based on user context
job_matching_agent = Agent(
    name="job_matching_agent",
    model="gemini-2.0-flash",
    instruction="You are a job matching assistant. Help job seekers find opportunities and help recruiters find candidates.",
    description="Adapts behavior based on user type (job_seeker vs recruiter)"
)

# Configure with artifact support for file uploads
artifact_service = GcsArtifactService(bucket_name="job-matching-files")
session_service = InMemorySessionService()

runner = Runner(
    agent=job_matching_agent,
    app_name="job_matching_app", 
    session_service=session_service,
    artifact_service=artifact_service
)
```

#### Agent Capabilities by User Type
- **Talent**: Resume analysis, job search guidance, interview prep, skills assessment
- **Companies**: Candidate sourcing advice, job posting optimization, screening assistance

### File Upload Support (ADK Artifacts)

#### Configuration
```python
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService

# Development
artifact_service = InMemoryArtifactService()

# Production  
artifact_service = GcsArtifactService(bucket_name="your-job-files-bucket")
```

#### File Handling in Agent Tools
```python
from google.adk.tools.tool_context import ToolContext
import google.genai.types as types

def analyze_uploaded_resume(tool_context: ToolContext, filename: str):
    """Analyze user's uploaded resume"""
    # Load user-scoped artifact (persists across sessions)
    resume_artifact = tool_context.load_artifact(f"user:{filename}")
    
    if resume_artifact and resume_artifact.inline_data:
        resume_bytes = resume_artifact.inline_data.data
        mime_type = resume_artifact.inline_data.mime_type
        
        # Process resume content
        # Return analysis to agent for conversation
        return f"Resume analysis for {filename}..."
    
    return "Resume not found. Please upload your resume first."
```

### Storage Strategy

#### All Firestore for Simplicity
- **User data**: Firestore users collection
- **Chat history**: Firestore conversations collection  
- **Session management**: Firestore sessions collection
- **File storage**: Google Cloud Storage via ADK Artifacts
- **No SQLite**: Use Firestore for both dev and production to avoid environment differences

### Environment Configuration

```bash
# Required for all environments
GOOGLE_CLOUD_PROJECT=your-project-id
FIREBASE_PROJECT_ID=your-firebase-project  
VERTEX_AI_LOCATION=us-central1

# Environment-specific
ENVIRONMENT=development  # or production
```

### Deployment (Cloud Run)

#### Key Requirements
- Single service deployment
- Environment secrets for Firebase service account
- Automatic scaling with reasonable limits
- HTTPS enforcement (automatic with Cloud Run)

## Development Guidelines

### FastHTML Frontend Patterns
- Single page chat interface with real-time updates
- Mobile-responsive design for both user types
- Display user context (type, profile) in UI
- Handle file uploads through chat interface

### Security (Minimal for MVP)
- Firebase ID token verification on protected routes
- Basic CORS configuration for browser requests
- Standard GCP encryption (automatic)
- Basic Firestore security rules based on user authentication

### Error Handling Patterns
```python
# Always check for artifact service configuration
try:
    version = context.save_artifact(filename, artifact)
except ValueError as e:
    # ArtifactService not configured
    return "File upload not available"
except Exception as e:
    # Handle storage errors
    return "File upload failed, please try again"
```

## Development Workflow

### Local Development
```bash
# Setup
uv sync
export ENVIRONMENT=development
export GOOGLE_CLOUD_PROJECT=your-dev-project

# Run locally
uvicorn main:app --reload --port 8000
```

### Testing Access Points
- **Chat Interface**: http://localhost:8000/dashboard
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Implementation Priority

### Phase 1: Core MVP
1. Setup GCP project with Firebase, Firestore, Vertex AI
2. Create basic FastAPI app with routes
3. Implement Firebase authentication with user types
4. Build FastHTML chat interface
5. Configure ADK agent with basic job matching capabilities
6. Deploy to Cloud Run

### Phase 2: File Support  
1. Configure ADK Artifacts with GCS
2. Add file upload to chat interface
3. Implement resume/job description processing
4. Test end-to-end file handling

### Phase 3: Enhancements
1. Advanced document analysis (skill extraction, matching)
2. Vector storage for semantic search
3. Enhanced UI/UX
4. Performance monitoring

## Key Constraints & Decisions

### What's Intentionally Simple
- **Single file architecture** (main.py) for prototype
- **No complex authorization** beyond user type
- **No advanced monitoring** initially
- **No microservices** - single FastAPI service
- **No complex session management** - basic Firestore storage

### What Can Be Enhanced Later
- Vector storage for intelligent matching
- Advanced file processing pipelines  
- Team/company features for recruiters
- Complex workflow orchestration
- Performance monitoring and analytics

## Common Pitfalls to Avoid

1. **Don't over-engineer** - stick to the simple architecture for MVP
2. **Firebase vs Firestore confusion** - use Firebase Auth + Firestore database
3. **ADK complexity** - start with single agent, add multi-agent later
4. **File handling** - use ADK Artifacts, not custom upload logic
5. **Environment differences** - use Firestore everywhere, no SQLite

## Success Metrics for MVP

- Users can register as job seeker or recruiter
- Chat interface works end-to-end with agent
- Basic job matching conversations function
- File upload and processing works
- Deployment to Cloud Run succeeds
- Authentication flow is smooth

---

*This document should be updated as the prototype evolves and new requirements emerge.*