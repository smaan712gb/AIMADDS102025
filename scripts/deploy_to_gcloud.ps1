# Google Cloud Deployment Script for M&A Diligence Swarm (PowerShell)
# This script automates the complete deployment process for Windows

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  M&A Diligence Swarm - Google Cloud Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Blue

# Check gcloud
if (!(Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: gcloud CLI not found!" -ForegroundColor Red
    Write-Host "Please install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Check npm (for frontend build)
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "WARNING: npm not found. Frontend deployment will be skipped." -ForegroundColor Yellow
    $skipFrontend = $true
} else {
    $skipFrontend = $false
}

Write-Host "✓ Prerequisites check complete" -ForegroundColor Green
Write-Host ""

# Get configuration
Write-Host "Configuration Setup" -ForegroundColor Blue
Write-Host "-------------------" -ForegroundColor Blue

$projectId = Read-Host "Enter your GCP Project ID (default: aimadds-production)"
if ([string]::IsNullOrWhiteSpace($projectId)) {
    $projectId = "aimadds-production"
}

$region = Read-Host "Enter region (default: us-central1)"
if ([string]::IsNullOrWhiteSpace($region)) {
    $region = "us-central1"
}

$domain = Read-Host "Enter your domain name (optional, press Enter to skip)"
$skipDomain = [string]::IsNullOrWhiteSpace($domain)

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  Project ID: $projectId" -ForegroundColor White
Write-Host "  Region: $region" -ForegroundColor White
if (!$skipDomain) {
    Write-Host "  Domain: $domain" -ForegroundColor White
}
Write-Host ""

$confirm = Read-Host "Continue with deployment? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Starting Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Set GCP project
Write-Host "Setting GCP project..." -ForegroundColor Blue
gcloud config set project $projectId
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to set project. You may need to create it first." -ForegroundColor Red
    Write-Host "Run: gcloud projects create $projectId" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Project set" -ForegroundColor Green
Write-Host ""

# Enable APIs
Write-Host "Enabling required Google Cloud APIs (this may take a few minutes)..." -ForegroundColor Blue
gcloud services enable `
    run.googleapis.com `
    sql-component.googleapis.com `
    sqladmin.googleapis.com `
    storage.googleapis.com `
    secretmanager.googleapis.com `
    compute.googleapis.com `
    --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ APIs enabled" -ForegroundColor Green
} else {
    Write-Host "WARNING: Some APIs may have failed to enable" -ForegroundColor Yellow
}
Write-Host ""

# Check for existing Cloud SQL instance
Write-Host "Checking for existing Cloud SQL instance..." -ForegroundColor Blue
$sqlExists = gcloud sql instances describe aimadds-db --project=$projectId 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "⚠  Cloud SQL instance 'aimadds-db' already exists. Skipping creation." -ForegroundColor Yellow
    $skipDbCreation = $true
} else {
    $skipDbCreation = $false
    Write-Host "Creating Cloud SQL PostgreSQL instance (this takes 5-10 minutes)..." -ForegroundColor Blue
    
    $dbRootPassword = Read-Host "Enter database root password" -AsSecureString
    $dbRootPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbRootPassword))
    
    $dbUserPassword = Read-Host "Enter database user password" -AsSecureString
    $dbUserPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbUserPassword))
    
    gcloud sql instances create aimadds-db `
        --database-version=POSTGRES_15 `
        --tier=db-f1-micro `
        --region=$region `
        --root-password="$dbRootPasswordPlain" `
        --backup-start-time=03:00 `
        --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Cloud SQL instance created" -ForegroundColor Green
        
        # Create database
        Write-Host "Creating database..." -ForegroundColor Blue
        gcloud sql databases create ma_diligence --instance=aimadds-db --quiet
        Write-Host "✓ Database created" -ForegroundColor Green
        
        # Create user
        Write-Host "Creating database user..." -ForegroundColor Blue
        gcloud sql users create aimadds_user `
            --instance=aimadds-db `
            --password="$dbUserPasswordPlain" `
            --quiet
        Write-Host "✓ Database user created" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to create Cloud SQL instance" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Get Cloud SQL connection name
Write-Host "Getting Cloud SQL connection name..." -ForegroundColor Blue
$cloudSqlConnection = gcloud sql instances describe aimadds-db --format='value(connectionName)'
Write-Host "✓ Cloud SQL connection: $cloudSqlConnection" -ForegroundColor Green
Write-Host ""

# Set up secrets
Write-Host "Setting up secrets in Secret Manager..." -ForegroundColor Blue

# Helper function for secrets
function Set-GCloudSecret {
    param($secretName, $secretValue)
    
    $secretExists = gcloud secrets describe $secretName --project=$projectId 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Output $secretValue | gcloud secrets versions add $secretName --data-file=- --quiet
    } else {
        Write-Output $secretValue | gcloud secrets create $secretName --data-file=- --quiet
    }
}

