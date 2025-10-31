# Google Cloud Production Deployment Guide

## Overview
This guide will help you deploy the M&A Diligence Swarm to Google Cloud Platform with:
- ✅ Multi-user authentication with Cloud SQL (PostgreSQL)
- ✅ Auto-scaling with Cloud Run
- ✅ Custom domain name with HTTPS/SSL
- ✅ Secure secret management
- ✅ Real-time WebSocket support
- ✅ CDN for frontend static assets

## Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Custom Domain (HTTPS)                     │
│              yourdomain.com / aimadds.com                    │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
    ┌─────▼─────┐              ┌────────▼────────┐
    │  Frontend │              │  Backend API    │
    │ (Storage  │              │  (Cloud Run)    │
    │  + CDN)   │              │  FastAPI Server │
    └───────────┘              └─────────┬───────┘
                                         │
                         ┌───────────────┴────────────────┐
                         │                                │
                  ┌──────▼──────┐              ┌─────────▼────────┐
                  │  Cloud SQL  │              │  Cloud Storage   │
                  │ (PostgreSQL)│              │  (Reports/Files) │
                  └─────────────┘              └──────────────────┘
```

## Prerequisites
1. Google Cloud account with billing enabled
2. `gcloud` CLI installed and authenticated
3. Domain name ready (can purchase through Google Domains)

## Cost Estimate
- **Cloud Run**: ~$20-50/month (with free tier)
- **Cloud SQL**: ~$25-100/month (depends on traffic)
- **Cloud Storage**: ~$1-5/month
- **Domain**: ~$12/year
- **Total**: ~$50-150/month depending on usage

## Phase 1: Project Setup

### 1. Set Project Variables
```bash
export PROJECT_ID="aimadds-production"
export REGION="us-central1"
export DOMAIN="yourdomain.com"  # Replace with your domain
```

### 2. Create and Configure GCP Project
```bash
# Create project
gcloud projects create $PROJECT_ID --name="AIMADDS Production"

# Set as active project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  compute.googleapis.com

# Link billing (required for Cloud Run)
# Note: You'll need to do this manually in console first time
```

## Phase 2: Database Setup (Cloud SQL PostgreSQL)

### 1. Create Cloud SQL Instance
```bash
# Create PostgreSQL instance
gcloud sql instances create aimadds-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --root-password="ChangeThisPassword123!" \
  --backup-start-time=03:00

# Create database
gcloud sql databases create ma_diligence --instance=aimadds-db

# Create user
gcloud sql users create aimadds_user \
  --instance=aimadds-db \
  --password="ChangeThisPassword456!"
```

### 2. Store Database Credentials in Secret Manager
```bash
# Store database password
echo -n "ChangeThisPassword456!" | gcloud secrets create db-password --data-file=-

# Store JWT secret
openssl rand -base64 32 | gcloud secrets create jwt-secret --data-file=-

# Store API keys (you'll need to set these)
echo -n "your-anthropic-key" | gcloud secrets create anthropic-api-key --data-file=-
echo -n "your-google-key" | gcloud secrets create google-api-key --data-file=-
echo -n "your-fmp-key" | gcloud secrets create fmp-api-key --data-file=-
```

## Phase 3: Storage Setup

### 1. Create Cloud Storage Buckets
```bash
# Create bucket for reports
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://${PROJECT_ID}-reports

# Create bucket for frontend
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://${PROJECT_ID}-frontend

# Enable CORS for frontend bucket
cat > cors.json << EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://${PROJECT_ID}-frontend
```

## Phase 4: Backend Deployment

### 1. Build and Deploy Backend to Cloud Run
```bash
# Deploy backend
gcloud run deploy aimadds-backend \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=production" \
  --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest,GOOGLE_API_KEY=google-api-key:latest,FMP_API_KEY=fmp-api-key:latest,JWT_SECRET_KEY=jwt-secret:latest,DB_PASSWORD=db-password:latest" \
  --min-instances=1 \
  --max-instances=10 \
  --memory=2Gi \
  --cpu=2 \
  --timeout=3600 \
  --concurrency=80
