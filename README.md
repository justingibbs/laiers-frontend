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
- **Landing Page**: `http://localhost:8000/` - Professional branded landing with user type selection
- **Registration**: `http://localhost:8000/register?user_type=talent` or `http://localhost:8000/register?user_type=company`
- **Login**: `http://localhost:8000/login`
- **Dashboard**: `http://localhost:8000/dashboard` - Multi-section interface with personalized welcome and AI chat assistant

### Opportunity Management System
- **Company Portal**: `http://localhost:8000/company/{company_id}` - Company dashboard with opportunities management
- **Create Opportunity**: `http://localhost:8000/company/{company_id}/opportunities/create` - AI-guided job creation through chat
- **Browse Opportunities**: `http://localhost:8000/opportunities` - Card-based job discovery interface for talent users
- **Opportunity Details**: `http://localhost:8000/opportunities/{opportunity_id}` - Comprehensive job details with application form

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
- **Dynamic Form Fields**: `GET /api/form-fields/{user_type}` - HTMX dynamic form switching

## Project Architecture

### ADK Integration
The application uses Google's Agent Development Kit (ADK) to power the AI agent functionality:

- **Agent Structure**: The job matching agent is defined in `job_matching_agent/agent.py`
- **FastAPI Integration**: ADK provides a pre-configured FastAPI app mounted under `/adk`
- **Custom UI**: The main application provides professional branded authentication and user interface
- **Chat Interface**: Users interact with the agent through a sophisticated HTMX-powered chat interface with loading states
- **Vertex AI Backend**: Uses Gemini models via Google Cloud Vertex AI

### Enhanced User Flow

#### Landing Experience
1. **Professional Landing Page** - Laiers.ai branding with clear user type selection
2. **Dynamic Registration Forms** - HTMX-powered form switching based on user type selection
3. **Firebase Authentication** - Secure login/registration with session management

#### Dashboard Experience
4. **Multi-Section Dashboard** - Personalized welcome, user-type specific navigation, and AI chat
   - **Title Container**: Personalized welcome message
   - **Navigation Section**: Context-aware buttons (Company Portal vs Browse Opportunities)
   - **Profile Section**: Conditional display of talent user skills and experience
   - **Chat Section**: Enhanced AI assistant with loading indicators and auto-scroll

#### Company User Journey
5. **Company Portal** - Comprehensive company dashboard with opportunities management
6. **AI-Guided Job Creation** - Sophisticated chat interface for creating structured job postings
7. **Opportunity Management** - View, edit, and manage posted opportunities
8. **Application Review** - Review candidate applications and survey responses

#### Talent User Journey
5. **Opportunity Discovery** - Card-based browsing interface with rich job metadata
6. **Detailed Job Views** - Complete job descriptions with company information
7. **Custom Applications** - Personalized survey applications tailored to each opportunity
8. **Application Tracking** - View application status and history

### UI/UX Design System

#### Layout Patterns
- **Multi-Section Layouts**: Flexible grid systems that adapt to content and screen size
- **Card-Based Design**: Consistent card components for opportunity display
- **Progressive Enhancement**: HTMX for dynamic behavior while maintaining accessibility
- **Mobile-First Responsive**: Graceful degradation on smaller screens

