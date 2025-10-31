# PowerShell Script to Setup Google Cloud Storage for AIMADDS102025

$GCLOUD_PATH = "C:\Users\smaan\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  GCS Setup for AIMADDS102025" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if gcloud exists
if (-not (Test-Path $GCLOUD_PATH)) {
    Write-Host "ERROR: gcloud not found at $GCLOUD_PATH" -ForegroundColor Red
    Write-Host "Please verify Google Cloud SDK installation path" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Found Google Cloud SDK" -ForegroundColor Green
Write-Host ""

# Get gcloud version
Write-Host "Checking gcloud version..." -ForegroundColor Yellow
& $GCLOUD_PATH version
Write-Host ""

# Check if authenticated
Write-Host "Checking authentication..." -ForegroundColor Yellow
$auth = & $GCLOUD_PATH auth list 2>&1
Write-Host $auth
Write-Host ""

# Prompt for project ID
$PROJECT_ID = Read-Host "Enter your GCP Project ID (e.g., aimadds102025)"
if ([string]::IsNullOrWhiteSpace($PROJECT_ID)) {
    Write-Host "ERROR: Project ID is required" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setting up project: $PROJECT_ID" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Set project
Write-Host "Setting active project..." -ForegroundColor Yellow
& $GCLOUD_PATH config set project $PROJECT_ID
Write-Host ""

# Enable required APIs
Write-Host "Enabling required APIs..." -ForegroundColor Yellow
Write-Host "  - Cloud Storage API" -ForegroundColor Gray
& $GCLOUD_PATH services enable storage.googleapis.com

Write-Host "  - BigQuery API" -ForegroundColor Gray
& $GCLOUD_PATH services enable bigquery.googleapis.com

Write-Host "  - Vertex AI API" -ForegroundColor Gray
& $GCLOUD_PATH services enable aiplatform.googleapis.com

Write-Host ""
Write-Host "✓ APIs enabled successfully" -ForegroundColor Green
Write-Host ""

# Prompt for bucket name
$BUCKET_NAME = Read-Host "Enter GCS bucket name (must be globally unique, e.g., aimadds102025-docs)"
if ([string]::IsNullOrWhiteSpace($BUCKET_NAME)) {
    Write-Host "ERROR: Bucket name is required" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Creating GCS bucket: $BUCKET_NAME..." -ForegroundColor Yellow

# Create bucket
$createResult = & $GCLOUD_PATH storage buckets create gs://$BUCKET_NAME --location=US --uniform-bucket-level-access 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Bucket created successfully!" -ForegroundColor Green
} else {
    Write-Host "Bucket creation result: $createResult" -ForegroundColor Yellow
    if ($createResult -match "already exists") {
        Write-Host "Note: Bucket already exists, continuing..." -ForegroundColor Yellow
    }
}

Write-Host ""

# List buckets to verify
Write-Host "Listing your buckets..." -ForegroundColor Yellow
& $GCLOUD_PATH storage buckets list
Write-Host ""

# Create service account
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Creating Service Account" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$SA_NAME = "aimadds-sa"
$SA_EMAIL = "$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

Write-Host "Creating service account: $SA_NAME..." -ForegroundColor Yellow
$saResult = & $GCLOUD_PATH iam service-accounts create $SA_NAME --display-name="AIMADDS Service Account" --description="Service account for AI M&A Due Diligence System" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Service account created!" -ForegroundColor Green
} else {
    if ($saResult -match "already exists") {
        Write-Host "Note: Service account already exists, continuing..." -ForegroundColor Yellow
    } else {
        Write-Host "Service account creation result: $saResult" -ForegroundColor Yellow
    }
}

Write-Host ""

# Grant permissions
Write-Host "Granting permissions to service account..." -ForegroundColor Yellow

Write-Host "  - Storage Admin role" -ForegroundColor Gray
& $GCLOUD_PATH projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/storage.admin" | Out-Null

Write-Host "  - BigQuery Admin role" -ForegroundColor Gray
& $GCLOUD_PATH projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/bigquery.admin" | Out-Null

Write-Host "✓ Permissions granted" -ForegroundColor Green
Write-Host ""

# Create and download key
Write-Host "Creating service account key..." -ForegroundColor Yellow
$KEY_FILE = "aimadds-key.json"

& $GCLOUD_PATH iam service-accounts keys create $KEY_FILE --iam-account=$SA_EMAIL

if (Test-Path $KEY_FILE) {
    Write-Host "✓ Service account key created: $KEY_FILE" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to create service account key" -ForegroundColor Red
}

Write-Host ""

# Update .env file
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Updating .env File" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    
    # Update or add GCP settings
    if ($envContent -match "GOOGLE_CLOUD_PROJECT=") {
        $envContent = $envContent -replace "GOOGLE_CLOUD_PROJECT=.*", "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
    } else {
        $envContent += "`nGOOGLE_CLOUD_PROJECT=$PROJECT_ID"
    }
    
    if ($envContent -match "GOOGLE_APPLICATION_CREDENTIALS=") {
        $envContent = $envContent -replace "GOOGLE_APPLICATION_CREDENTIALS=.*", "GOOGLE_APPLICATION_CREDENTIALS=./$KEY_FILE"
    } else {
        $envContent += "`nGOOGLE_APPLICATION_CREDENTIALS=./$KEY_FILE"
    }
    
    if ($envContent -match "GCS_BUCKET_NAME=") {
        $envContent = $envContent -replace "GCS_BUCKET_NAME=.*", "GCS_BUCKET_NAME=$BUCKET_NAME"
    } else {
        $envContent += "`nGCS_BUCKET_NAME=$BUCKET_NAME"
    }
    
    $envContent | Set-Content ".env"
    Write-Host "✓ .env file updated" -ForegroundColor Green
} else {
    Write-Host "WARNING: .env file not found" -ForegroundColor Yellow
}

Write-Host ""

# Final summary
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration Summary:" -ForegroundColor Green
Write-Host "  Project ID: $PROJECT_ID" -ForegroundColor White
Write-Host "  Bucket Name: $BUCKET_NAME" -ForegroundColor White
Write-Host "  Service Account: $SA_EMAIL" -ForegroundColor White
Write-Host "  Key File: $KEY_FILE" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Verify .env file has been updated" -ForegroundColor White
Write-Host "  2. Run: python verify_setup.py" -ForegroundColor White
Write-Host "  3. Test GCS: python -c `"from src.integrations.gcs_client import get_gcs_client; print('GCS Status:', 'Connected' if get_gcs_client().use_gcs else 'Local')`"" -ForegroundColor White
Write-Host "  4. Run demo: python demo_full_workflow.py" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
