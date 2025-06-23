# Job Matching App - Cloud Run Deployment Guide

This guide covers deploying your FastAPI + Google ADK application to Google Cloud Run with maintenance mode support.

Cloud URL:
https://your-app-url.us-central1.run.app/

## 🚀 Quick Start

### Prerequisites
1. **Google Cloud SDK installed and authenticated**
   ```bash
   # Install gcloud (macOS)
   brew install google-cloud-sdk
   
   # Authenticate
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Environment Variables Set**
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export GOOGLE_CLOUD_LOCATION=us-central1
   ```

3. **Required APIs Enabled** (done automatically by deployment script)
   - Cloud Run API
   - Cloud Build API  
   - Vertex AI API
   - AI Platform API
   - Secret Manager API (for secure configuration)

## 🎯 **The Two Commands You Need**

### **For Development/Testing (Safe Deployment):**
```bash
./deployment/quick-deploy.sh deploy
```
- Deploys your app in **maintenance mode**
- Users see a professional "Coming Soon" page
- You can test functionality safely
- Health checks work for monitoring

### **For Going Live (Production):**
```bash
./deployment/quick-deploy.sh live
```
- Makes your app **live** for real users
- Switches from maintenance mode to normal operation
- Instant toggle - no rebuild required

## ⚡ **Complete Workflow Example**

```bash
# Step 1: Deploy safely (maintenance mode)
./deployment/quick-deploy.sh deploy

# Step 2: Test your deployment
curl "$(./deployment/quick-deploy.sh url)/health"

# Step 3: Make it live when ready
./deployment/quick-deploy.sh live

# Later: Put back in maintenance for updates
./deployment/quick-deploy.sh maintenance
```

## 📋 **All Available Commands**

```bash
# Deployment
./deployment/quick-deploy.sh deploy      # Deploy in maintenance mode
./deployment/quick-deploy.sh live        # Make app live
./deployment/quick-deploy.sh maintenance # Back to maintenance mode

# Information  
./deployment/quick-deploy.sh url         # Get service URL
./deployment/quick-deploy.sh logs        # View recent logs

# Help
./deployment/quick-deploy.sh             # Show help
```

## 📋 Deployment Files Overview

```
deployment/
├── deploy.sh          # Full-featured deployment script
├── quick-deploy.sh    # Quick commands for common operations  
├── README.md          # This documentation
└── cloudbuild.yaml    # Cloud Build configuration (optional)

# Root files
├── Dockerfile         # Container configuration
├── .dockerignore      # Files to exclude from build
└── .env.example       # Environment variables template
```

## 🔧 Deployment Scripts

### Full Deployment Script (`deploy.sh`)

Comprehensive script with all features:

```bash
# Deploy in maintenance mode
./deployment/deploy.sh deploy

# Deploy live immediately  
./deployment/deploy.sh deploy-live

# Toggle maintenance mode
./deployment/deploy.sh maintenance-on
./deployment/deploy.sh maintenance-off

# Check status and logs
./deployment/deploy.sh status
./deployment/deploy.sh logs
```

### Quick Deploy Script (`quick-deploy.sh`)

Simplified commands for common operations:

```bash
# Deploy (maintenance mode)
./deployment/quick-deploy.sh deploy

# Make live
./deployment/quick-deploy.sh live

# Back to maintenance
./deployment/quick-deploy.sh maintenance

# Get URL and logs
./deployment/quick-deploy.sh url
./deployment/quick-deploy.sh logs
```

## 🛠️ Manual Deployment Commands

If you prefer manual control:

### Initial Deployment
```bash
gcloud run deploy job-matching-app \
  --source . \
  --region us-central1 \
  --set-env-vars="MAINTENANCE_MODE=true,ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=your-project-id,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=true,PORT=8080,FIREBASE_API_KEY=your-firebase-api-key,FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com,FIREBASE_STORAGE_BUCKET=your-project-id.firebasestorage.app,FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id,FIREBASE_APP_ID=your-firebase-app-id" \
  --allow-unauthenticated \
  --memory=1Gi \
  --max-instances=10
```

**🔐 Enhanced Security: Secret Manager Integration**

The application now uses **Google Cloud Secret Manager** for secure configuration management in production. This provides enhanced security and eliminates the need for sensitive environment variables.

