# laiers

## Project Purpose/Goal
An agent-powered job matching platform that revolutionizes hiring by identifying candidates with the essential soft skills needed to excel in GenAI-transformed workplaces. Rather than focusing on traditional hard skills that AI increasingly automates, the platform evaluates and matches based on uniquely human capabilities—creative problem-solving, emotional intelligence, adaptability, critical thinking, and collaborative leadership—that become more valuable as AI handles routine tasks. The platform connects Companies with Talent through AI-powered conversations and matching.

## Project Setup

This project uses [UV](https://github.com/astral-sh/uv) for dependency management.

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
- Error tracking

To view logs:
```bash
# Development mode (verbose logging)
ENVIRONMENT=development uv run -- uvicorn main:app --reload --port 8000

# Production mode (minimal logging)
ENVIRONMENT=production uv run -- uvicorn main:app --port 8000
```

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
