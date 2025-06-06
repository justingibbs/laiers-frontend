# Gemini AI Assistant Guide

## Project Overview

### Project Purpose/Goal
An agent-powered job matching platform that revolutionizes hiring by identifying candidates with the essential soft skills needed to excel in GenAI-transformed workplaces. Rather than focusing on traditional hard skills that AI increasingly automates, the platform evaluates and matches based on uniquely human capabilities—creative problem-solving, emotional intelligence, adaptability, critical thinking, and collaborative leadership—that become more valuable as AI handles routine tasks.

### Target Users
Initially focused on technology professionals, with planned expansion to serve all industries and career levels. The platform addresses the universal need for soft-skill assessment across any role where human-AI collaboration is becoming essential.

### Key Features
- **Intelligent Survey Generation**: AI agents analyze job posting text to automatically create customized assessments that evaluate soft skills most relevant to each specific role
- **Dynamic Candidate Assessment**: Job seekers complete personalized surveys designed to reveal their adaptability, problem-solving approach, and AI-collaboration readiness for the target position
- **Smart Ranking & Analysis**: Advanced algorithms analyze responses to rank candidates based on soft-skill alignment with role requirements, providing recruiters with insights beyond traditional qualifications

### Architecture Overview
The platform operates through three specialized AI agents working in concert:

- **Recruiter Agent**: Collaborates with hiring managers via LLM chat interface to analyze job postings and generate tailored soft-skill assessments
- **Candidate Agent**: Guides job seekers through personalized survey experiences, ensuring comprehensive evaluation of relevant capabilities
- **Analytics Agent**: Processes assessment results to deliver ranked candidate recommendations with detailed soft-skill insights

Users authenticate as either recruiters or job seekers. Recruiters submit job descriptions to generate custom surveys, while candidates complete targeted assessments. The primary interaction model is conversational AI, making the process intuitive and adaptive.

### Current Status
- **Phase 1 (In Progress)**: Core infrastructure development including user authentication, basic page structure, and local environment setup
- **Phase 2 (Next)**: Survey generation engine and candidate assessment interface development
- **Phase 3 (Planned)**: Cloud deployment and production optimization

---

This document outlines how to effectively work with Google's Gemini AI assistant for this project, including our tech stack, coding standards, and interaction guidelines.

## Tech Stack

This project utilizes the following technologies:

### Backend & Framework
- **UV**: Dependency management for Python packages
- **FastAPI**: Modern, fast web framework for building APIs with Python
- **NiceGUI** ([https://nicegui.io/documentation](https://nicegui.io/documentation)): Python-based frontend framework for creating web interfaces

### Agent Orchestration
- **Google ADK** ([https://google.github.io/adk-docs/](https://google.github.io/adk-docs/)): Agent Development Kit for orchestrating AI agents and workflows

### Cloud Infrastructure
- **Google Cloud Platform** - Primary cloud provider
- **Cloud Run** - Serverless container deployment platform
- **Firebase Auth**: User authentication and authorization
- **Firestore**: NoSQL document database for application data
- **Firebase Storage**: Cloud storage for user uploads and file management

## Architecture Requirements

### Authentication & Authorization
- **Firebase Auth** - User authentication and identity management
  - Integration with FastAPI for token verification
  - Client-side SDK integration with NiceGUI frontend
  - User management dashboard access

### Data Storage Strategy

#### Primary Database
- **Firestore** - NoSQL document database for application data
  - Schemaless document structure
  - Real-time synchronization capabilities
  - Integration with Firebase Auth for security rules

#### File Storage
- **Firebase Storage** - User-generated content and file uploads
- **Cloud Storage** - Application assets, ML models, and static files

#### Vector Storage (if needed)
- **Vertex AI Vector Search** - For AI/ML features requiring similarity search
- Alternative: Evaluate Pinecone or other vector databases based on requirements

## Code Style Guidelines

When contributing code, please adhere to the following style guidelines:

### Core Principles
- **No Defensive Coding**: Avoid adding overly defensive code. Trust the contracts and inputs.
- **Simplicity Over Complexity**: Always strive for the simplest solution to a problem, even if it means some repetition.
- **Leverage Existing Libraries**: Prefer using libraries already present in the project over introducing new ones, where feasible.
- **Avoid JavaScript**: Minimize or avoid the use of JavaScript unless absolutely necessary and no alternative within the existing stack (e.g., NiceGUI capabilities) exists.

### Python Standards
```python
# Simple, direct function implementations
def calculate_user_score(activities: list[dict]) -> float:
    total_points = sum(activity['points'] for activity in activities)
    return total_points / len(activities) if activities else 0.0

# Use type hints consistently
from typing import Optional

def get_user_data(user_id: str) -> Optional[dict]:
    # Trust the input, no excessive validation
    doc = firestore_client.collection('users').document(user_id).get()
    return doc.to_dict() if doc.exists else None
```

### FastAPI Patterns
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    email: str
    name: str

@app.post("/users/")
async def create_user(user: UserCreate):
    # Simple, direct implementation
    user_data = user.dict()
    doc_ref = firestore_client.collection('users').add(user_data)
    return {"user_id": doc_ref[1].id, "message": "User created successfully"}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user_data = get_user_data(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    return user_data
```

### NiceGUI Interface Patterns
```python
from nicegui import ui, app

def create_user_dashboard(user_id: str):
    user_data = get_user_data(user_id)
    
    with ui.card().classes('w-full max-w-md'):
        ui.label(f"Welcome, {user_data['name']}").classes('text-2xl font-bold')
        ui.label(f"Email: {user_data['email']}")
        
        # Use NiceGUI's built-in capabilities instead of custom JS
        ui.button('Update Profile', on_click=lambda: update_profile_dialog(user_id))

def update_profile_dialog(user_id: str):
    with ui.dialog() as dialog, ui.card():
        ui.label('Update Profile')
        name_input = ui.input('Name')
        ui.button('Save', on_click=lambda: save_and_close(user_id, name_input.value, dialog))

def save_and_close(user_id: str, new_name: str, dialog):
    # Simple update operation
    firestore_client.collection('users').document(user_id).update({'name': new_name})
    dialog.close()
    ui.notify('Profile updated successfully')
```

### Cloud Run Deployment
```python
# Dockerfile example for Cloud Run
FROM python:3.11-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run the application
CMD ["uv", "run", "python", "main.py", "--host", "0.0.0.0", "--port", "8080"]
```

### Google Cloud Storage Integration
```python
from google.cloud import storage

def upload_to_gcs(file_data: bytes, bucket_name: str, blob_name: str) -> str:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(file_data)
    return blob.public_url

def download_from_gcs(bucket_name: str, blob_name: str) -> bytes:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_bytes()
```

### Vertex AI Vector Search Integration
```python
from google.cloud import aiplatform

def create_vector_index(project_id: str, location: str, display_name: str):
    client = aiplatform.gapic.IndexServiceClient()
    parent = f"projects/{project_id}/locations/{location}"
    
    index = aiplatform.gapic.Index(
        display_name=display_name,
        description="Vector search index for similarity matching"
    )
    
    operation = client.create_index(parent=parent, index=index)
    return operation.result()

def search_vectors(query_vector: list[float], index_name: str) -> list[dict]:
    # Simple vector similarity search implementation
    # Integrate with your specific vector search requirements
    pass
```

## Working with Gemini

### Effective Prompting Strategies
1. **Be Specific About Stack**: Always mention you're working with FastAPI + NiceGUI + Firebase
2. **Request Simple Solutions**: Ask for straightforward implementations without defensive coding
3. **Specify No JavaScript**: Explicitly request Python-only solutions using NiceGUI capabilities
4. **Include Context**: Mention Google ADK when working with agent orchestration

### Code Generation Requests
When asking Gemini to generate code:

```
Generate a FastAPI endpoint that:
- Uses simple, direct implementation (no defensive coding)
- Integrates with Firestore for data persistence
- Returns clear error messages using HTTPException
- Follows our existing patterns in the codebase
```

```
Create a NiceGUI interface component that:
- Uses only NiceGUI built-in elements (no custom JavaScript)
- Implements simple, clean styling with classes
- Handles user interactions through Python callbacks
- Integrates with our Firebase backend
```

```
Design a Google ADK agent workflow that:
- Orchestrates multiple AI agents for [specific task]
- Uses simple configuration patterns
- Integrates with our FastAPI backend
- Follows ADK best practices from the documentation
```

### Code Review Requests
```
Review this Python code for:
- Adherence to our "no defensive coding" principle
- Simplicity and directness of implementation
- Proper use of existing libraries (FastAPI, NiceGUI, Firebase)
- Avoidance of unnecessary JavaScript
- Type hint usage and clarity
```

### Debugging Assistance
```
I'm encountering [specific error] in [FastAPI/NiceGUI/Firebase/ADK].
Context: [brief description of functionality]
Current code: [paste relevant Python code]
Error message: [paste error]
Expected behavior: [what should happen]
Please provide the simplest solution using our existing stack.
```

## Project-Specific Instructions

### Firebase Integration
- Use Firebase Admin SDK for server-side operations
- Implement simple document reads/writes without excessive error handling
- Trust Firebase's built-in validation and constraints
- Use subcollections for related data (e.g., user activities, uploads)

### NiceGUI Development
- Leverage NiceGUI's reactive elements instead of custom JavaScript
- Use built-in styling classes for consistent appearance
- Implement user interactions through Python event handlers
- Utilize NiceGUI's built-in components (cards, dialogs, notifications)

### FastAPI API Design
- Keep endpoint logic simple and direct
- Use Pydantic models for request/response validation
- Implement straightforward error handling with HTTPException
- Follow RESTful conventions where appropriate

### Google ADK Agent Patterns
- Configure agents using simple dictionary-based configurations
- Chain agents using ADK's built-in orchestration patterns
- Integrate agent outputs directly with FastAPI endpoints
- Keep agent logic focused and single-purpose

## Common Patterns

### User Authentication Flow
```python
from firebase_admin import auth

def verify_user_token(token: str) -> str:
    # Simple token verification
    decoded_token = auth.verify_id_token(token)
    return decoded_token['uid']

@app.get("/protected-endpoint")
async def protected_route(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    user_id = verify_user_token(token)
    return {"user_id": user_id, "message": "Access granted"}
```

### File Upload Pattern
```python
from firebase_admin import storage

@app.post("/upload")
async def upload_file(file: UploadFile, user_id: str):
    bucket = storage.bucket()
    blob = bucket.blob(f"uploads/{user_id}/{file.filename}")
    blob.upload_from_file(file.file)
    return {"download_url": blob.public_url}
```

### NiceGUI Page Structure
```python
@ui.page('/dashboard')
def dashboard_page():
    ui.label('Dashboard').classes('text-3xl font-bold mb-4')
    
    with ui.row().classes('w-full gap-4'):
        create_stats_card()
        create_activity_card()
        create_upload_card()

def create_stats_card():
    with ui.card().classes('flex-1'):
        ui.label('Statistics').classes('text-xl font-semibold')
        # Simple data display without complex state management
        stats = get_user_stats(get_current_user_id())
        ui.label(f"Total Activities: {stats['total']}")
```

## Dependency Management with UV

### Adding Dependencies
```bash
# Add a new dependency
uv add fastapi[all]
uv add nicegui
uv add firebase-admin

# Add development dependencies
uv add --dev pytest
uv add --dev black
```

### Project Setup
```bash
# Initialize new project
uv init my-project
cd my-project

# Install dependencies
uv sync

# Run the application
uv run python main.py
```

## Testing Guidelines
- Write simple, focused tests that verify core functionality
- Use pytest for testing FastAPI endpoints
- Test NiceGUI components through their Python interfaces
- Mock Firebase operations for unit tests
- Keep test setup minimal and direct

## Documentation Standards
- Write clear docstrings for complex functions only
- Document ADK agent configurations and workflows
- Maintain API endpoint documentation with FastAPI's automatic docs
- Keep this guide updated as patterns evolve

