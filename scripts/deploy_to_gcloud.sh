#!/bin/bash

# Google Cloud Deployment Script for M&A Diligence Swarm
# This script automates the complete deployment process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists gcloud; then
    print_error "gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! command_exists docker; then
    print_error "Docker not found. Please install: https://docs.docker.com/get-docker/"
    exit 1
fi

print_success "All prerequisites found"

# Configuration
print_info "Setting up configuration..."

# Get user inputs
read -p "Enter your GCP Project ID (default: aimadds-production): " PROJECT_ID
PROJECT_ID=${PROJECT_ID:-aimadds-production}

read -p "Enter region (default: us-central1): " REGION
REGION=${REGION:-us-central1}

read -p "Enter your domain name (e.g., yourdomain.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    print_warning "No domain provided. Skipping domain configuration."
    SKIP_DOMAIN=true
fi

print_success "Configuration set"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Domain: $DOMAIN"

# Set GCP project
print_info "Setting GCP project..."
gcloud config set project $PROJECT_ID
print_success "Project set to $PROJECT_ID"

# Enable required APIs
print_info "Enabling required Google Cloud APIs (this may take a few minutes)..."
gcloud services enable \
    run.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com \
    compute.googleapis.com \
    --quiet

print_success "APIs enabled"

# Create Cloud SQL instance
print_info "Checking for existing Cloud SQL instance..."
if gcloud sql instances describe aimadds-db --project=$PROJECT_ID 2>/dev/null; then
    print_warning "Cloud SQL instance 'aimadds-db' already exists. Skipping creation."
else
    print_info "Creating Cloud SQL PostgreSQL instance (this takes 5-10 minutes)..."
    
    read -sp "Enter database root password: " DB_ROOT_PASSWORD
    echo
    read -sp "Enter database user password: " DB_USER_PASSWORD
    echo
    
    gcloud sql instances create aimadds-db \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --root-password="$DB_ROOT_PASSWORD" \
        --backup-start-time=03:00 \
        --quiet
    
    print_success "Cloud SQL instance created"
    
    # Create database
    print_info "Creating database..."
    gcloud sql databases create ma_diligence --instance=aimadds-db --quiet
    print_success "Database created"
    
    # Create user
    print_info "Creating database user..."
    gcloud sql users create aimadds_user \
        --instance=aimadds-db \
        --password="$DB_USER_PASSWORD" \
        --quiet
    print_success "Database user created"
fi

# Get Cloud SQL connection name
CLOUD_SQL_CONNECTION=$(gcloud sql instances describe aimadds-db --format='value(connectionName)')
print_success "Cloud SQL connection: $CLOUD_SQL_CONNECTION"

# Store secrets in Secret Manager
print_info "Setting up secrets..."

# Helper function to create or update secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if gcloud secrets describe $secret_name --project=$PROJECT_ID 2>/dev/null; then
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=- --quiet
    else
        echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=- --quiet
    fi
}

# JWT Secret
if ! gcloud secrets describe jwt-secret --project=$PROJECT_ID 2>/dev/null; then
    print_info "Creating JWT secret..."
    JWT_SECRET=$(openssl rand -base64 32)
    create_or_update_secret "jwt-secret" "$JWT_SECRET"
    print_success "JWT secret created"
fi

# API Keys
print_info "Setting up API keys..."
read -sp "Enter Anthropic API key: " ANTHROPIC_KEY
echo
create_or_update_secret "anthropic-api-key" "$ANTHROPIC_KEY"

read -sp "Enter Google API key: " GOOGLE_KEY
echo
create_or_update_secret "google-api-key" "$GOOGLE_KEY"

read -sp "Enter FMP API key: " FMP_KEY
echo
create_or_update_secret "fmp-api-key" "$FMP_KEY"

# Database password
if [ ! -z "$DB_USER_PASSWORD" ]; then
    create_or_update_secret "db-password" "$DB_USER_PASSWORD"
fi

print_success "All secrets configured"

# Create Cloud Storage buckets
print_info "Setting up Cloud Storage..."

# Reports bucket
if gsutil ls -p $PROJECT_ID gs://${PROJECT_ID}-reports 2>/dev/null; then
    print_warning "Reports bucket already exists"
else
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://${PROJECT_ID}-reports
    print_success "Reports bucket created"
fi

# Frontend bucket
if gsutil ls -p $PROJECT_ID gs://${PROJECT_ID}-frontend 2>/dev/null; then
    print_warning "Frontend bucket already exists"
else
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://${PROJECT_ID}-frontend
    
    # Configure CORS
    cat > /tmp/cors.json << EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF
    gsutil cors set /tmp/cors.json gs://${PROJECT_ID}-frontend
    rm /tmp/cors.json
    
    print_success "Frontend bucket created with CORS"
