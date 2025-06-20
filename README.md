# laiers

## Project Purpose/Goal
An agent-powered job matching platform that revolutionizes hiring by identifying candidates with the essential soft skills needed to excel in GenAI-transformed workplaces. Rather than focusing on traditional hard skills that AI increasingly automates, the platform evaluates and matches based on uniquely human capabilities—creative problem-solving, emotional intelligence, adaptability, critical thinking, and collaborative leadership—that become more valuable as AI handles routine tasks. The platform connects Companies with Talent through AI-powered conversations and matching.

## Project Setup

This project uses [UV](https://github.com/astral-sh/uv) for dependency management and Google ADK (Agent Development Kit) for AI-powered agent functionality.

### Prerequisites

1. **Google Cloud SDK** - Required for authentication and API access
   ```bash
   # On macOS
   brew install google-cloud-sdk
   
   # On Ubuntu/Debian
   sudo apt-get install google-cloud-sdk
   
   # On Windows - Download from https://cloud.google.com/sdk/docs/install
   ```

2. **Google Cloud Project** - You need a Google Cloud project with billing enabled

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd laiers
   ```

2. **Install dependencies:**
   ```bash
   # Install all production dependencies
   uv sync
   
   # Or install with development tools
   uv sync --extra dev
   ```

3. **Google Cloud Setup (CRITICAL):**
   
   **Enable Required APIs:**
   ```bash
   # Set your project ID
   gcloud config set project YOUR_PROJECT_ID
   
   # Enable Vertex AI API (REQUIRED for ADK)
   gcloud services enable aiplatform.googleapis.com
   
   # Enable Firestore API
   gcloud services enable firestore.googleapis.com
   ```
   
   **Authenticate:**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

4. **Firebase Setup:**
   1. Go to [Firebase Console](https://console.firebase.google.com/)
   2. Create a new project or select existing project
   3. Enable Authentication with Email/Password provider
   4. Enable Firestore Database in test mode
   5. **Download Service Account Key:**
      - Go to Project Settings → Service Accounts
      - Click "Generate new private key"
      - Save as `config/firebase-credentials.json`
   6. **Download Web App Config:**
      - Go to Project Settings → General → Your Apps
      - Add web app if needed, then copy config
      - Save as `config/firebase-web-config.json`

5. **Environment Setup:**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your values
   nano .env
   ```
   
   **Required environment variables:**
   ```bash
   # Environment
   ENVIRONMENT=development
   
   # Google Cloud - REQUIRED for ADK/Vertex AI
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GOOGLE_GENAI_USE_VERTEXAI=true
   
   # Firebase Authentication
   # DEVELOPMENT: Use JSON service account file
   FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json
   
   # PRODUCTION: Use Application Default Credentials (no file needed)
   
   # ADK Configuration (optional)
   ADK_BUCKET_NAME=your-bucket-name
   
   # Cloud Run Deployment (set automatically in production)
   PORT=8080
   MAINTENANCE_MODE=false
   ```

6. **Verify Setup:**
   ```bash
   # Test that everything is configured correctly
   uv run -- python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print('Project:', os.getenv('GOOGLE_CLOUD_PROJECT'))
   print('Location:', os.getenv('GOOGLE_CLOUD_LOCATION'))
   print('Firebase:', os.path.exists(os.getenv('FIREBASE_CREDENTIALS_PATH', '')))
   "
   ```

7. **Run the application:**
   ```bash
   # Start the development server
   uv run -- uvicorn main:app --reload --port 8000
   ```
   
   **Important:** Use `http://localhost:8000` (not `https://`) for local development.

8. **Test the Setup:**
   
   Visit `http://localhost:8000/test/adk-complete-flow` to verify ADK integration.
   
   **Expected result:**
   ```json
   {
     "session_creation": {"status_code": 400, "text": "{\"detail\":\"Session already exists: test_session_123\"}"},
     "message_send": {"status_code": 200, "success": true},
     "overall_success": true
   }
   ```
   
   - `400` for session creation is **normal** (session reuse)
   - `200` for message send means **ADK is working**
   - If you get `500` errors, check the troubleshooting section below

## Application URLs

Once the application is running, you can access these different interfaces:

### Main Application
- **Landing Page**: `http://localhost:8000/` - User registration and login
- **Registration**: `http://localhost:8000/register?user_type=talent` or `http://localhost:8000/register?user_type=company`
- **Login**: `http://localhost:8000/login`
- **Dashboard**: `http://localhost:8000/dashboard` - Main user interface with AI chat assistant

### Opportunity Management (NEW FEATURE)
- **Company Portal**: `http://localhost:8000/company/{company_id}` - Company page with opportunities list
- **Create Opportunity**: `http://localhost:8000/company/{company_id}/opportunities/create` - AI-guided job creation
- **Browse Opportunities**: `http://localhost:8000/opportunities` - All available jobs (talent users)
- **Opportunity Details**: `http://localhost:8000/opportunities/{opportunity_id}` - Job details + application form

### Development & Debugging
- **ADK Dev UI**: `http://localhost:8000/adk/dev-ui/` - Google ADK development interface for testing agents
- **API Documentation**: `http://localhost:8000/adk/docs` - ADK API documentation
- **Setup Test**: `http://localhost:8000/test/adk-complete-flow` - Verify ADK configuration
- **Debug Info**: `http://localhost:8000/debug/adk` - Agent configuration and status
- **Health Check**: `http://localhost:8000/health` - Application health status
- **Test Opportunities**: `http://localhost:8000/test/opportunities/{company_id}` - Debug opportunities data

### API Endpoints
- **Chat with Agent**: `POST /api/chat` - HTMX endpoint for chat interface
- **User Registration**: `POST /api/register` - Firebase registration endpoint
- **User Login**: `POST /api/login` - Firebase login endpoint
- **Logout**: `POST /api/logout` - User logout endpoint
- **Create Opportunity**: `POST /api/opportunities/create` - HTMX endpoint for AI-guided creation
- **Apply to Job**: `POST /api/opportunities/{opportunity_id}/apply` - Submit job application

## Project Architecture

### ADK Integration
The application uses Google's Agent Development Kit (ADK) to power the AI agent functionality:

- **Agent Structure**: The job matching agent is defined in `job_matching_agent/agent.py`
- **FastAPI Integration**: ADK provides a pre-configured FastAPI app mounted under `/adk`
- **Custom UI**: The main application provides custom authentication and user interface
- **Chat Interface**: Users interact with the agent through a custom HTMX-powered chat interface
- **Vertex AI Backend**: Uses Gemini models via Google Cloud Vertex AI

### User Flow
1. **Landing Page** - Users choose between "Talent" or "Company" registration
2. **Registration/Login** - Firebase authentication with user type selection
3. **Dashboard** - Two-panel interface:
   - Left: User profile information
   - Right: AI chat assistant powered by ADK agent
4. **Agent Interaction** - Context-aware conversations based on user type (talent vs company)

#### Company User Flow (NEW)
5. **Company Portal** - Access company page from dashboard
6. **Create Opportunities** - AI-guided job posting through chat interface
7. **Manage Opportunities** - View and manage posted jobs
8. **Review Applications** - View candidate applications (future feature)

#### Talent User Flow (NEW)
5. **Browse Opportunities** - Discover available jobs from dashboard
6. **View Job Details** - See complete job descriptions and requirements
7. **Apply to Jobs** - Complete custom survey applications
8. **Track Applications** - View application status (future feature)

### Technical Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   FastAPI App    │    │   Google Cloud  │
│                 │    │                  │    │                 │
│ • HTMX Forms    │───▶│ • Custom Routes  │───▶│ • Vertex AI     │
│ • Jinja2 HTML   │    │ • Firebase Auth  │    │ • Firestore     │
│ • CSS/Static    │    │ • ADK Mount      │    │ • ADK Backend   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ ADK Agent        │
                       │ /adk/*           │
                       │ • Agent Logic    │
                       │ • Session Mgmt   │
                       │ • LLM Interface  │
                       └──────────────────┘
```

## Opportunity Management System

The application includes a complete job opportunity management system that allows companies to create job postings through AI-guided conversations and enables talent users to discover and apply to opportunities.

### Key Features

#### For Company Users:
- **AI-Guided Job Creation**: Chat with the AI agent to create structured job postings
- **Company Portal**: Dedicated page showing all company opportunities
- **Automatic Publishing**: AI determines when job details are complete and auto-publishes
- **Survey Generation**: AI creates custom application questions for each job

#### For Talent Users:
- **Opportunity Discovery**: Browse all available jobs in a clean, searchable interface
- **Detailed Job Views**: See complete job descriptions, requirements, and company info
- **Custom Applications**: Complete personalized survey applications for each job
- **Application Tracking**: View application status and history

### Data Structure

The system uses Firestore collections:

- **opportunities**: Job postings with company info, requirements, and survey questions
- **applications**: User applications with survey responses and metadata
- **users**: Extended with company affiliations and profile data

### AI Integration

The ADK agent handles opportunity creation through structured conversations:
1. **Job Title & Description**: AI guides users through basic job details
2. **Requirements & Qualifications**: Collects necessary skills and experience
3. **Logistics**: Location, employment type, salary information
4. **Survey Questions**: AI generates 3-5 relevant application questions
5. **Auto-Publishing**: When complete, opportunity is automatically created

### Technical Implementation

- **HTMX-Powered**: Dynamic forms and real-time updates without page refreshes
- **Responsive Design**: Mobile-friendly interfaces for all opportunity pages
- **Component-Based**: Reusable templates for opportunity cards and forms
- **Error Handling**: Graceful fallbacks and user-friendly error messages
- **Performance Optimized**: Efficient Firestore queries with client-side sorting

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

1. **Setup Verification**: `http://localhost:8000/test/adk-complete-flow` - Automated test
2. **Custom Chat Interface**: Use the dashboard at `http://localhost:8000/dashboard` after logging in
3. **ADK Dev UI**: Use the development interface at `http://localhost:8000/adk/dev-ui/`
4. **Direct API**: Make POST requests to `/adk/run` with proper payload
5. **Opportunity Creation**: Test AI-guided job creation at `/company/{company_id}/opportunities/create`
6. **Opportunity Testing**: Debug opportunities data at `/test/opportunities/{company_id}`

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
├── job_matching_agent/         # ADK agent directory (REQUIRED structure)
│   ├── __init__.py            # Must contain: from . import agent
│   └── agent.py               # Job matching agent definition (root_agent variable)
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── firestore.py           # Firestore database operations + opportunity management
│   ├── auth.py                # Firebase authentication helpers
│   ├── middleware.py          # Maintenance mode middleware
│   └── models.py              # Pydantic data models
├── templates/                 # Jinja2 templates
│   ├── base.html             # Base template
│   ├── landing.html          # Landing page
│   ├── register.html         # Registration page
│   ├── login.html            # Login page
│   ├── dashboard.html        # Main dashboard with chat
│   ├── company.html          # Company portal with opportunities list
│   ├── opportunities_list.html # Browse all opportunities (talent users)
│   ├── create_opportunity.html # AI-guided opportunity creation
│   ├── opportunity_detail.html # Job details + application form
│   └── components/           # Reusable components
│       ├── chat_message.html # Chat message component
│       ├── chat_error.html   # Chat error component
│       ├── opportunity_card.html # Opportunity display card
│       └── survey_form.html  # Application survey form
├── static/                   # Static assets
│   └── css/
│       └── styles.css        # Application styles
├── config/                   # Configuration files
│   ├── firebase-credentials.json      # Firebase service account (excluded from git)
│   └── firebase-web-config.json       # Firebase web config
├── deployment/              # Cloud Run deployment system
│   ├── deploy.sh            # Full-featured deployment script
│   ├── quick-deploy.sh      # Quick deployment commands
│   ├── README.md            # Comprehensive deployment guide
│   └── cloudbuild.yaml      # Cloud Build configuration
├── Dockerfile               # Container configuration for Cloud Run
├── .dockerignore           # Files excluded from container build
├── run.py                  # Entry point for Cloud Run deployment
├── .env                    # Environment variables (excluded from git)
├── .env.example           # Environment template
├── pyproject.toml         # UV project configuration
└── README.md             # This file
```

## Troubleshooting

### Common Setup Issues

#### 1. ADK Agent Not Working (500 Internal Server Error)

**Symptoms:**
- `/test/adk-complete-flow` returns `"message_send": {"status_code": 500}`
- Agent responses fail in chat interface

**Solutions:**
```bash
# 1. Check if Vertex AI API is enabled
gcloud services list --enabled | grep aiplatform
# If not found, enable it:
gcloud services enable aiplatform.googleapis.com

# 2. Verify authentication
gcloud auth list
gcloud auth application-default login

# 3. Check environment variables
echo $GOOGLE_CLOUD_PROJECT
echo $GOOGLE_CLOUD_LOCATION

# 4. Test Google Cloud connection
gcloud auth application-default print-access-token
```

**Common Error Messages:**
- `"Vertex AI API has not been used in project"` → Enable Vertex AI API
- `"Project and location or API key must be set"` → Check environment variables
- `"403 PERMISSION_DENIED"` → Run `gcloud auth application-default login`

#### 2. Session Already Exists (400 Error)

**This is NORMAL behavior!** ADK reuses existing sessions. Only worry if the message sending fails (500 error).

Expected test result:
```json
{
  "session_creation": {"status_code": 400, "text": "Session already exists"},
  "message_send": {"status_code": 200, "success": true},
  "overall_success": true
}
```

#### 3. Firebase Configuration Issues

**Symptoms:**
- Login/registration fails
- "Firebase not initialized" errors
- Opportunity creation/retrieval fails

**Solutions:**
```bash
# Check Firebase files exist
ls -la config/
# Should show:
# firebase-credentials.json
# firebase-web-config.json

# Verify Firebase credentials format
python -c "
import json
with open('config/firebase-credentials.json') as f:
    data = json.load(f)
    print('Project ID:', data.get('project_id'))
    print('Client Email:', data.get('client_email'))
"

# Test Firestore collections (opportunities feature)
# Ensure Firestore is in test mode or has proper security rules
# Collections used: users, opportunities, applications
```

#### 4. Environment Variable Issues

**Check your `.env` file has the correct variable names:**
```bash
# CORRECT (use these):
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true

# INCORRECT (don't use these - these are outdated):
# VERTEX_AI_LOCATION=us-central1
# GCP_PROJECT=your-project-id

# NEW: Deployment variables (set automatically in Cloud Run)
PORT=8080
MAINTENANCE_MODE=false
```

### Debug Endpoints

Use these URLs to diagnose issues:

- **Setup Test**: `http://localhost:8000/test/adk-complete-flow` - Complete ADK workflow test
- **Health Check**: `http://localhost:8000/health` - Application health status
- **Debug Info**: `http://localhost:8000/debug/adk` - Agent configuration details
- **ADK Docs**: `http://localhost:8000/adk/docs` - ADK API documentation

### Logs to Check

When troubleshooting, look for these log messages:

**Success indicators:**
- "ADK app created successfully"
- "ADK app mounted under /adk"
- "Firebase Admin SDK initialized successfully"
- "Firestore service initialized successfully"
- "Found root_agent in job_matching_agent.agent"

**Error indicators:**
- "ValueError: Project and location or API key must be set"
- "403 PERMISSION_DENIED"
- "Vertex AI API has not been used"
- "Failed to load Firebase credentials"

### Step-by-Step Debugging

If the application isn't working, follow these steps:

1. **Basic Environment Check:**
   ```bash
   # Check environment variables
   cat .env
   
   # Verify Google Cloud setup
   gcloud config list
   gcloud auth list
   ```

2. **Google Cloud API Check:**
   ```bash
   # List enabled APIs
   gcloud services list --enabled | grep -E "(aiplatform|firestore)"
   
   # If missing, enable them:
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable firestore.googleapis.com
   ```

3. **Authentication Check:**
   ```bash
   # Test authentication
   gcloud auth application-default print-access-token
   
   # If fails, re-authenticate:
   gcloud auth application-default login
   ```

4. **Firebase Check:**
   ```bash
   # Verify Firebase files
   ls -la config/
   
   # Test Firebase credentials
   python -c "
   import firebase_admin
   from firebase_admin import credentials
   cred = credentials.Certificate('config/firebase-credentials.json')
   print('Firebase credentials valid')
   "
   ```

5. **ADK Test:**
   ```bash
   # Start server and test
   uv run -- uvicorn main:app --reload --port 8000 &
   
   # Test ADK endpoint
   curl http://localhost:8000/test/adk-complete-flow
   ```

### Getting Help

If you're still having issues:

1. **Check the console logs** when starting the application
2. **Use the test endpoint** `/test/adk-complete-flow` to get specific error details
3. **Verify all prerequisites** are installed and configured
4. **Check Google Cloud Console** that your project has billing enabled
5. **Ensure you're using the correct region** (us-central1 is recommended)

## Alternative Setup: Google AI Studio (Free Tier)

If you want to avoid Google Cloud costs during development, you can use Google AI Studio instead of Vertex AI:

1. **Get API Key:**
   - Visit [Google AI Studio](https://aistudio.google.com/)
   - Click "Get API Key"
   - Copy the API key

2. **Update Environment:**
   ```bash
   # In your .env file, replace Vertex AI settings with:
   GOOGLE_GENAI_API_KEY=your_api_key_here
   
   # Comment out or remove:
   # GOOGLE_GENAI_USE_VERTEXAI=true
   # GOOGLE_CLOUD_PROJECT=your-project-id
   # GOOGLE_CLOUD_LOCATION=us-central1
   ```

3. **No Authentication Required:**
   - Skip `gcloud auth` steps
   - No need to enable Vertex AI API

**Note:** Google AI Studio has rate limits and is for development only. Use Vertex AI for production.

## Deployment

The application is production-ready and can be deployed to Google Cloud Run with a complete maintenance mode system for safe deployments.

### 🔄 Local vs Cloud Run Comparison

| Aspect | Local Development (`uv run main.py`) | Cloud Run Production |
|--------|--------------------------------------|---------------------|
| **Command** | `uv run main.py` | Dockerfile + `uv run uvicorn` |
| **Port** | 8000 (hardcoded) | 8080 (from PORT env var) |
| **Firebase Auth** | JSON file (`config/firebase-credentials.json`) | Application Default Credentials |
| **Environment** | `.env` file | Cloud Run environment variables |
| **CORS** | Enabled (`allow_origins=["*"]`) | Disabled for security |
| **Logging** | DEBUG level | INFO level |
| **Configuration** | Development settings | Production optimized |
| **Cost** | Free (your machine) | Pay-per-request |
| **Scaling** | Single instance | Auto-scaling (0-10 instances) |

### 🚀 Quick Deployment

**Prerequisites:**
```bash
# Set your project ID
export GOOGLE_CLOUD_PROJECT=your-project-id

# Ensure you're authenticated
gcloud auth login
gcloud auth application-default login
```

**Deploy in 3 Commands:**
```bash
# 1. Deploy in maintenance mode (safe)
./deployment/quick-deploy.sh deploy

# 2. Test the deployment
curl "$(./deployment/quick-deploy.sh url)/health"

# 3. Make app live when ready
./deployment/quick-deploy.sh live
```

### 🎯 Maintenance Mode System

The deployment includes a maintenance mode feature that allows safe deployments:

- **Deploy in maintenance mode**: Users see a professional "Coming Soon" page
- **Test functionality**: Verify everything works before going live
- **Instant toggle**: Switch between maintenance/live with single command
- **Health checks always work**: Monitoring endpoints remain accessible
- **Cost-effective**: No need for separate staging environments

### 📋 Deployment Commands

**Quick Operations:**
```bash
./deployment/quick-deploy.sh deploy      # Deploy in maintenance mode
./deployment/quick-deploy.sh live        # Make app live
./deployment/quick-deploy.sh maintenance # Back to maintenance mode
./deployment/quick-deploy.sh url         # Get service URL
./deployment/quick-deploy.sh logs        # View recent logs
```

**Full-Featured Operations:**
```bash
./deployment/deploy.sh deploy            # Deploy with full options
./deployment/deploy.sh deploy-live       # Deploy live immediately
./deployment/deploy.sh maintenance-on    # Enable maintenance mode
./deployment/deploy.sh maintenance-off   # Disable maintenance mode
./deployment/deploy.sh status            # Detailed service status
./deployment/deploy.sh logs              # Comprehensive logs
```

### 🌍 Production Environment Variables

The deployment automatically sets these environment variables:

```bash
ENVIRONMENT=production
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true
MAINTENANCE_MODE=false
PORT=8080  # Set automatically by Cloud Run
```

### 🔒 Production Firebase Configuration

In production, the app uses **Application Default Credentials** instead of JSON files:

- **More secure**: No embedded credentials in containers
- **Automatic authentication**: Cloud Run provides credentials automatically
- **Easy management**: Rotate credentials through Google Cloud Console

### 📊 Cost Optimization

The deployment is optimized for cost-effectiveness:

- **Pay-per-request**: No traffic = no cost
- **Auto-scaling to zero**: Scales down when idle
- **Free tier**: Up to 2M requests/month included
- **Optimized resources**: 1Gi memory, efficient container

### 🔧 Troubleshooting Deployment

**Common Issues:**

1. **Project ID vs Project Number**: Use project ID (string), not project number (numeric)
2. **API Enablement**: Ensure Vertex AI and Cloud Run APIs are enabled
3. **Authentication**: Run `gcloud auth application-default login`
4. **Environment Variables**: Use `GOOGLE_CLOUD_LOCATION` not `VERTEX_AI_LOCATION`

**Debug Commands:**
```bash
# Check deployment status
./deployment/deploy.sh status

# View recent logs
./deployment/deploy.sh logs

# Test health endpoint
curl "$(./deployment/quick-deploy.sh url)/health"
```

### 📖 Complete Deployment Guide

See `deployment/README.md` for comprehensive deployment documentation including:
- Detailed setup instructions
- Firebase credentials configuration
- Manual deployment commands
- Monitoring and debugging
- Cost optimization strategies

### 🚦 Recommended Deployment Workflow

1. **Deploy in maintenance mode** → `./deployment/quick-deploy.sh deploy`
2. **Test the deployment** → Verify health checks and functionality
3. **Make live** → `./deployment/quick-deploy.sh live`
4. **Monitor** → Check logs and metrics

This approach ensures zero-downtime deployments and safe rollbacks.

## Contributing

When contributing to this project:

1. **Follow the established patterns** in `.cursorrules`
2. **Test ADK integration** using `/test/adk-complete-flow`
3. **Maintain the two-panel dashboard design**
4. **Use HTMX for dynamic interactions**
5. **Keep Firebase as the only authentication method**
6. **Store all data in Firestore**

## License

[Your license information here]