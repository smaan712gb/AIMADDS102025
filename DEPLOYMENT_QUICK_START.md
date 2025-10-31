# 🚀 Quick Start: Deploy to Google Cloud

## Overview
This guide will help you deploy the M&A Diligence Swarm to Google Cloud in under 30 minutes.

## What You'll Get
✅ Multi-user authentication system  
✅ PostgreSQL database (Cloud SQL)  
✅ Auto-scaling backend (Cloud Run)  
✅ Static frontend (Cloud Storage + CDN)  
✅ HTTPS/SSL enabled  
✅ Production-ready architecture  

## Prerequisites

### 1. Install Google Cloud SDK
```bash
# Download from: https://cloud.google.com/sdk/docs/install
# Or on Windows: https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe

# After installation, authenticate:
gcloud auth login
gcloud auth application-default login
```

### 2. Enable Billing
- Go to: https://console.cloud.google.com/billing
- Link your billing account to your project
- **Note**: Free tier covers most initial usage (~$300 credit for new users)

### 3. Prepare API Keys
You'll need these API keys ready:
- **Anthropic API Key** (Claude): https://console.anthropic.com/
- **Google API Key** (Gemini): https://makersuite.google.com/app/apikey
- **FMP API Key** (Financial data): https://site.financialmodelingprep.com/developer/docs

## Deployment Steps

### Option 1: Automated Deployment (Recommended)

```bash
# Clone or navigate to your project directory
cd AIMADDS102025

# Run the deployment script
bash scripts/deploy_to_gcloud.sh
```

The script will prompt you for:
1. **Project ID** (default: `aimadds-production`)
2. **Region** (default: `us-central1`)
3. **Domain name** (optional, can skip for now)
4. **Database passwords** (create strong passwords!)
5. **API keys** (prepared above)

**Estimated time**: 15-20 minutes

### Option 2: Manual Deployment

Follow the detailed guide in `GOOGLE_CLOUD_DEPLOYMENT_GUIDE.md`

## What Happens During Deployment

The script will:
1. ✅ Create GCP project and enable required APIs
2. ✅ Set up Cloud SQL PostgreSQL database
3. ✅ Store secrets in Secret Manager
4. ✅ Create Cloud Storage buckets
5. ✅ Build and deploy backend Docker container
6. ✅ Build and deploy frontend static files
7. ✅ Initialize database schema
8. ✅ Create default admin user

## After Deployment

### 1. Access Your Application

You'll receive two URLs:
```
Backend URL:  https://aimadds-backend-xxxxx.run.app
Frontend URL: https://storage.googleapis.com/aimadds-production-frontend/index.html
```

### 2. Login with Admin Credentials

```
Email:    smaan2011@gmail.com
Password: admin123
```

⚠️ **IMPORTANT**: Change this password immediately after first login!

### 3. Add Users

As an admin, you can:
1. Go to Settings → Users
2. Click "Add User"
3. Enter email and temporary password
4. Share credentials with team members

### 4. Run Your First Analysis

1. Click "New Analysis"
2. Enter:
   - **Project Name**: Test Deal
   - **Target Ticker**: NVDA (or any public company)
   - **Deal Type**: Acquisition
3. Click "Start Analysis"
4. Watch real-time progress!

## Domain Setup (Optional)

### Using Google Domains

1. **Purchase Domain**
   - Go to: https://domains.google.com
   - Search and purchase your domain (e.g., `aimadds.com`)
   - Cost: ~$12/year

2. **Configure DNS**
   ```bash
   # Create DNS zone
   gcloud dns managed-zones create aimadds-zone \
     --dns-name=yourdomain.com \
     --description="AIMADDS Production"
   
   # Get nameservers
   gcloud dns managed-zones describe aimadds-zone \
     --format="value(nameServers)"
   ```

3. **Map to Cloud Run**
   - Go to: https://console.cloud.google.com/run
   - Select `aimadds-backend` service
   - Click "Manage Custom Domains"
   - Add your domain and follow verification steps

4. **Map to Frontend**
   - Follow guide: https://cloud.google.com/storage/docs/hosting-static-website#custom-domain

## Monitoring & Maintenance

### View Logs
```bash
# Backend logs (real-time)
gcloud run services logs read aimadds-backend --region=us-central1 --follow

# Check recent errors
gcloud run services logs read aimadds-backend --region=us-central1 --limit=50
```

### Monitor Costs
- Dashboard: https://console.cloud.google.com/billing
- Set up budget alerts to avoid surprises

### Database Management
```bash
# Connect to database
gcloud sql connect aimadds-db --user=aimadds_user

# Backup database
gcloud sql backups create --instance=aimadds-db

# List backups
gcloud sql backups list --instance=aimadds-db
```

### Update Deployment
```bash
# After making code changes, redeploy:
bash scripts/deploy_to_gcloud.sh
```

## Troubleshooting

### Backend Won't Start
```bash
# Check logs
gcloud run services logs read aimadds-backend --region=us-central1 --limit=50

# Check service status
gcloud run services describe aimadds-backend --region=us-central1

# Common issues:
# - API keys not configured: Check Secret Manager
# - Database connection: Verify Cloud SQL instance is running
# - Memory issues: Increase memory in Cloud Run settings
```

### Database Connection Failed
```bash
# Test connection
gcloud sql connect aimadds-db --user=aimadds_user

# Check instance status
gcloud sql instances list

# Restart instance if needed
gcloud sql instances restart aimadds-db
```

### Frontend Not Loading
```bash
# Check bucket contents
gsutil ls -r gs://aimadds-production-frontend

# Check public access
gsutil iam get gs://aimadds-production-frontend

# Redeploy frontend
cd frontend
npm run build
gsutil -m rsync -r -d dist gs://aimadds-production-frontend
```

## Cost Optimization

### Development Environment
- Use `db-f1-micro` tier (smallest, cheapest)
- Set Cloud Run min-instances to 0
- Delete old analyses to save storage

### Production Environment
- Upgrade to `db-g1-small` for better performance
- Set Cloud Run min-instances to 1 (faster response)
- Enable Cloud CDN for frontend
- Set up Cloud Armor for DDoS protection

### Estimated Monthly Costs

**Development** (light usage):
- Cloud Run: $5-10
- Cloud SQL: $10-25
- Cloud Storage: $1-2
- **Total**: ~$20-40/month

**Production** (moderate usage):
- Cloud Run: $20-50
- Cloud SQL: $50-100
- Cloud Storage: $5-10
- Load Balancer: $20
- **Total**: ~$100-180/month

**High Volume** (heavy usage):
- Cloud Run: $100-200
- Cloud SQL: $200-400
- Cloud Storage: $20-50
- Load Balancer: $20
- **Total**: ~$350-670/month

## Security Best Practices

1. ✅ **Change Default Password**: First thing after deployment!
2. ✅ **Enable 2FA**: For Google Cloud Console access
3. ✅ **Rotate Secrets**: Update API keys quarterly
4. ✅ **Monitor Access**: Review user activity logs
5. ✅ **Set Budget Alerts**: Prevent unexpected costs
6. ✅ **Regular Backups**: Database backed up daily
7. ✅ **HTTPS Only**: Already configured by Cloud Run

## Sharing with Clients

Once deployed, share this with clients
