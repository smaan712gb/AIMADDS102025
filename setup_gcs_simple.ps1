# Simple GCS Setup Script for AIMADDS102025

$GCLOUD = "C:\Users\smaan\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

Write-Host "============================================"
Write-Host "  GCS Setup for AIMADDS102025"
Write-Host "============================================"
Write-Host ""

# Check gcloud exists
if (-not (Test-Path $GCLOUD)) {
    Write-Host "ERROR: gcloud not found" -ForegroundColor Red
    exit 1
}

Write-Host "Found Google Cloud SDK" -ForegroundColor Green
Write-Host ""

# Get version
Write-Host "Checking gcloud version..."
& $GCLOUD version
Write-Host ""

# Check authentication
Write-Host "Checking authentication..."
& $GCLOUD auth list
Write-Host ""

# Prompt for inputs
$PROJECT_ID = Read-Host "Enter your GCP Project ID"
$BUCKET_NAME = Read-Host "Enter GCS bucket name (must be globally unique)"

Write-Host ""
Write-Host "Setting up project: $PROJECT_ID"
Write-Host ""

# Set project
& $GCLOUD config set project $PROJECT_ID

# Enable APIs
Write-Host "Enabling APIs..."
& $GCLOUD services enable storage.googleapis.com
& $GCLOUD services enable bigquery.googleapis.com
& $GCLOUD services enable aiplatform.googleapis.com

# Create bucket
Write-Host ""
Write-Host "Creating bucket: $BUCKET_NAME"
& $GCLOUD storage buckets create "gs://$BUCKET_NAME" --location=US --uniform-bucket-level-access

# Create service account
Write-Host ""
Write-Host "Creating service account..."
$SA_EMAIL = "aimadds-sa@$PROJECT_ID.iam.gserviceaccount.com"
& $GCLOUD iam service-accounts create aimadds-sa --display-name="AIMADDS SA"

# Grant permissions
Write-Host "Granting permissions..."
& $GCLOUD projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/storage.admin"
& $GCLOUD projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/bigquery.admin"

# Create key
Write-Host ""
Write-Host "Creating service account key..."
& $GCLOUD iam service-accounts keys create aimadds-key.json --iam-account=$SA_EMAIL

# Update .env
Write-Host ""
Write-Host "Updating .env file..."
if (Test-Path ".env") {
    $env_content = Get-Content ".env" -Raw
    
    if ($env_content -match "GOOGLE_CLOUD_PROJECT=") {
        $env_content = $env_content -replace "GOOGLE_CLOUD_PROJECT=.*", "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
    } else {
        $env_content += "`nGOOGLE_CLOUD_PROJECT=$PROJECT_ID"
    }
    
    if ($env_content -match "GOOGLE_APPLICATION_CREDENTIALS=") {
        $env_content = $env_content -replace "GOOGLE_APPLICATION_CREDENTIALS=.*", "GOOGLE_APPLICATION_CREDENTIALS=./aimadds-key.json"
    } else {
        $env_content += "`nGOOGLE_APPLICATION_CREDENTIALS=./aimadds-key.json"
    }
    
    if ($env_content -match "GCS_BUCKET_NAME=") {
        $env_content = $env_content -replace "GCS_BUCKET_NAME=.*", "GCS_BUCKET_NAME=$BUCKET_NAME"
    } else {
        $env_content += "`nGCS_BUCKET_NAME=$BUCKET_NAME"
    }
    
    $env_content | Set-Content ".env"
    Write-Host "Updated .env file" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================"
Write-Host "  Setup Complete!"
Write-Host "============================================"
Write-Host ""
Write-Host "Project: $PROJECT_ID"
Write-Host "Bucket: $BUCKET_NAME"
Write-Host "Service Account: $SA_EMAIL"
Write-Host "Key File: aimadds-key.json"
Write-Host ""
Write-Host "Next: Run 'python verify_setup.py' to test"
Write-Host ""
