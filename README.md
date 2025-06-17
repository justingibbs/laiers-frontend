# laiers

## Project Purpose/Goal
An agent-powered job matching platform that revolutionizes hiring by identifying candidates with the essential soft skills needed to excel in GenAI-transformed workplaces. Rather than focusing on traditional hard skills that AI increasingly automates, the platform evaluates and matches based on uniquely human capabilities—creative problem-solving, emotional intelligence, adaptability, critical thinking, and collaborative leadership—that become more valuable as AI handles routine tasks. The platform connects Companies with Talent through AI-powered conversations and matching.

## Project Setup

This project uses [UV](https://github.com/astral-sh/uv) for dependency management and Google ADK (Agent Development Kit) for AI-powered agent functionality.

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd laiers
    ```

2.  **Install dependencies:**
    To install all production dependencies:
    ```bash
    uv sync
    ```
    To install all dependencies, including development tools like `pytest` and `black`:
    ```bash
    uv sync --extra dev
    ```

3.  **Google Cloud Setup:**
    Install the Google Cloud SDK:
    ```bash
    # On macOS
    brew install google-cloud-sdk
    ```
    
    Authenticate with Google Cloud:
    ```bash
    gcloud auth login
    gcloud auth application-default login
    gcloud config set project YOUR_PROJECT_ID
    ```

4.  **Environment Setup:**
    1. Download your Firebase service account key from the Firebase Console
    2. Save it as `config/firebase-credentials.json`
    3. Copy `.env.example` to `.env` and fill in your values:
       ```
       ENVIRONMENT=development
       GOOGLE_CLOUD_PROJECT=your-project-id
       VERTEX_AI_LOCATION=us-central1
       FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json
       ADK_BUCKET_NAME=your-bucket-name
       GOOGLE_GENAI_USE_VERTEXAI=true
       ```

5.  **Run the application:**
    ```bash
    # Start the development server
    uv run -- uvicorn main:app --reload --port 8000
    ```
    
    Then access the application at:
    ```
    http://localhost:8000
    ```
    
    Note: Use `http://` (not `https://`) for local development.

## Application URLs

Once the application is running, you can access these different interfaces:

### Main Application
- **Landing Page**: `http://localhost:8000/` - User registration and login
- **Registration**: `http://localhost:8000/register?user_type=talent` or `http://localhost:8000/register?user_type=company`
- **Login**: `http://localhost:8000/login`
- **Dashboard**: `http://localhost:8000/dashboard` - Main user interface with AI chat assistant

### Development & Debugging
- **ADK Dev UI**: `http://localhost:8000/adk/dev-ui/` - Google ADK development interface for testing agents
- **API Documentation**: `http://localhost:8000/adk/docs` - ADK API documentation
- **Debug Info**: `http://localhost:8000/debug/adk` - Agent configuration and status
- **Health Check**: `http://localhost:8000/health` - Application health status

### API Endpoints
- **Chat with Agent**: `POST /api/chat` - HTMX endpoint for chat interface
- **User Registration**: `POST /api/register` - Firebase registration endpoint
- **User Login**: `POST /api/login` - Firebase login endpoint
- **Logout**: `POST /api/logout` - User logout endpoint

## Project Architecture

### ADK Integration
The application uses Google's Agent Development Kit (ADK) to power the AI agent functionality:

- **Agent Structure**: The job matching agent is defined in `job_matching_agent/agent.py`
- **FastAPI Integration**: ADK provides a pre-configured FastAPI app mounted under `/adk`
- **Custom UI**: The main application provides custom authentication and user interface
- **Chat Interface**: Users interact with the agent through a custom HTMX-powered chat interface

### User Flow
1. **Landing Page** - Users choose between "Talent" or "Company" registration
2. **Registration/Login** - Firebase authentication with user type selection
3. **Dashboard** - Two-panel interface:
   - Left: User profile information
   - Right: AI chat assistant powered by ADK agent
4. **Agent Interaction** - Context-aware conversations based on user type (talent vs company)

## Development

### Logging and Debugging

The application uses Python's built-in logging module with different levels based on the environment:

- Development (`ENVIRONMENT=development`): DEBUG level logging
- Production: INFO level logging

Key logging features:
- Environment variable loading
- Firebase configuration and initialization
- User authentication events
- Firestore operations
- ADK agent mounting and configuration
- Error tracking

To view logs:
```bash
# Development mode (verbose logging)
ENVIRONMENT=development uv run -- uvicorn main:app --reload --port 8000

# Production mode (minimal logging)
ENVIRONMENT=production uv run -- uvicorn main:app --port 8000
```

### Testing the Agent

You can test the AI agent in multiple ways:

1. **Custom Chat Interface**: Use the dashboard at `http://localhost:8000/dashboard` after logging in
2. **ADK Dev UI**: Use the development interface at `http://localhost:8000/adk/dev-ui/`
3. **Direct API**: Make POST requests to `/adk/apps/job_matching_agent/users/{user_id}/sessions/{session_id}`

### Firebase Setup

1. Enable Firebase Authentication in the Firebase Console
2. Enable Firestore Database in the Firebase Console
3. Download your Firebase service account key from the Firebase Console
4. Save it as `config/firebase-credentials.json`
5. Copy `.env.example` to `.env` and fill in your values

Note: Firestore collections are created automatically when first used. No manual collection setup is required.

### Firebase Configuration Files

The application requires two Firebase configuration files:

1. **Server-side Configuration** (`config/firebase-credentials.json`):
   - Service account key for Firebase Admin SDK
   - Used for server-side operations (auth, Firestore)
   - Download from Firebase Console > Project Settings > Service Accounts
   - Contains sensitive credentials - never commit to version control

2. **Client-side Configuration** (`config/firebase-web-config.json`):
   - Web app configuration for Firebase client SDK
   - Used for client-side authentication
   - Download from Firebase Console > Project Settings > General > Your Apps > Web App
   - Example structure:
     ```json
     {
       "apiKey": "your-api-key",
       "authDomain": "your-project-id.firebaseapp.com",
       "projectId": "your-project-id",
       "storageBucket": "your-project-id.appspot.com",
       "messagingSenderId": "your-sender-id",
       "appId": "your-app-id"
     }
     ```

Both files should be placed in the `config/` directory. The `.gitignore` file is configured to exclude `firebase-credentials.json` but include `firebase-web-config.json` (with placeholder values).

## Project Structure

```
laiers/
├── main.py                     # Main FastAPI application with ADK integration
├── job_matching_agent/         # ADK agent directory
│   ├── __init__.py            # Agent module exports
│   └── agent.py               # Job matching agent definition
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── firestore.py           # Firestore database operations
│   └── models.py              # Pydantic data models
├── templates/                 # Jinja2 templates
│   ├── base.html             # Base template
│   ├── landing.html          # Landing page
│   ├── register.html         # Registration page
│   ├── login.html            # Login page
│   ├── dashboard.html        # Main dashboard with chat
│   └── components/           # Reusable components
│       ├── chat_message.html # Chat message component
│       └── chat_error.html   # Chat error component
├── static/                   # Static assets
│   └── css/
│       └── styles.css        # Application styles
├── config/                   # Configuration files
│   ├── firebase-credentials.json      # Firebase service account (excluded from git)
│   └── firebase-web-config.json       # Firebase web config
├── .env                      # Environment variables (excluded from git)
├── .env.example             # Environment template
├── pyproject.toml           # UV project configuration
└── README.md               # This file
```

## Troubleshooting

### Common Issues

1. **ADK Dev UI not loading**: Make sure to use the trailing slash: `/adk/dev-ui/`
2. **Firebase errors**: Check that both configuration files are properly placed in `config/`
3. **Agent not found**: Verify the `job_matching_agent/` directory structure is correct
4. **Chat not working**: Check the browser console for JavaScript errors and server logs

### Debug Endpoints

- `/debug/adk` - Shows agent configuration and status
- `/health` - Application health check
- `/adk/docs` - ADK API documentation

### Logs to Check

When troubleshooting, look for these log messages:
- "ADK app created successfully"
- "ADK app mounted under /adk"
- "Firebase Admin SDK initialized successfully"
- "Firestore service initialized successfully"