```

### 2. Get Backend URL
```bash
export BACKEND_URL=$(gcloud run services describe aimadds-backend --region=$REGION --format='value(status.url)')
echo "Backend URL: $BACKEND_URL"
```

## Phase 5: Frontend Deployment

### 1. Build Frontend with Backend URL
```bash
cd frontend

# Update .env.production
cat > .env.production << EOF
VITE_API_URL=$BACKEND_URL
VITE_WS_URL=${BACKEND_URL/https/wss}
EOF

# Build frontend
npm install
npm run build

# Deploy to Cloud Storage
gsutil -m rsync -r -d dist gs://${PROJECT_ID}-frontend

# Make files public
gsutil -m acl ch -r -u AllUsers:R gs://${PROJECT_ID}-frontend

# Set default page
gsutil web set -m index.html -e index.html gs://${PROJECT_ID}-frontend
```

### 2. Get Frontend URL
```bash
echo "Frontend URL: https://storage.googleapis.com/${PROJECT_ID}-frontend/index.html"
```

## Phase 6: Domain Configuration

### 1. Purchase Domain (if needed)
- Go to https://domains.google.com
- Purchase your desired domain
- Or use existing domain and update nameservers to Google Cloud DNS

### 2. Configure Cloud DNS
```bash
# Create DNS zone
gcloud dns managed-zones create aimadds-zone \
  --description="AIMADDS Production Zone" \
  --dns-name=$DOMAIN

# Get nameservers and update domain registrar
gcloud dns managed-zones describe aimadds-zone --format="value(nameServers)"
```

### 3. Create DNS Records
```bash
# Get Load Balancer IP (we'll create this next)
export LB_IP=$(gcloud compute addresses describe aimadds-ip --global --format="value(address)")

# Create A record for domain
gcloud dns record-sets transaction start --zone=aimadds-zone
gcloud dns record-sets transaction add $LB_IP \
  --name=$DOMAIN. \
  --ttl=300 \
  --type=A \
  --zone=aimadds-zone
gcloud dns record-sets transaction execute --zone=aimadds-zone

# Create A record for www subdomain
gcloud dns record-sets transaction start --zone=aimadds-zone
gcloud dns record-sets transaction add $LB_IP \
  --name=www.$DOMAIN. \
  --ttl=300 \
  --type=A \
  --zone=aimadds-zone
gcloud dns record-sets transaction execute --zone=aimadds-zone
```

### 4. Set Up Load Balancer with SSL
```bash
# Reserve static IP
gcloud compute addresses create aimadds-ip \
  --ip-version=IPV4 \
  --global

# Create backend bucket for frontend
gcloud compute backend-buckets create aimadds-frontend-bucket \
  --gcs-bucket-name=${PROJECT_ID}-frontend \
  --enable-cdn

# Create SSL certificate (managed by Google)
gcloud compute ssl-certificates create aimadds-cert \
  --domains=$DOMAIN,www.$DOMAIN \
  --global

# Create URL map
gcloud compute url-maps create aimadds-lb \
  --default-backend-bucket=aimadds-frontend-bucket

# Add backend service to URL map
gcloud compute url-maps add-path-matcher aimadds-lb \
  --path-matcher-name=api-matcher \
  --default-backend-bucket=aimadds-frontend-bucket \
  --backend-service-path-rules="/api/*=aimadds-backend"

# Create HTTPS proxy
gcloud compute target-https-proxies create aimadds-https-proxy \
  --url-map=aimadds-lb \
  --ssl-certificates=aimadds-cert

# Create forwarding rule
gcloud compute forwarding-rules create aimadds-https-rule \
  --address=aimadds-ip \
  --global \
  --target-https-proxy=aimadds-https-proxy \
  --ports=443
```

## Phase 7: Database Migration

### 1. Initialize Database Schema
The database schema will be automatically created when you run the migration script.

### 2. Migrate Users (if you have existing users)
```bash
# Connect to Cloud SQL from local machine
gcloud sql connect aimadds-db --user=aimadds_user