**Production (Recommended - Secret Manager):**
- Firebase configuration stored securely in Secret Manager
- No sensitive data in environment variables or container images
- Easy API key rotation without redeployment
- Enhanced security with IAM access controls

**Legacy (Environment Variables):**
If using environment variables instead of Secret Manager, get these values from:
1. Firebase Console → Project Settings → General → Your Apps
2. Copy the config object values to environment variables
3. These values are safe to use as environment variables (they're public client config)

### Toggle Maintenance Mode
```bash
# Enable maintenance mode
gcloud run services update job-matching-app \
  --region us-central1 \
  --set-env-vars="MAINTENANCE_MODE=true"

# Disable maintenance mode (make live)
gcloud run services update job-matching-app \
  --region us-central1 \
  --set-env-vars="MAINTENANCE_MODE=false"
```

## 🔒 Firebase Credentials Setup

### For Development
1. Download Firebase service account key
2. Place in `config/firebase-credentials.json`
3. Set `FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json`

### For Production (Cloud Run)
**Option 1: Service Account (Recommended)**
```bash
# Create service account
gcloud iam service-accounts create job-matching-app-sa

# Grant permissions
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:job-matching-app-sa@your-project-id.iam.gserviceaccount.com" \
  --role="roles/firebase.admin"

# Deploy with service account
gcloud run deploy job-matching-app \
  --service-account=job-matching-app-sa@your-project-id.iam.gserviceaccount.com \
  # ... other options
```

**Option 2: Application Default Credentials**
If your Cloud Run service runs in the same project as Firebase, it will automatically use the default compute service account.

## 🔐 Secret Manager Setup (Recommended)

### Setting Up Secure Configuration

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

# Or create a complete config as JSON (alternative)
echo '{"apiKey":"YOUR_API_KEY","authDomain":"..."}' | gcloud secrets create firebase-web-config --data-file=-
```

**3. Grant Cloud Run Access to Secrets:**
```bash
# Get your project number and service account
PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")
SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

# Grant secret access to Cloud Run
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"
```

**4. Deploy with Secret Manager:**
```bash
# Deploy with minimal environment variables (secrets loaded automatically)
gcloud run deploy job-matching-app \
    --source . \
    --region us-central1 \
    --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,MAINTENANCE_MODE=true"
```

**5. Test Secret Manager Integration:**
```bash
# Verify secrets are loading correctly
curl "$(./deployment/quick-deploy.sh url)/debug/secrets"

# Expected response: {"status": "ok", "secret_manager_available": true, ...}
```

### API Key Rotation with Secret Manager

With Secret Manager, rotating API keys is simple and secure:

```bash
# Update the secret with new API key
echo "NEW_FIREBASE_API_KEY" | gcloud secrets versions add firebase-api-key --data-file=-

# The change takes effect immediately - no redeployment needed!
# Cloud Run automatically picks up the latest secret version
```

## 🌍 Environment Variables

### Required for Cloud Run (with Secret Manager)
```bash
ENVIRONMENT=production
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true
PORT=8080
MAINTENANCE_MODE=false

# Note: Firebase configuration is now loaded from Secret Manager
# No need to set Firebase environment variables in production
```

### Legacy (Environment Variables)
```bash
# Only needed if not using Secret Manager
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
FIREBASE_STORAGE_BUCKET=your-project-id.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id
FIREBASE_APP_ID=your-firebase-app-id
```

### Optional
```bash
ADK_BUCKET_NAME=your-bucket-name
FIREBASE_CREDENTIALS_PATH=/path/to/credentials.json
```

## 🎯 Maintenance Mode

The maintenance mode feature allows safe deployments:

### How It Works
- `MAINTENANCE_MODE=true`: Shows "Coming Soon" page to all users
- `MAINTENANCE_MODE=false`: Normal application operation
- Health check endpoints (`/health`, `/_ah/health`) always work

### Benefits
- Deploy safely without downtime concerns
- Test deployments before going live
- Quick rollback by enabling maintenance mode
- Cost-effective (no need for separate staging environment)

### Maintenance Page
Users see a beautiful "Coming Soon" page with:
- Gradient background
- Professional messaging
- Status indicator
- Mobile-responsive design

## 📊 Monitoring & Debugging

### Health Checks
- **Primary**: `https://your-service-url/health`
- **Cloud Run**: `https://your-service-url/_ah/health`
- **Alternative**: `https://your-service-url/api/health`

### Service Status
```bash
gcloud run services describe job-matching-app --region us-central1
```

### Logs
```bash
# Recent logs
gcloud run services logs read job-matching-app --region us-central1

# Follow logs
gcloud run services logs tail job-matching-app --region us-central1
```

### Service URL
```bash
gcloud run services describe job-matching-app \
  --region us-central1 \
  --format="value(status.url)"
```

## 💰 Cost Optimization

### Cloud Run Pricing Benefits
- **Pay-per-request**: No traffic = no cost
- **Auto-scaling to zero**: Scales down when idle
- **Free tier**: 2M requests/month included
- **Memory optimization**: 1Gi memory allocated

### Configuration
```bash
--memory=1Gi           # Sufficient for FastAPI + ADK
--cpu=1                # 1 vCPU
--max-instances=10     # Prevent runaway scaling
--min-instances=0      # Scale to zero when idle
--timeout=300          # 5-minute request timeout
```

## 🔧 Troubleshooting

### Common Issues

**1. Vertex AI Permission Denied**
```bash
# Enable APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable vertexai.googleapis.com

# Wait 2-3 minutes after enabling
```

**2. Firebase Connection Issues**
- **Backend (Admin SDK)**: Verify `GOOGLE_CLOUD_PROJECT` matches Firebase project
- **Frontend (Authentication)**: Ensure Firebase environment variables are set correctly
- **Missing Config**: Check if Firebase web config is empty `{}` in browser dev tools
- **Environment Variables**: Verify all 5 Firebase env vars are set in Cloud Run
- Check service account permissions
- Ensure Firebase Admin SDK is properly initialized

**Test Firebase Config Loading:**
```bash
# Check if Firebase config is loading in production
curl -s "$(./deployment/quick-deploy.sh url)/login" | grep -A10 "firebase-config"

# Should show populated config, not empty {}

# Test Secret Manager specifically
curl -s "$(./deployment/quick-deploy.sh url)/debug/secrets"

# Should show: {"status": "ok", "secret_manager_available": true, ...}
```

**5. Secret Manager Issues (NEW)**
```bash
# Enable Secret Manager API if not enabled
gcloud services enable secretmanager.googleapis.com

# Verify secrets exist
gcloud secrets list | grep firebase

# Grant proper permissions to Cloud Run service account
PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Test secret access
gcloud secrets versions access latest --secret="firebase-api-key"
```

**3. Container Build Failures**
- Check `Dockerfile` syntax
- Verify UV dependencies in `pyproject.toml`
- Review `.dockerignore` exclusions

**4. Health Check Failures**
- Service may still be starting (wait 30-60 seconds)
- Check logs for startup errors
- Verify port 8080 is properly exposed

### Debug Commands
```bash
# Check service details
./deployment/deploy.sh status

# View recent logs
./deployment/deploy.sh logs

# Test health endpoint
curl -f "$(./deployment/quick-deploy.sh url)/health"
```

## 🚦 Deployment Workflow

### Recommended Process
1. **Deploy in maintenance mode** → Safe deployment
2. **Test the service** → Verify functionality  
3. **Make live** → Toggle off maintenance mode
4. **Monitor** → Check logs and metrics

### Example Session
```bash
# Step 1: Deploy safely
./deployment/quick-deploy.sh deploy

# Step 2: Test
curl "$(./deployment/quick-deploy.sh url)/health"

# Step 3: Go live
./deployment/quick-deploy.sh live

# Step 4: Monitor
./deployment/quick-deploy.sh logs
```

## 📝 Next Steps

After successful deployment:

1. **Set up custom domain** (optional)
2. **Configure CDN** for static assets (optional)
3. **Set up monitoring alerts**
4. **Implement CI/CD pipeline** with Cloud Build
5. **Configure backup strategies** for Firestore

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Cloud Run logs: `./deployment/deploy.sh logs`
3. Verify environment variables are set correctly
4. Ensure all required APIs are enabled
5. Check service account permissions for Firebase/Vertex AI

---

**Ready to deploy?** Start with `./deployment/quick-deploy.sh deploy` 🚀 