# JWT Secret
$jwtSecretExists = gcloud secrets describe jwt-secret --project=$projectId 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating JWT secret..." -ForegroundColor Blue
    $jwtSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    Set-GCloudSecret "jwt-secret" $jwtSecret
    Write-Host "✓ JWT secret created" -ForegroundColor Green
}

# API Keys - Read from .env file
Write-Host "Reading API keys from .env file..." -ForegroundColor Blue

$envFile = ".env"
if (Test-Path $envFile) {
    Write-Host "✓ Found .env file" -ForegroundColor Green
    
    # Parse .env file
    $envVars = @{}
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")
            $envVars[$key] = $value
        }
    }
    
    # Extract API keys
    $anthropicKey = $envVars['ANTHROPIC_API_KEY']
    $googleKey = $envVars['GOOGLE_API_KEY']
    $openaiKey = $envVars['OPENAI_API_KEY']
    $xaiKey = $envVars['XAI_API_KEY']
    $tavilyKey = $envVars['TAVILY_API_KEY']
    $fmpKey = $envVars['FMP_API_KEY']
    
    # Validate keys exist
    if ([string]::IsNullOrWhiteSpace($anthropicKey)) {
        Write-Host "⚠  ANTHROPIC_API_KEY not found in .env" -ForegroundColor Yellow
        $anthropicKey = Read-Host "Enter Anthropic API key manually"
    } else {
        Write-Host "  ✓ Found ANTHROPIC_API_KEY" -ForegroundColor Green
    }
    
    if ([string]::IsNullOrWhiteSpace($googleKey)) {
        Write-Host "⚠  GOOGLE_API_KEY not found in .env" -ForegroundColor Yellow
        $googleKey = Read-Host "Enter Google API key manually"
    } else {
        Write-Host "  ✓ Found GOOGLE_API_KEY" -ForegroundColor Green
    }
    
    if ([string]::IsNullOrWhiteSpace($openaiKey)) {
        Write-Host "⚠  OPENAI_API_KEY not found in .env" -ForegroundColor Yellow
        $openaiKey = Read-Host "Enter OpenAI API key manually"
    } else {
        Write-Host "  ✓ Found OPENAI_API_KEY" -ForegroundColor Green
    }
    
    if ([string]::IsNullOrWhiteSpace($xaiKey)) {
        Write-Host "⚠  XAI_API_KEY not found in .env" -ForegroundColor Yellow
        $xaiKey = Read-Host "Enter XAI API key (Grok) manually"
    } else {
        Write-Host "  ✓ Found XAI_API_KEY (Grok)" -ForegroundColor Green
    }
    
    if ([string]::IsNullOrWhiteSpace($tavilyKey)) {
        Write-Host "⚠  TAVILY_API_KEY not found in .env" -ForegroundColor Yellow
        $tavilyKey = Read-Host "Enter Tavily API key (Web research) manually"
    } else {
        Write-Host "  ✓ Found TAVILY_API_KEY (Web research)" -ForegroundColor Green
    }
    
    if ([string]::IsNullOrWhiteSpace($fmpKey)) {
        Write-Host "⚠  FMP_API_KEY not found in .env" -ForegroundColor Yellow
        $fmpKey = Read-Host "Enter FMP API key manually"
    } else {
        Write-Host "  ✓ Found FMP_API_KEY" -ForegroundColor Green
    }
    
} else {
    Write-Host "⚠  .env file not found. Please enter API keys manually." -ForegroundColor Yellow
    $anthropicKey = Read-Host "Anthropic API key (Claude)"
    $googleKey = Read-Host "Google API key (Gemini)"
    $openaiKey = Read-Host "OpenAI API key (Grok)"
    $fmpKey = Read-Host "FMP API key (Financial data)"
}

