#!/bin/bash

# Job Matching App - Cloud Run Deployment Script
# This script handles deployment with maintenance mode support

set -e  # Exit on any error

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-""}
REGION=${GOOGLE_CLOUD_LOCATION:-"us-central1"}
SERVICE_NAME="job-matching-app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found. Please install Google Cloud SDK."
        exit 1
    fi
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        log_error "Not authenticated with gcloud. Run: gcloud auth login"
        exit 1
    fi
    
    # Check project ID
    if [ -z "$PROJECT_ID" ]; then
        log_error "GOOGLE_CLOUD_PROJECT not set. Please set it in your environment or .env file."
        exit 1
    fi
    
    # Set project
    gcloud config set project "$PROJECT_ID"
    
    log_success "Prerequisites check completed"
}

# Enable required APIs
enable_apis() {
    log_info "Enabling required Google Cloud APIs..."
    
    gcloud services enable run.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable artifactregistry.googleapis.com
    gcloud services enable aiplatform.googleapis.com
    gcloud services enable vertexai.googleapis.com
    
    log_success "APIs enabled"
}

# Deploy function
deploy_service() {
    local maintenance_mode=${1:-"true"}
    
    log_info "Deploying to Cloud Run..."
    log_info "Service: $SERVICE_NAME"
    log_info "Project: $PROJECT_ID"
    log_info "Region: $REGION"
    log_info "Maintenance Mode: $maintenance_mode"
    
    # Set environment variables
    ENV_VARS="ENVIRONMENT=production"
    ENV_VARS="$ENV_VARS,GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
    ENV_VARS="$ENV_VARS,GOOGLE_CLOUD_LOCATION=$REGION"
    ENV_VARS="$ENV_VARS,GOOGLE_GENAI_USE_VERTEXAI=true"
    ENV_VARS="$ENV_VARS,MAINTENANCE_MODE=$maintenance_mode"
    
    # Deploy with gcloud run deploy
    gcloud run deploy "$SERVICE_NAME" \
        --source . \
        --region "$REGION" \
        --platform managed \
        --allow-unauthenticated \
        --set-env-vars="$ENV_VARS" \
        --memory=1Gi \
        --cpu=1 \
        --timeout=300 \
        --max-instances=10 \
        --min-instances=0 \
        --port=8080
    
    log_success "Deployment completed"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
    log_success "Service URL: $SERVICE_URL"
    
    # Health check
    log_info "Performing health check..."
    if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_warning "Health check failed - service may still be starting up"
    fi
}

# Toggle maintenance mode
toggle_maintenance() {
    local mode=$1
    
    if [ "$mode" != "true" ] && [ "$mode" != "false" ]; then
        log_error "Invalid maintenance mode. Use 'true' or 'false'"
        exit 1
    fi
    
    log_info "Setting maintenance mode to: $mode"
    
    gcloud run services update "$SERVICE_NAME" \
        --region "$REGION" \
        --set-env-vars="MAINTENANCE_MODE=$mode,ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GOOGLE_GENAI_USE_VERTEXAI=true"
    
    log_success "Maintenance mode updated to: $mode"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
    log_info "Service URL: $SERVICE_URL"
}

# Show service status
show_status() {
    log_info "Service Status:"
    gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="table(
        metadata.name,
        status.url,
        status.conditions[0].type,
        status.conditions[0].status,
        spec.template.spec.containers[0].env[?(@.name=='MAINTENANCE_MODE')].value
    )"
}

# Show logs
show_logs() {
    log_info "Recent logs:"
    gcloud run services logs read "$SERVICE_NAME" --region="$REGION" --limit=50
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        check_prerequisites
        enable_apis
        deploy_service "${2:-true}"
        ;;
    "deploy-live")
        check_prerequisites
        enable_apis
        deploy_service "false"
        ;;
    "maintenance-on")
        toggle_maintenance "true"
        ;;
    "maintenance-off")
        toggle_maintenance "false"
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "help"|*)
        echo -e "${BLUE}Job Matching App - Cloud Run Deployment${NC}"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  deploy          Deploy in maintenance mode (default)"
        echo "  deploy-live     Deploy with app live (maintenance off)"
        echo "  maintenance-on  Enable maintenance mode"
        echo "  maintenance-off Disable maintenance mode"
        echo "  status          Show service status"
        echo "  logs            Show recent logs"
        echo "  help            Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 deploy                 # Deploy in maintenance mode"
        echo "  $0 maintenance-off        # Make app live"
        echo "  $0 maintenance-on         # Put app in maintenance mode"
        echo "  $0 status                 # Check service status"
        echo ""
        echo "Environment variables:"
        echo "  GOOGLE_CLOUD_PROJECT      Google Cloud project ID"
        echo "  GOOGLE_CLOUD_LOCATION     Deployment region (default: us-central1)"
        ;;
esac 