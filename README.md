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
   
   # Enable Secret Manager API (for secure production config)
   gcloud services enable secretmanager.googleapis.com
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
   5. **Download Service Account Key (for local development):**
      - Go to Project Settings → Service Accounts
      - Click "Generate new private key"
      - Save as `config/firebase-credentials.json`
   6. **Get Web App Config (for frontend authentication):**
      - Go to Project Settings → General → Your Apps
      - Add web app if needed, then copy config
      - **For local development**: Save as `config/firebase-web-config.json`
      - **For production**: Use environment variables (see below)

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
   
   # Firebase Web Config (for frontend authentication)
   # DEVELOPMENT: Uses config/firebase-web-config.json file
   # PRODUCTION: Set these environment variables (required for Cloud Run)
   FIREBASE_API_KEY=your-firebase-api-key
   FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
   FIREBASE_STORAGE_BUCKET=your-project-id.firebasestorage.app
   FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id
   FIREBASE_APP_ID=your-firebase-app-id
   
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
- **Assessment**: `POST /api/opportunities/{opportunity_id}/assess` - Submit candidate assessment

## Project Architecture

### ADK Integration
The application uses Google's Agent Development Kit (ADK) to power the AI agent functionality:

- **Agent Structure**: The job matching agent is defined in `job_matching_agent/agent.py`
- **Sub-Agent Architecture**: Specialized sub-agents for job posting and candidate assessment
- **FastAPI Integration**: ADK provides a pre-configured FastAPI app mounted under `/adk`
- **Custom UI**: The main application provides professional branded authentication and user interface
- **Chat Interface**: Users interact with the agent through a sophisticated HTMX-powered chat interface with loading states
- **Vertex AI Backend**: Uses Gemini models via Google Cloud Vertex AI