# Store secrets
Set-GCloudSecret "anthropic-api-key" $anthropicKey
Set-GCloudSecret "google-api-key" $googleKey
Set-GCloudSecret "openai-api-key" $openaiKey
Set-GCloudSecret "xai-api-key" $xaiKey
Set-GCloudSecret "tavily-api-key" $tavilyKey
Set-GCloudSecret "fmp-api-key" $fmpKey

# Database password
if (!$skipDbCreation -and ![string]::IsNullOrWhiteSpace($dbUserPasswordPlain)) {
    Set-GCloudSecret "db-password" $dbUserPasswordPlain
}

Write-Host "✓ All secrets configured" -ForegroundColor Green
Write-Host ""

# Grant Secret Manager permissions to Cloud Run service account
Write-Host "Granting Secret Manager permissions..." -ForegroundColor Blue
$projectNumber = gcloud projects describe $projectId --format='value(projectNumber)'
$serviceAccount = "$projectNumber-compute@developer.gserviceaccount.com"

$secrets = @("anthropic-api-key", "google-api-key", "openai-api-key", "xai-api-key", "tavily-api-key", "fmp-api-key", "jwt-secret", "db-password")
foreach ($secret in $secrets) {
    gcloud secrets add-iam-policy-binding $secret `
        --member="serviceAccount:$serviceAccount" `
        --role="roles/secretmanager.secretAccessor" `
        --quiet 2>&1 | Out-Null
}
Write-Host "✓ Permissions granted" -ForegroundColor Green
Write-Host ""

# Create Cloud Storage buckets
Write-Host "Setting up Cloud Storage..." -ForegroundColor Blue

# Reports bucket
$reportsBucketExists = gsutil ls -p $projectId "gs://$projectId-reports" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "⚠  Reports bucket already exists" -ForegroundColor Yellow
} else {
    gsutil mb -p $projectId -c STANDARD -l $region "gs://$projectId-reports"
    Write-Host "✓ Reports bucket created" -ForegroundColor Green
}

# Frontend bucket
$frontendBucketExists = gsutil ls -p $projectId "gs://$projectId-frontend" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "⚠  Frontend bucket already exists" -ForegroundColor Yellow
} else {
    gsutil mb -p $projectId -c STANDARD -l $region "gs://$projectId-frontend"
    
    # Configure CORS
    $corsJson = @"
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
"@
    $corsJson | Out-File -FilePath "$env:TEMP\cors.json" -Encoding utf8
    gsutil cors set "$env:TEMP\cors.json" "gs://$projectId-frontend"
    Remove-Item "$env:TEMP\cors.json"
    
    Write-Host "✓ Frontend bucket created with CORS" -ForegroundColor Green
}
Write-Host ""

# Deploy Backend to Cloud Run
Write-Host "Building and deploying backend to Cloud Run (this may take 10-15 minutes)..." -ForegroundColor Blue
Write-Host "This will build a Docker container and deploy it..." -ForegroundColor Yellow

gcloud run deploy aimadds-backend `
    --source . `
    --platform managed `
    --region $region `
    --allow-unauthenticated `
    --set-env-vars="ENVIRONMENT=production,CLOUD_SQL_CONNECTION_NAME=$cloudSqlConnection,POSTGRES_DB=ma_diligence,POSTGRES_USER=aimadds_user,GCS_BUCKET_NAME=$projectId-reports" `
    --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest,GOOGLE_API_KEY=google-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,XAI_API_KEY=xai-api-key:latest,TAVILY_API_KEY=tavily-api-key:latest,FMP_API_KEY=fmp-api-key:latest,JWT_SECRET_KEY=jwt-secret:latest,POSTGRES_PASSWORD=db-password:latest" `
    --add-cloudsql-instances=$cloudSqlConnection `
    --min-instances=0 `
    --max-instances=10 `
    --memory=4Gi `
    --cpu=2 `
    --timeout=3600 `
    --concurrency=80 `
    --quiet

if ($LASTEXITCODE -eq 0) {
    $backendUrl = gcloud run services describe aimadds-backend --region=$region --format='value(status.url)'
    Write-Host "✓ Backend deployed: $backendUrl" -ForegroundColor Green
    
    # Test backend health
    Write-Host "Testing backend health..." -ForegroundColor Blue
    try {
        $response = Invoke-WebRequest -Uri "$backendUrl/api/health" -Method Get -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Backend is healthy!" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠  Backend health check failed. Check logs later." -ForegroundColor Yellow
    }
} else {
    Write-Host "ERROR: Backend deployment failed" -ForegroundColor Red
    Write-Host "Check logs: gcloud run services logs read aimadds-backend --region=$region" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Build and deploy frontend
if (!$skipFrontend) {
    Write-Host "Building and deploying frontend..." -ForegroundColor Blue
    
    Push-Location frontend
    
    # Create production environment file
    @"
VITE_API_URL=$backendUrl
VITE_WS_URL=$($backendUrl.Replace('https','wss'))
"@ | Out-File -FilePath .env.production -Encoding utf8
    
    # Install and build
    Write-Host "Installing npm packages..." -ForegroundColor Blue
    npm install --silent
    
    Write-Host "Building frontend..." -ForegroundColor Blue
    npm run build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Frontend built" -ForegroundColor Green
        
        # Deploy to Cloud Storage
        Write-Host "Deploying to Cloud Storage..." -ForegroundColor Blue
        gsutil -m rsync -r -d dist "gs://$projectId-frontend"
        
        # Make files public
        gsutil -m acl ch -r -u AllUsers:R "gs://$projectId-frontend"
        
        # Set website configuration
        gsutil web set -m index.html -e index.html "gs://$projectId-frontend"
        
        $frontendUrl = "https://storage.googleapis.com/$projectId-frontend/index.html"
        Write-Host "✓ Frontend deployed: $frontendUrl" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Frontend build failed" -ForegroundColor Red
        $frontendUrl = "Not deployed"
    }
    
    Pop-Location
} else {
    Write-Host "⚠  Frontend deployment skipped (npm not found)" -ForegroundColor Yellow
    $frontendUrl = "Not deployed"
}
Write-Host ""

# Print deployment summary
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Deployment Details:" -ForegroundColor Yellow
Write-Host "  Backend URL:  $backendUrl" -ForegroundColor White
Write-Host "  Frontend URL: $frontendUrl" -ForegroundColor White
Write-Host "  Region:       $region" -ForegroundColor White
Write-Host "  Project:      $projectId" -ForegroundColor White
Write-Host ""
Write-Host "🔐 Admin Credentials:" -ForegroundColor Yellow
Write-Host "  Email:        smaan2011@gmail.com" -ForegroundColor White
Write-Host "  Password:     admin123" -ForegroundColor White
Write-Host "  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!" -ForegroundColor Red
Write-Host ""
Write-Host "📚 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test the application: $frontendUrl" -ForegroundColor White
Write-Host "  2. Change admin password via the UI" -ForegroundColor White
Write-Host "  3. Add team members as users" -ForegroundColor White
Write-Host "  4. Share link with clients!" -ForegroundColor White
Write-Host ""
Write-Host "📖 View logs:" -ForegroundColor Yellow
Write-Host "  gcloud run services logs read aimadds-backend --region=$region --follow" -ForegroundColor White
Write-Host ""
Write-Host "💰 Monitor costs:" -ForegroundColor Yellow
Write-Host "  https://console.cloud.google.com/billing" -ForegroundColor White
Write-Host ""
Write-Host "🔄 To update deployment:" -ForegroundColor Yellow
Write-Host "  .\scripts\deploy_to_gcloud.ps1" -ForegroundColor White
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Ready to start analyzing M&A deals!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
