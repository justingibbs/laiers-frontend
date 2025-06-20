#!/bin/bash

# Quick deployment commands for Job Matching App
# Simplified version of deploy.sh for common operations

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-""}
REGION=${GOOGLE_CLOUD_LOCATION:-"us-central1"}
SERVICE_NAME="job-matching-app"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ GOOGLE_CLOUD_PROJECT not set"
    echo "Please set your project ID: export GOOGLE_CLOUD_PROJECT=your-project-id"
    exit 1
fi

# Validate that PROJECT_ID is not a number (project number)
if [[ "$PROJECT_ID" =~ ^[0-9]+$ ]]; then
    echo "❌ GOOGLE_CLOUD_PROJECT appears to be a project number ($PROJECT_ID)"
    echo "Please use the project ID instead. Run: gcloud projects list"
    echo "Then set: export GOOGLE_CLOUD_PROJECT=your-project-id"
    exit 1
fi

case "${1:-help}" in
    "deploy")
        echo "🚀 Deploying in maintenance mode..."
        gcloud run deploy "$SERVICE_NAME" \
            --source . \
            --region "$REGION" \
            --set-env-vars="MAINTENANCE_MODE=true,ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GOOGLE_GENAI_USE_VERTEXAI=true" \
            --allow-unauthenticated \
            --memory=1Gi \
            --max-instances=10 \
            --port=8080
        echo "✅ Deployment complete - App is in maintenance mode"
        ;;
    "live")
        echo "🌟 Making app live..."
        gcloud run services update "$SERVICE_NAME" \
            --region "$REGION" \
            --set-env-vars="MAINTENANCE_MODE=false,ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GOOGLE_GENAI_USE_VERTEXAI=true"
        echo "✅ App is now live!"
        ;;
    "maintenance")
        echo "🔧 Enabling maintenance mode..."
        gcloud run services update "$SERVICE_NAME" \
            --region "$REGION" \
            --set-env-vars="MAINTENANCE_MODE=true,ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GOOGLE_GENAI_USE_VERTEXAI=true"
        echo "✅ Maintenance mode enabled"
        ;;
    "url")
        gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)"
        ;;
    "logs")
        gcloud run services logs read "$SERVICE_NAME" --region="$REGION" --limit=20
        ;;
    *)
        echo "Job Matching App - Quick Deploy"
        echo ""
        echo "Commands:"
        echo "  deploy      Deploy in maintenance mode"
        echo "  live        Make app live (disable maintenance)"
        echo "  maintenance Enable maintenance mode"
        echo "  url         Show service URL"
        echo "  logs        Show recent logs"
        echo ""
        echo "Usage: $0 [command]"
        ;;
esac 