### Agent Architecture
```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   Root Agent                                        │
│                              job_matching_agent                                     │
│                                                                                     │
│  • Main orchestration and routing                                                  │
│  • User context management (talent vs company)                                     │
│  • Task delegation to specialized sub-agents                                       │
│  • General job matching guidance and support                                       │
│                                                                                     │
│  ┌─────────────────────────────────┐    ┌─────────────────────────────────┐      │
│  │         Sub-Agent               │    │         Sub-Agent               │      │
│  │     job_posting_agent           │    │     assessment_agent            │      │
│  │                                 │    │                                 │      │
│  │ • AI-guided job creation        │    │ • Candidate evaluation          │      │
│  │ • Structured opportunity data   │    │ • Survey response analysis      │      │
│  │ • Survey question generation    │    │ • Candidate ranking             │      │
│  │ • Requirements optimization     │    │ • Interview recommendations     │      │
│  │ • Soft skills identification    │    │ • Strengths/weaknesses analysis │      │
│  │                                 │    │ • Red flag detection            │      │
│  │ Tools:                          │    │                                 │      │
│  │ • create_opportunity_structure  │    │ Tools:                          │      │
│  │ • generate_survey_questions     │    │ • analyze_candidate_fit         │      │
│  │ • validate_job_requirements     │    │ • rank_candidates               │      │
│  │                                 │    │ • generate_interview_questions  │      │
│  └─────────────────────────────────┘    └─────────────────────────────────┘      │
│                                                                                     │
│  Triggered by:                           Triggered by:                            │
│  • Task: create_opportunity              • Task: assess_candidates                │
│  • Company user context                  • Company user context                   │
│  • /api/opportunities/create             • /api/opportunities/{id}/assess         │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │   Data Flow     │
                                   │                 │
                                   │ Firestore       │
                                   │ • opportunities │
                                   │ • applications  │
                                   │ • users         │
                                   │ • companies     │
                                   └─────────────────┘
```

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
8. **Candidate Assessment** - AI-powered evaluation interface for reviewing applications
9. **Application Review** - Comprehensive candidate analysis with ranking and interview recommendations

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
│ • Assessment UI │    │ • Assessment API │    │ • Sub-Agents    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ ADK Agent        │
                       │ /adk/*           │
                       │ • Root Agent     │
                       │ • Sub-Agents     │
                       │ • Session Mgmt   │
                       │ • LLM Interface  │
                       │ • Job Matching   │
                       │ • Assessment     │
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

## Assessment System

The application features a comprehensive AI-powered candidate assessment system that helps company users evaluate job applicants efficiently and objectively.

### Key Features

#### Assessment Sub-Agent
- **Specialized AI Assistant**: Dedicated assessment_agent for candidate evaluation
- **Survey Response Analysis**: Deep analysis of candidate answers against job requirements
- **Candidate Ranking**: Objective scoring and ranking of applicants
- **Interview Recommendations**: Tailored interview questions for each candidate
- **Red Flag Detection**: Identification of concerning responses or gaps
- **Strengths Analysis**: Highlighting candidate qualifications and potential

#### Assessment Interface
- **Integrated Chat Interface**: Seamlessly integrated into opportunity detail pages
- **Company User Access**: Only visible to company users who own the opportunity
- **Real-time Analysis**: Instant AI-powered insights and recommendations
- **Application Statistics**: Clear display of candidate count and application status
- **Professional UI**: Consistent with the overall application design

### Assessment Workflow

#### For Company Users:
1. **Access Assessment**: Navigate to any opportunity detail page they own
2. **View Application Stats**: See number of candidates who have applied
3. **Request Analysis**: Ask the AI to evaluate specific candidates or all applicants
4. **Receive Insights**: Get comprehensive evaluations including:
   - Candidate ranking and fit assessment
   - Strengths and weaknesses analysis
   - Response quality evaluation
   - Interview question recommendations
   - Hiring recommendations

#### Assessment Capabilities:
- **Individual Evaluation**: "Assess candidate John Smith's responses"
- **Bulk Analysis**: "Rank all candidates for this position"
- **Comparative Analysis**: "Compare the top 3 candidates"
- **Interview Preparation**: "Suggest interview questions for Sarah Johnson"
- **Red Flag Identification**: "Are there any concerning responses?"
- **Skill Matching**: "Which candidates best match our requirements?"

### Technical Implementation

#### Assessment Agent Architecture
```python
# job_matching_agent/assessment_agent.py
assessment_agent = LlmAgent(
    name="assessment_agent",
    model="gemini-2.0-flash-lite",
    instruction="""You are a candidate assessment specialist...""",
    tools=[
        FunctionTool(analyze_candidate_fit),
        FunctionTool(rank_candidates),
        FunctionTool(generate_interview_questions)
    ]
)
```

#### Data Processing
- **Robust Format Handling**: Supports both string and dictionary survey question formats
- **Response Quality Analysis**: Evaluates completeness and relevance of candidate answers
- **Scoring Algorithms**: Objective assessment based on job requirements and response quality
- **Context Preservation**: Maintains job description and requirements throughout evaluation

#### API Integration
- **Dedicated Endpoint**: `POST /api/opportunities/{opportunity_id}/assess`
- **HTMX Interface**: Real-time chat interface with loading states
- **Access Control**: Secure access limited to opportunity owners
- **Error Handling**: Graceful failure handling with user-friendly messages

### Assessment UI Components

#### Assessment Chat Interface
```html
<!-- Professional assessment interface -->
<div class="assessment-section">
    <div class="assessment-header">
        <h2 class="assessment-title">🎯 Candidate Assessment</h2>
        <div class="assessment-stats">
            <span class="stat-item">
                <strong>{{ applications_count }}</strong> 
                candidate{{ 's' if applications_count != 1 else '' }} applied
            </span>
        </div>
    </div>
    
    <div class="assessment-chat-container">
        <!-- Chat messages and input form -->
    </div>
</div>
```

#### Features
- **Application Statistics**: Real-time display of candidate count
- **Professional Styling**: Consistent with application design system
- **Loading Indicators**: Visual feedback during AI processing
- **Auto-scroll**: Smooth scrolling for chat interactions
- **Mobile Responsive**: Optimized for all screen sizes

### Assessment Examples

#### Sample Interactions:
- **"Evaluate all candidates for this position"** → Comprehensive ranking with scores
- **"What are the red flags in the applications?"** → Identification of concerning responses
- **"Suggest interview questions for the top candidate"** → Tailored interview preparation
- **"Compare John and Sarah's qualifications"** → Side-by-side candidate analysis
- **"Who has the best communication skills?"** → Skill-specific assessment

#### Assessment Output:
- **Candidate Rankings**: Objective scoring from 1-10
- **Fit Analysis**: Match percentage against job requirements
- **Response Quality**: Evaluation of answer completeness and relevance
- **Strengths/Weaknesses**: Balanced assessment of candidate qualities
- **Interview Recommendations**: Specific questions to explore with each candidate
- **Hiring Advice**: Clear recommendations on next steps

## Project Structure

```
laiers/
├── main.py                     # Main FastAPI application with ADK integration
├── job_matching_agent/         # ADK agent directory (REQUIRED structure)
│   ├── __init__.py            # Must contain: from . import agent
│   ├── agent.py               # Job matching agent definition (root_agent variable)
│   ├── job_posting_agent.py   # Sub-agent for AI-guided job creation
│   └── assessment_agent.py    # Sub-agent for candidate evaluation and ranking
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── firestore.py           # Enhanced Firestore operations + opportunity management
│   ├── auth.py                # Firebase authentication helpers
│   ├── middleware.py          # Maintenance mode middleware
│   ├── secrets.py             # Google Cloud Secret Manager utilities
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
│   ├── opportunity_detail.html # Detailed job view with application form + assessment interface
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
│   │   └── opportunity-detail.css # Job detail page + assessment interface styles
│   └── images/
│       ├── logo_laiers.png   # Main Laiers.ai logo
│       └── favicon.ico       # Site favicon
├── config/                   # Configuration files
│   ├── firebase-credentials.json      # Firebase service account (local dev only - excluded from git)
│   └── firebase-web-config.json       # Firebase web config (local dev only - excluded from git)
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
- **Secret Manager Status**: `/debug/secrets` - Secret Manager configuration and access
- **Route Discovery**: `/debug/routes` - All available application routes
- **Firestore Data**: `/test/firestore-users` - User data debugging
- **Opportunity Testing**: `/test/opportunities/{company_id}` - Opportunity data validation

### Testing the Enhanced Agent System

Multiple testing approaches for the sophisticated agent system:

1. **Automated Verification**: `http://localhost:8000/test/adk-complete-flow` - Complete workflow test
2. **Interactive Dashboard**: Professional chat interface at `/dashboard` with loading states
3. **Opportunity Creation**: AI-guided job creation at `/company/{company_id}/opportunities/create`
4. **Assessment Interface**: Candidate evaluation at `/opportunities/{opportunity_id}` (company users only)
5. **ADK Dev Interface**: Development tools at `/adk/dev-ui/` for direct agent testing
6. **API Testing**: Direct API calls to `/adk/run` with structured payloads
7. **Component Testing**: Individual component functionality through specialized endpoints

#### Testing Assessment Features

**Prerequisites for Assessment Testing:**
1. **Company User Account**: Register as a company user
2. **Published Opportunity**: Create at least one job opportunity
3. **Candidate Applications**: Have talent users apply to the opportunity
4. **Survey Responses**: Ensure applications include survey responses

**Assessment Test Workflow:**
```bash
# 1. Create test opportunity with company user
curl -X POST http://localhost:8000/api/opportunities/create \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "company_id=company_1&message=Create a Senior Developer position"

# 2. Apply as talent user with survey responses
curl -X POST http://localhost:8000/api/opportunities/{opportunity_id}/apply \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "question_0=I have 5 years experience...&question_1=Led a team of 3..."

# 3. Test assessment interface (company user)
curl -X POST http://localhost:8000/api/opportunities/{opportunity_id}/assess \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "message=Evaluate all candidates for this position"
```

**Assessment UI Testing:**
1. **Access Control**: Verify assessment interface only shows for opportunity owners
2. **Application Count**: Confirm candidate statistics display correctly
3. **Chat Interface**: Test assessment chat functionality and loading states
4. **Response Quality**: Verify AI provides comprehensive candidate evaluations
5. **Mobile Responsive**: Test assessment interface on various screen sizes

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

## Security and Configuration Management

### Google Cloud Secret Manager Integration

For production deployments, the application uses Google Cloud Secret Manager to securely store and manage sensitive configuration data like API keys and authentication credentials.

#### Why Secret Manager?

- **Enhanced Security**: No sensitive data in environment variables or container images
- **Easy Rotation**: Update secrets without redeployment
- **Audit Trail**: Track who accessed what secrets when
- **IAM Integration**: Fine-grained access control with Google Cloud IAM
- **Version Management**: Keep track of secret versions and rollback if needed

#### Setting Up Secret Manager

**1. Enable Secret Manager API:**
```bash
gcloud services enable secretmanager.googleapis.com
```

**2. Create Firebase Configuration Secrets:**
```bash
# Create individual Firebase config secrets
echo "YOUR_FIREBASE_API_KEY" | gcloud secrets create firebase-api-key --data-file=-
echo "YOUR_PROJECT_ID.firebaseapp.com" | gcloud secrets create firebase-auth-domain --data-file=-
echo "YOUR_PROJECT_ID.firebasestorage.app" | gcloud secrets create firebase-storage-bucket --data-file=-
echo "YOUR_MESSAGING_SENDER_ID" | gcloud secrets create firebase-messaging-sender-id --data-file=-
echo "YOUR_FIREBASE_APP_ID" | gcloud secrets create firebase-app-id --data-file=-

# Or create a complete config as JSON
echo '{"apiKey":"YOUR_API_KEY","authDomain":"..."}' | gcloud secrets create firebase-web-config --data-file=-
```

**3. Grant Cloud Run Access to Secrets:**
```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")

# Grant secret access to Cloud Run service account
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

**4. Deploy with Secret Manager:**
```bash
# Deploy without sensitive environment variables
gcloud run deploy job-matching-app \
    --source . \
    --region us-central1 \
    --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"
```

#### Configuration Loading Priority

The application loads configuration in this order:

1. **Production**: Google Cloud Secret Manager (most secure)
2. **Development**: Local JSON files (`config/firebase-web-config.json`)
3. **Fallback**: Environment variables (legacy support)

#### Rotating API Keys

With Secret Manager, rotating API keys is simple:

```bash
# Update the secret with new API key
echo "NEW_API_KEY" | gcloud secrets versions add firebase-api-key --data-file=-

# The change takes effect immediately - no redeployment needed
```

#### Testing Secret Manager

Use the debug endpoint to verify Secret Manager integration:

```bash
# Test locally
curl http://localhost:8000/debug/secrets

# Test in production
curl https://your-app-url/debug/secrets
```

Expected response when working correctly:
```json
{
  "status": "ok",
  "secret_manager_available": true,
  "api_key_available": true,
  "complete_config_available": true,
  "config_keys": ["apiKey", "authDomain", "projectId", "storageBucket", "messagingSenderId", "appId"]
}
```

## Troubleshooting

### Common Setup Issues

#### 1. Enhanced ADK Agent Issues (500 Internal Server Error)

**Symptoms:**
- `/test/adk-complete-flow` returns `"message_send": {"status_code": 500}`
- Agent responses fail in dashboard chat interface
- Opportunity creation chat interface not working
- Assessment interface returns errors

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

#### 2. Assessment Feature Issues (NEW)

**Symptoms:**
- Assessment interface not visible on opportunity detail pages
- Assessment chat returns errors or timeouts
- Candidate evaluation responses are incomplete or incorrect
- Applications count shows 0 when applications exist

**Assessment-Specific Solutions:**

**A. Assessment Interface Not Showing:**
```bash
# Check user access and company ownership
python -c "
import asyncio
from utils.firestore import FirestoreService

async def check_access():
    fs = FirestoreService()
    
    # Check opportunity ownership
    opportunity = await fs.get_opportunity('your_opportunity_id')
    print('Opportunity company_id:', opportunity.get('company_id'))
    
    # Check user profile
    user_profile = await fs.get_user_profile('your_user_id')
    print('User company_id:', user_profile.get('company_id'))
    print('User type:', user_profile.get('user_type'))
    
    # Check applications
    applications = await fs.get_applications_by_opportunity('your_opportunity_id')
    print('Applications count:', len(applications))

asyncio.run(check_access())
"
```

**B. Assessment Agent Errors:**
```bash
# Verify assessment agent structure
python -c "
try:
    from job_matching_agent.assessment_agent import assessment_agent
    print('✓ Assessment agent imported successfully')
    print('Agent name:', assessment_agent.name)
    print('Agent model:', assessment_agent.model)
except Exception as e:
    print('✗ Assessment agent error:', e)
"

# Check if assessment agent is properly integrated
python -c "
try:
    from job_matching_agent.agent import root_agent
    print('✓ Root agent imported successfully')
    print('Available tools:', [tool.name for tool in root_agent.tools if hasattr(tool, 'name')])
except Exception as e:
    print('✗ Root agent error:', e)
"
```

**C. Data Format Issues:**
```bash
# Check survey question formats in Firestore
python -c "
import asyncio
from utils.firestore import FirestoreService

async def check_survey_format():
    fs = FirestoreService()
    opportunity = await fs.get_opportunity('your_opportunity_id')
    
    survey_questions = opportunity.get('survey_questions', [])
    print(f'Survey questions count: {len(survey_questions)}')
    
    for i, question in enumerate(survey_questions):
        print(f'Question {i}: {type(question)} - {question}')

asyncio.run(check_survey_format())
"
```

**D. Assessment Timeout Issues:**
```bash
# Test assessment endpoint with timeout monitoring
curl -X POST http://localhost:8000/api/opportunities/your_opportunity_id/assess \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "message=Test assessment functionality" \
  --max-time 35 \
  -w "Total time: %{time_total}s\n"
```

#### 3. UI Component and HTMX Issues

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

#### 4. Enhanced Firebase and Firestore Issues

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

#### 5. Google Cloud Secret Manager Issues (NEW)

**Symptoms:**
- Production login/registration fails with Firebase configuration errors
- `/debug/secrets` shows `secret_manager_available: false` or empty config
- API key rotation doesn't take effect
- Permission denied errors accessing secrets

**Solutions:**

**A. Secret Manager Not Available:**
```bash
# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Verify secrets exist
gcloud secrets list | grep firebase
```

**B. Permission Denied Accessing Secrets:**
```bash
# Get your project number and service account
PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")
SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

# Grant access to Secret Manager
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

# Verify IAM binding
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT \
    --flatten="bindings[].members" \
    --format="table(bindings.role,bindings.members)" \
    --filter="bindings.members:$SERVICE_ACCOUNT"
```

**C. Secrets Not Loading in Production:**
```bash
# Test secret access from Cloud Run
curl "https://your-app-url/debug/secrets"

# Check logs for Secret Manager messages
gcloud run services logs read job-matching-app --region=us-central1 | grep -i secret

# Verify environment variable
gcloud run services describe job-matching-app --region=us-central1 \
    --format="value(spec.template.spec.containers[0].env[?(@.name=='ENVIRONMENT')].value)"
```

**D. API Key Rotation Issues:**
```bash
# Verify secret version was created
gcloud secrets versions list firebase-api-key

# Check if new version is being accessed
gcloud secrets versions access latest --secret="firebase-api-key"

# Force restart Cloud Run to pick up changes (usually not needed)
gcloud run services update job-matching-app --region=us-central1
```

**E. Local Development Secret Testing:**
```bash
# Test Secret Manager utilities locally
python -c "
from utils.secrets import get_secret, load_firebase_config_from_secrets
print('API Key available:', bool(get_secret('firebase-api-key')))
config = load_firebase_config_from_secrets()
print('Config loaded:', bool(config))
print('Config keys:', list(config.keys()) if config else 'None')
"
```

### Enhanced Debug Endpoints

Comprehensive debugging tools for the mature application:

- **Application Health**: `http://localhost:8000/health` - Full system status including Firebase and Firestore
- **Component Analysis**: `http://localhost:8000/debug/adk` - Agent configuration and component status
- **Secret Manager Status**: `http://localhost:8000/debug/secrets` - Secret Manager configuration and access verification
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

# 2. Set Firebase environment variables for production (REQUIRED for authentication)
gcloud run services update job-matching-app \
  --region us-central1 \
  --set-env-vars="FIREBASE_API_KEY=your-firebase-api-key,FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com,FIREBASE_STORAGE_BUCKET=your-project-id.firebasestorage.app,FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id,FIREBASE_APP_ID=your-firebase-app-id"

# 3. Validate all systems including opportunities
curl "$(./deployment/quick-deploy.sh url)/health"
curl "$(./deployment/quick-deploy.sh url)/test/opportunities/company_1"

# 4. Professional go-live process
./deployment/quick-deploy.sh live
```

**⚠️ Important: Firebase Environment Variables**

For production deployment, you MUST set Firebase environment variables for frontend authentication to work. Get these values from your Firebase project:

1. Go to Firebase Console → Project Settings → General → Your Apps
2. Copy the config values and set them as environment variables:
   ```bash
   # Example values (replace with your actual config)
   FIREBASE_API_KEY=
   FIREBASE_AUTH_DOMAIN=
   FIREBASE_STORAGE_BUCKET=
   FIREBASE_MESSAGING_SENDER_ID=
   FIREBASE_APP_ID=
   ```

Without these variables, users won't be able to register or login.

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