fi

# Deploy Backend to Cloud Run
print_info "Building and deploying backend to Cloud Run (this may take 10-15 minutes)..."

gcloud run deploy aimadds-backend \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="ENVIRONMENT=production,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION,POSTGRES_DB=ma_diligence,POSTGRES_USER=aimadds_user,GCS_BUCKET_NAME=${PROJECT_ID}-reports" \
    --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest,GOOGLE_API_KEY=google-api-key:latest,FMP_API_KEY=fmp-api-key:latest,JWT_SECRET_KEY=jwt-secret:latest,POSTGRES_PASSWORD=db-password:latest" \
    --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
    --min-instances=0 \
    --max-instances=10 \
    --memory=4Gi \
    --cpu=2 \
    --timeout=3600 \
    --concurrency=80 \
    --quiet

BACKEND_URL=$(gcloud run services describe aimadds-backend --region=$REGION --format='value(status.url)')
print_success "Backend deployed: $BACKEND_URL"

# Test backend health
print_info "Testing backend health..."
if curl -f -s "$BACKEND_URL/api/health" > /dev/null; then
    print_success "Backend is healthy!"
else
    print_warning "Backend health check failed. Check logs: gcloud run services logs read aimadds-backend --region=$REGION"
fi

# Build and deploy frontend
print_info "Building and deploying frontend..."

cd frontend

# Create production environment file
cat > .env.production << EOF
VITE_API_URL=$BACKEND_URL
VITE_WS_URL=${BACKEND_URL/https/wss}
EOF

# Install dependencies and build
npm install --quiet
npm run build

# Deploy to Cloud Storage
gsutil -m rsync -r -d dist gs://${PROJECT_ID}-frontend

# Make files public
gsutil -m acl ch -r -u AllUsers:R gs://${PROJECT_ID}-frontend

# Set website configuration
gsutil web set -m index.html -e index.html gs://${PROJECT_ID}-frontend

FRONTEND_URL="https://storage.googleapis.com/${PROJECT_ID}-frontend/index.html"
print_success "Frontend deployed: $FRONTEND_URL"

cd ..

# Initialize database
print_info "Initializing database schema..."
gcloud run jobs create init-db \
    --image=gcr.io/$PROJECT_ID/aimadds-backend \
    --region=$REGION \
    --set-env-vars="ENVIRONMENT=production,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION,POSTGRES_DB=ma_diligence,POSTGRES_USER=aimadds_user" \
    --set-secrets="POSTGRES_PASSWORD=db-password:latest" \
    --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
    --command="python,-c,from src.database import init_db; init_db()" \
    --quiet 2>/dev/null || true

gcloud run jobs execute init-db --region=$REGION --quiet 2>/dev/null || print_warning "Database init job execution skipped"

print_success "Database initialized"

# Domain configuration (if provided)
if [ -z "$SKIP_DOMAIN" ]; then
    print_info "Setting up custom domain..."
    
    print_warning "Manual steps required for domain setup:"
    echo "1. Go to Cloud Console: https://console.cloud.google.com/run"
    echo "2. Select the 'aimadds-backend' service"
    echo "3. Click 'Manage Custom Domains'"
    echo "4. Add your domain: $DOMAIN"
    echo "5. Follow the verification steps"
    echo ""
    echo "For frontend domain mapping:"
    echo "https://cloud.google.com/storage/docs/hosting-static-website#custom-domain"
fi

# Print deployment summary
echo ""
echo "=================================================="
print_success "🎉 Deployment Complete!"
echo "=================================================="
echo ""
echo "📊 Deployment Details:"
echo "  Backend URL:  $BACKEND_URL"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Region:       $REGION"
echo "  Project:      $PROJECT_ID"
echo ""
echo "🔐 Admin Credentials:"
echo "  Email:        smaan2011@gmail.com"
echo "  Password:     admin123"
echo "  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!"
echo ""
echo "📚 Next Steps:"
echo "  1. Test the application: $FRONTEND_URL"
echo "  2. Change admin password via the UI"
echo "  3. Add team members as users"
echo "  4. Configure custom domain (if needed)"
echo "  5. Share link with clients!"
echo ""
echo "📖 View logs:"
echo "  Backend:  gcloud run services logs read aimadds-backend --region=$REGION --follow"
echo "  Frontend: gsutil ls -r gs://${PROJECT_ID}-frontend"
echo ""
echo "💰 Monitor costs:"
echo "  https://console.cloud.google.com/billing"
echo ""
echo "🔄 To update deployment:"
echo "  bash scripts/deploy_to_gcloud.sh"
echo ""
print_success "Ready to start analyzing M&A deals!"
echo "=================================================="