#### Branding Implementation
- **Logo Integration**: Consistent Laiers.ai branding across all pages
- **Color Scheme**: Professional indigo (#6366f1) primary color with consistent application
- **Typography Hierarchy**: Clear content structure with semantic HTML
- **Visual Consistency**: Standardized spacing, colors, and component styling

#### Component Architecture
- **Shared Components**: Reusable header, form, and message components
- **Template Includes**: Consistent includes for common elements
- **Dynamic Loading**: HTMX-powered loading states and indicators
- **Error Handling**: User-friendly error messages and fallback states

### Technical Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   FastAPI App    │    │   Google Cloud  │
│                 │    │                  │    │                 │
│ • HTMX Forms    │───▶│ • Custom Routes  │───▶│ • Vertex AI     │
│ • Jinja2 HTML   │    │ • Firebase Auth  │    │ • Firestore     │
│ • Professional  │    │ • ADK Mount      │    │ • ADK Backend   │
│   UI Components │    │ • Component Sys  │    │ • Cloud Storage │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ ADK Agent        │
                       │ /adk/*           │
                       │ • Agent Logic    │
                       │ • Session Mgmt   │
                       │ • LLM Interface  │
                       │ • Job Matching   │
                       └──────────────────┘
```

## Opportunity Management System

The application features a comprehensive job opportunity management system with AI-powered creation and sophisticated user interfaces.

### Key Features

#### For Company Users:
- **AI-Guided Job Creation**: Interactive chat interface for creating structured job postings
- **Company Portal Dashboard**: Professional interface showing all company opportunities
- **Automatic Publishing**: AI determines when job details are complete and auto-publishes
- **Custom Survey Generation**: AI creates tailored application questions for each position
- **Rich Job Metadata**: Support for location, employment type, salary ranges, and detailed requirements

#### For Talent Users:
- **Card-Based Discovery**: Modern grid layout for browsing opportunities with rich previews
- **Advanced Filtering**: Browse opportunities by location, type, company, and other criteria
- **Detailed Job Views**: Comprehensive job descriptions with company information
- **Personalized Applications**: Custom survey applications tailored to each opportunity
- **Application Tracking**: View application status and history across all applied positions

### UI Components

#### Opportunity Cards
- **Rich Metadata Display**: Location (📍), employment type (💼), salary (💰) with emoji icons
- **Truncated Descriptions**: Preview text with expansion options
- **Tag System**: Visual tags for quick scanning of job characteristics
- **Clickable Areas**: Large touch targets for mobile accessibility
- **Empty States**: Professional messaging when no opportunities are available

#### Application Forms
- **Dynamic Survey Questions**: AI-generated questions specific to each opportunity
- **Validation States**: Real-time form validation with clear error messaging
- **Progress Indicators**: Visual feedback during form submission
- **Success Confirmations**: Clear next steps after successful application

### Data Architecture

The system uses Firestore collections with sophisticated data modeling:

- **opportunities**: Rich job data with company associations and survey configurations
- **applications**: User applications with structured survey responses and metadata
- **users**: Extended profiles with company affiliations and skill tracking
- **companies**: Company information and branding data

### AI Integration

The ADK agent provides intelligent opportunity management:
1. **Structured Conversations**: Guided dialogue for job creation
2. **Data Validation**: AI ensures completeness before publishing
3. **Question Generation**: Creates relevant application screening questions
4. **Content Optimization**: Suggests improvements to job descriptions
5. **Matching Insights**: Provides hiring recommendations based on applications

## Project Structure

```
laiers/
├── main.py                     # Main FastAPI application with ADK integration
├── job_matching_agent/         # ADK agent directory (REQUIRED structure)
│   ├── __init__.py            # Must contain: from . import agent
│   └── agent.py               # Job matching agent definition (root_agent variable)
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── firestore.py           # Enhanced Firestore operations + opportunity management
│   ├── auth.py                # Firebase authentication helpers
│   ├── middleware.py          # Maintenance mode middleware
│   └── model.py               # Pydantic data models
├── templates/                 # Professional Jinja2 templates
│   ├── base.html             # Base template with shared elements
│   ├── landing.html          # Branded landing page with user type selection
│   ├── register.html         # Registration with dynamic form switching
│   ├── login.html            # Professional login interface
│   ├── dashboard.html        # Multi-section dashboard with AI chat
│   ├── company.html          # Company portal with opportunity management
│   ├── opportunities_list.html # Card-based opportunity browsing
│   ├── create_opportunity.html # AI-guided opportunity creation
│   ├── opportunity_detail.html # Detailed job view with application form
│   └── components/           # Reusable template components
│       ├── header.html       # Shared header component
│       ├── chat_message.html # Chat message component
│       ├── chat_error.html   # Chat error component
│       ├── opportunity_card.html # Opportunity display card
│       ├── survey_form.html  # Application survey form
│       ├── chat.html         # Chat interface component
│       ├── forms.html        # Form components
│       └── messages.html     # Message display components
├── static/                   # Static assets with organized structure
│   ├── css/
│   │   ├── styles.css        # Main application styles
│   │   ├── opportunities.css # Opportunity browsing styles
│   │   ├── company.css       # Company portal styles
│   │   ├── create-opportunity.css # Opportunity creation styles
│   │   └── opportunity-detail.css # Job detail page styles
│   └── images/
│       ├── logo_laiers.png   # Main Laiers.ai logo
│       └── favicon.ico       # Site favicon
├── config/                   # Configuration files
│   ├── firebase-credentials.json      # Firebase service account (excluded from git)
│   └── firebase-web-config.json       # Firebase web config
├── deployment/              # Production deployment system
│   ├── deploy.sh            # Full-featured deployment script
│   ├── quick-deploy.sh      # Quick deployment commands
│   ├── README.md            # Comprehensive deployment guide
│   └── cloudbuild.yaml      # Cloud Build configuration
├── Dockerfile               # Optimized container configuration for Cloud Run
├── .dockerignore           # Files excluded from container build
├── run.py                  # Entry point for Cloud Run deployment
├── .env                    # Environment variables (excluded from git)
├── .env.example           # Environment template
├── pyproject.toml         # UV project configuration
└── README.md             # This comprehensive documentation
```

## Development

### Enhanced Logging and Debugging

The application features comprehensive logging with different levels based on environment:

- **Development** (`ENVIRONMENT=development`): DEBUG level with detailed component loading
- **Production**: INFO level with essential operation tracking

Key logging features:
- **Startup Sequence**: Environment loading, Firebase initialization, ADK mounting
- **User Authentication**: Registration, login, and session management events
- **Firestore Operations**: Database queries, opportunity management, and application tracking
- **ADK Integration**: Agent communication, session management, and response handling
- **UI Component Loading**: Template rendering, HTMX interactions, and error states

Enhanced debug endpoints:
- **Component Status**: `/debug/adk` - Agent configuration and health
- **Route Discovery**: `/debug/routes` - All available application routes
- **Firestore Data**: `/test/firestore-users` - User data debugging
- **Opportunity Testing**: `/test/opportunities/{company_id}` - Opportunity data validation

### Testing the Enhanced Agent System

Multiple testing approaches for the sophisticated agent system:

1. **Automated Verification**: `http://localhost:8000/test/adk-complete-flow` - Complete workflow test
2. **Interactive Dashboard**: Professional chat interface at `/dashboard` with loading states
3. **Opportunity Creation**: AI-guided job creation at `/company/{company_id}/opportunities/create`
4. **ADK Dev Interface**: Development tools at `/adk/dev-ui/` for direct agent testing
5. **API Testing**: Direct API calls to `/adk/run` with structured payloads
6. **Component Testing**: Individual component functionality through specialized endpoints

### Professional Firebase Configuration

The application requires comprehensive Firebase setup with enhanced security:

1. **Server-side Configuration** (`config/firebase-credentials.json`):
   - Service account key for Firebase Admin SDK
   - Server-side authentication and Firestore operations
   - Production security with Application Default Credentials
   - Never commit to version control - use `.gitignore` protection

2. **Client-side Configuration** (`config/firebase-web-config.json`):
   - Web app configuration for client-side Firebase SDK
   - Professional authentication flows with error handling
   - Secure API key management
   - Example structure with all required fields

Both configurations support the sophisticated user flows and opportunity management system.

## Troubleshooting

### Common Setup Issues

#### 1. Enhanced ADK Agent Issues (500 Internal Server Error)

**Symptoms:**
- `/test/adk-complete-flow` returns `"message_send": {"status_code": 500}`
- Agent responses fail in dashboard chat interface
- Opportunity creation chat interface not working

**Enhanced Solutions:**
```bash
# 1. Comprehensive API verification
gcloud services list --enabled | grep -E "(aiplatform|firestore|run)"
# Enable missing APIs:
gcloud services enable aiplatform.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable run.googleapis.com

# 2. Enhanced authentication check
gcloud auth list --filter=status:ACTIVE
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform

# 3. Environment validation
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Project:', os.getenv('GOOGLE_CLOUD_PROJECT'))
print('Location:', os.getenv('GOOGLE_CLOUD_LOCATION'))
print('Vertex AI:', os.getenv('GOOGLE_GENAI_USE_VERTEXAI'))
"

# 4. Advanced connection testing
gcloud auth application-default print-access-token | head -c 50
```

#### 2. UI Component and HTMX Issues

**Symptoms:**
- Dynamic form switching not working on landing page
- Chat interface not auto-scrolling
- Loading indicators not showing
- Opportunity cards not clickable

**Solutions:**
```bash
# Check static file serving
curl -I http://localhost:8000/static/css/styles.css

# Verify HTMX loading
curl -H "HX-Request: true" http://localhost:8000/api/form-fields/talent

# Test template rendering
curl -H "Accept: text/html" http://localhost:8000/opportunities
```

#### 3. Enhanced Firebase and Firestore Issues

**Symptoms:**
- User registration/login failures
- Opportunity creation not saving to Firestore  
- Application submissions failing
- Company portal not loading opportunities

**Enhanced Solutions:**
```bash
# Comprehensive Firebase validation
python -c "
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Test credentials
try:
    cred = credentials.Certificate('config/firebase-credentials.json')
    print('✓ Firebase credentials valid')
except Exception as e:
    print('✗ Firebase credentials error:', e)

# Test Firestore connection
try:
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print('✓ Firestore connection successful')
    
    # Test collections
    collections = ['users', 'opportunities', 'applications']
    for collection in collections:
        count = len(list(db.collection(collection).limit(1).stream()))
        print(f'✓ Collection {collection}: accessible')
except Exception as e:
    print('✗ Firestore error:', e)
"

# Check Firestore security rules
# Ensure collections are accessible in development mode
```

### Enhanced Debug Endpoints

Comprehensive debugging tools for the mature application:

- **Application Health**: `http://localhost:8000/health` - Full system status including Firebase and Firestore
- **Component Analysis**: `http://localhost:8000/debug/adk` - Agent configuration and component status
- **Route Discovery**: `http://localhost:8000/debug/routes` - All available routes with methods
- **User Data**: `http://localhost:8000/test/firestore-users` - User profile debugging
- **Opportunity System**: `http://localhost:8000/test/opportunities/{company_id}` - Opportunity data validation
- **Company Flow**: `http://localhost:8000/test/company-flow` - Complete company user journey testing

### Professional Error Handling

The application includes sophisticated error handling:

- **User-Friendly Messages**: Clear error communication without technical jargon
- **Fallback States**: Graceful degradation when services are unavailable
- **Loading States**: Visual feedback during all async operations
- **Validation Feedback**: Real-time form validation with contextual help
- **Empty States**: Professional messaging when no data is available

## Deployment

The application features a production-ready deployment system with professional maintenance mode and sophisticated monitoring.

### 🎯 Enhanced Maintenance Mode System

Professional deployment features:
- **Branded Maintenance Pages**: Custom "Coming Soon" pages with Laiers.ai branding
- **Component-Level Health Checks**: Individual service monitoring
- **Opportunity System Monitoring**: Specific checks for job posting and application systems
- **User Experience Continuity**: Smooth transitions between maintenance and live modes

### 🚀 Professional Deployment Workflow

**Enhanced Prerequisites:**
```bash
# Set environment with validation
export GOOGLE_CLOUD_PROJECT=your-project-id
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Comprehensive authentication
gcloud auth login
gcloud auth application-default login
gcloud auth configure-docker

# Validate all required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable firestore.googleapis.com
```

**Professional Deployment Commands:**
```bash
# 1. Deploy with comprehensive validation
./deployment/quick-deploy.sh deploy

# 2. Validate all systems including opportunities
curl "$(./deployment/quick-deploy.sh url)/health"
curl "$(./deployment/quick-deploy.sh url)/test/opportunities/company_1"

# 3. Professional go-live process
./deployment/quick-deploy.sh live
```

### 📊 Production Monitoring

Enhanced monitoring for the mature application:

```bash
# Comprehensive health check
curl "$(./deployment/quick-deploy.sh url)/health"

# Component-specific monitoring
curl "$(./deployment/quick-deploy.sh url)/debug/adk"

# Opportunity system health
curl "$(./deployment/quick-deploy.sh url)/test/opportunities/company_1"

# User system validation
curl "$(./deployment/quick-deploy.sh url)/test/firestore-users"
```

### 🎨 Production Branding

The production deployment maintains professional branding:
- **Consistent Logo Usage**: Proper logo sizing and placement
- **Professional Color Scheme**: Branded color palette throughout
- **Responsive Design**: Mobile-optimized layouts
- **Loading States**: Branded loading indicators and transitions

## Contributing

When contributing to this mature application:

1. **Follow Established Design Patterns**: Maintain consistency with card-based design, multi-section layouts, and component architecture
2. **Test Complete User Flows**: Verify both company and talent user journeys including opportunity management
3. **Maintain Branding Consistency**: Use established logo, colors, and typography patterns
4. **Validate HTMX Interactions**: Ensure loading states, auto-scroll, and dynamic form switching work properly
5. **Component-Based Development**: Use shared components and avoid duplicating template code
6. **Professional Error Handling**: Implement user-friendly error messages and fallback states
7. **Mobile-First Responsive**: Test layouts on various screen sizes and ensure graceful degradation
8. **Accessibility Standards**: Maintain semantic HTML, proper ARIA labels, and keyboard navigation

### Code Quality Standards

- **Template Organization**: Use component includes and maintain consistent structure
- **CSS Organization**: Separate styles by feature/page with clear naming conventions
- **HTMX Best Practices**: Implement proper loading indicators and error handling
- **Firebase Integration**: Follow security best practices and proper error handling
- **ADK Communication**: Use established HTTP API patterns and context passing

## License

[Your license information here]