# Or run migration from Cloud Shell
```

## Phase 8: Testing

### 1. Test Backend Health
```bash
curl $BACKEND_URL/api/health
```

### 2. Test Frontend Access
```bash
curl https://$DOMAIN
```

### 3. Test Authentication
```bash
# Register test user
curl -X POST https://$DOMAIN/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"smaan2011@gmail.com","password":"admin123"}'
```

## Phase 9: Security Hardening

### 1. Enable Cloud Armor (DDoS Protection)
```bash
# Create security policy
gcloud compute security-policies create aimadds-policy \
  --description="AIMADDS Security Policy"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy=aimadds-policy \
  --expression="true" \
  --action=rate-based-ban \
  --rate-limit-threshold-count=100 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600

# Attach to backend service
gcloud compute backend-services update aimadds-backend \
  --security-policy=aimadds-policy \
  --global
```

### 2. Enable VPC Connector for Cloud SQL
```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create aimadds-connector \
  --region=$REGION \
  --range=10.8.0.0/28

# Update Cloud Run to use connector
gcloud run services update aimadds-backend \
  --vpc-connector=aimadds-connector \
  --region=$REGION
```

## Phase 10: Monitoring & Logging

### 1. Set Up Uptime Checks
```bash
gcloud monitoring uptime-check-configs create aimadds-health-check \
  --display-name="AIMADDS Health Check" \
  --resource-type=uptime-url \
  --http-check-path=/api/health \
  --monitored-resource="https://$DOMAIN"
```

### 2. Set Up Alerts
```bash
# Create alert for downtime
gcloud alpha monitoring policies create \
  --notification-channels=your-email-channel \
  --display-name="AIMADDS Down Alert" \
  --condition-display-name="Uptime Check Failed" \
  --condition-threshold-value=1 \
  --condition-threshold-duration=60s
```

## Phase 11: Continuous Deployment (Optional)

### 1. Set Up Cloud Build
Create `.cloudbuild.yaml`:
```yaml
steps:
  # Build backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/aimadds-backend', '.']
  
  # Push backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/aimadds-backend']
  
  # Deploy backend
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'aimadds-backend'
      - '--image=gcr.io/$PROJECT_ID/aimadds-backend'
      - '--region=us-central1'
      - '--platform=managed'
  
  # Build frontend
  - name: 'gcr.io/cloud-builders/npm'
    dir: 'frontend'
    args: ['install']
  
  - name: 'gcr.io/cloud-builders/npm'
    dir: 'frontend'
    args: ['run', 'build']
  
  # Deploy frontend
  - name: 'gcr.io/cloud-builders/gsutil'
    args: ['-m', 'rsync', '-r', '-d', 'frontend/dist', 'gs://$PROJECT_ID-frontend']
```

## Maintenance

### Daily Tasks
- Monitor Cloud Logging for errors
- Check Cloud Monitoring dashboard
- Review cost reports

### Weekly Tasks
- Review security logs
- Check database performance
- Update dependencies

### Monthly Tasks
- Rotate secrets
- Review access logs
- Update SSL certificates (automatic with managed certs)

## Troubleshooting

### Backend Not Starting
```bash
# Check logs
gcloud run services logs read aimadds-backend --region=$REGION --limit=50

# Check service status
gcloud run services describe aimadds-backend --region=$REGION
```

### Database Connection Issues
```bash
# Test connection
gcloud sql connect aimadds-db --user=aimadds_user

# Check instances
gcloud sql instances list
```

### Frontend Not Loading
```bash
# Check bucket contents
gsutil ls -r gs://${PROJECT_ID}-frontend

# Check CORS settings
gsutil cors get gs://${PROJECT_ID}-frontend
```

## Next Steps

1. ✅ Complete all phases above
2. ✅ Test with multiple users
3. ✅ Share link with clients: `https://yourdomain.com`
4. ✅ Monitor usage and performance
5. ✅ Gather feedback and iterate

## Support

For issues during deployment:
1. Check Cloud Logging
2. Review documentation: https://cloud.google.com/run/docs
3. Contact support if needed

---

**Ready to deploy?** Run the automated deployment script:
```bash
bash scripts/deploy_to_gcloud.sh
