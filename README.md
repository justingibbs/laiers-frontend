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
    
    Can also use, but don't think this is proper anymore
    ```
    uv run main.py
    ```
    
    Then access the application at:
    ```
    http://localhost:8000
    ```
    
    Note: Use `http://` (not `https://`) for local development.

## Setup

1. Download your Firebase service account key from the Firebase Console
2. Save it as `firebase-credentials.json` in the project root
3. Copy `.env.example` to `.env` and fill in your values
