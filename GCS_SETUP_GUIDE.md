# Google Cloud Storage (GCS) Setup Guide

This guide walks you through setting up Google Cloud Storage for AIMADDS102025.

## Prerequisites

- Google Cloud account
- Billing enabled on your GCP project
- Admin or Owner permissions on the project

## Step 1: Install Google Cloud SDK

### Windows Installation

1. **Download the installer:**
   - Visit: https://cloud.google.com/sdk/docs/install
   - Download the Google Cloud SDK installer for Windows

2. **Run the installer:**
   - Execute the downloaded file
   - Follow the installation wizard
   - Allow the installer to update your PATH

3. **Initialize gcloud:**
   ```powershell
   # Open a NEW PowerShell window after installation
   gcloud init
   ```

4. **Follow the prompts:**
   - Log in with your Google account
   - Select or create a project
   - Set default region (e.g., us-central1)

## Step 2: Create a GCP Project (if needed)

```bash
# Set your project ID
$PROJECT_ID = "aimadds102025"

# Create new project
gcloud projects create $PROJECT_ID --name="AI M&A Due Diligence"

# Set as active project
gcloud config set project $PROJECT_ID
```

## Step 3: Enable Required APIs

```bash
# Enable Cloud Storage API
gcloud services enable storage.googleapis.com

# Enable BigQuery API (for future data analysis)
gcloud services enable bigquery.googleapis.com

# Enable Vertex AI API (for future ML features)
gcloud services enable aiplatform.googleapis.com

# Enable Cloud Resource Manager API
gcloud services enable cloudresourcemanager.googleapis.com
```

## Step 4: Create GCS Bucket

```bash
# Set bucket name (must be globally unique)
$BUCKET_NAME = "aimadds102025-documents"

# Create bucket in US region
gcloud storage buckets create gs://$BUCKET_NAME `
  --location=US `
  --storage-class=STANDARD `
  --uniform-bucket-level-access

# Verify bucket creation
gcloud storage buckets list
```

## Step 5: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create aimadds-sa `
  --display-name="AIMADDS Service Account" `
  --description="Service account for AI M&A Due Diligence System"

# Grant storage permissions
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:aimadds-sa@$PROJECT_ID.iam.gserviceaccount.com" `
  --role="roles/storage.admin"

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:aimadds-sa@$PROJECT_ID.iam.gserviceaccount.com" `
  --role="roles/bigquery.admin"

# Create and download key
gcloud iam service-accounts keys create aimadds-key.json `
  --iam-account=aimadds-sa@$PROJECT_ID.iam.gserviceaccount.com
```

## Step 6: Configure Environment Variables

Update your `.env` file:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=aimadds102025
GOOGLE_APPLICATION_CREDENTIALS=./aimadds-key.json
GCS_BUCKET_NAME=aimadds102025-documents
```

## Step 7: Test Connection

```bash
# Activate conda environment
conda activate AIMADDS102025

# Test GCS connection
python -c "from google.cloud import storage; client = storage.Client(); print([bucket.name for bucket in client.list_buckets()])"
```

## Bucket Structure

The system will organize files in GCS as follows:

```
gs://aimadds102025-documents/
├── deals/
│   ├── {deal_id}/
│   │   ├── documents/
│   │   │   ├── financials/
│   │   │   ├── legal/
│   │   │   └── market/
│   │   ├── reports/
│   │   │   ├── excel/
│   │   │   └── pdf/
│   │   └── analysis/
│   │       ├── vectors/
│   │       └── embeddings/
├── templates/
└── logs/
```

## Cost Optimization

1. **Use Standard Storage Class:**
   - Best for frequently accessed data
   - ~$0.02 per GB/month

2. **Enable Lifecycle Policies:**
   ```bash
   # Create lifecycle config
   cat > lifecycle.json << EOF
   {
     "rule": [
       {
         "action": {"type": "Delete"},
         "condition": {
           "age": 365,
           "matchesPrefix": ["deals/"]
         }
       }
     ]
   }
   EOF

   # Apply lifecycle policy
   gcloud storage buckets update gs://$BUCKET_NAME --lifecycle-file=lifecycle.json
   ```

3. **Set up Budget Alerts:**
   - Go to: https://console.cloud.google.com/billing/
   - Create budget alerts
   - Set thresholds (e.g., $10, $50, $100)

## Security Best Practices

1. **Restrict Service Account Permissions:**
   - Use principle of least privilege
   - Grant only necessary roles

2. **Keep Credentials Secure:**
   - Never commit service account keys to version control
   - Use environment variables
   - Rotate keys regularly

3. **Enable Audit Logging:**
   ```bash
   gcloud logging read "resource.type=gcs_bucket AND logName:cloudaudit.googleapis.com" --limit 10
   ```

4. **Use VPC Service Controls (Optional):**
   - For enhanced security in production
   - Restrict data exfiltration

## Alternative: Local Storage Fallback

If you prefer not to use GCS initially, the system will automatically fall back to local storage:

```python
# System automatically detects and uses local storage
# Files will be saved to:
# - ./outputs/deals/{deal_id}/
# - ./data/processed/
# - ./data/raw/
```

## Troubleshooting

### "gcloud not recognized" error
- Restart your terminal after installation
- Check PATH environment variable
- Reinstall Google Cloud SDK

### "Permission denied" errors
- Check service account has correct roles
- Verify GOOGLE_APPLICATION_CREDENTIALS path
- Ensure project billing is enabled

### "Bucket already exists" error
- Choose a different bucket name (must be globally unique)
- Try: aimadds102025-documents-{your-initials}

### Authentication errors
- Run: `gcloud auth application-default login`
- Verify service account key file exists
- Check .env file has correct path

## Next Steps

After GCS setup:

1. **Test the integration:**
   ```bash
   python -c "from src.integrations.gcs_client import GCSClient; client = GCSClient(); print('GCS Connected!')"
   ```

2. **Upload a test document:**
   ```bash
   python -c "from src.integrations.gcs_client import GCSClient; GCSClient().upload_file('test.txt', 'test.txt')"
   ```

3. **Run data ingestion agent:**
   ```bash
   python demo_data_ingestion.py
   ```

## Resources

- **GCS Documentation:** https://cloud.google.com/storage/docs
- **SDK Documentation:** https://cloud.google.com/sdk/docs
- **Pricing Calculator:** https://cloud.google.com/products/calculator
- **Best Practices:** https://cloud.google.com/storage/docs/best-practices

---

**Last Updated:** January 2025
