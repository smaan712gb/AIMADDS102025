# Setup and Deployment Guide

## 🚀 Quick Setup

### 1. Environment Setup

**Using Conda (Recommended):**
```bash
# Create environment from file
conda env create -f environment.yml

# Activate environment
conda activate AIMADDS102025
```

**Using pip:**
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. API Configuration

**📖 For detailed API key instructions, see [API_KEYS_GUIDE.md](API_KEYS_GUIDE.md)**

**Create `.env` file:**
```bash
cp .env.example .env
```

**Edit `.env` and add your API keys:**
```env
# AI Models (Required)
# Claude Sonnet 4.5
ANTHROPIC_API_KEY=your_claude_api_key_here

# Gemini 2.5 Pro  
GOOGLE_API_KEY=your_gemini_api_key_here

# Grok 4 from X.ai (use xai- prefix)
OPENAI_API_KEY=xai-your_grok_api_key_here

# Financial Data (Required for demo)
FMP_API_KEY=your_fmp_api_key_here

# Web Research (Optional)
TAVILY_API_KEY=your_tavily_key_here

# GCP Configuration (Optional)
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GCS_BUCKET_NAME=your-bucket-name
```

### 3. Configuration Customization

**Edit `config/settings.yaml`** to customize:
- Model parameters (temperature, max_tokens)
- Agent capabilities
- API endpoints
- Output settings
- Processing limits

## 🎯 Running the Demo

### Basic Demo

```bash
# Ensure environment is activated
conda activate AIMADDS102025

# Run demo script
python demo.py
```

**Expected Output:**
- Console logs showing progress
- Financial analysis results
- Excel report in `outputs/` directory

### Custom Analysis

```python
import asyncio
from src.core.state import create_initial_state
from src.agents.financial_analyst import FinancialAnalystAgent
from src.outputs.excel_generator import ExcelGenerator

async def custom_analysis():
    # Your target company
    state = create_initial_state(
        deal_id="CUSTOM-001",
        target_company="Your Company",
        target_ticker="TICK",  # Stock ticker
        investment_thesis="Your thesis",
        strategic_rationale="Your rationale",
        deal_type="acquisition",
        deal_value=1_000_000_000
    )
    
    # Run analysis
    analyst = FinancialAnalystAgent()
    state = await analyst.execute(state)
    
    # Generate report
    generator = ExcelGenerator()
    report = generator.generate_full_report(state)
    
    return report

# Run
report_path = asyncio.run(custom_analysis())
print(f"Report: {report_path}")
```

## 📊 Understanding the Output

### Excel Report Structure

The generated Excel report contains 6 worksheets:

1. **Executive Summary**
   - Deal information
   - Key financial metrics
   - Quick overview

2. **Financial Overview**
   - 5-year historical data
   - Revenue trends chart
   - Growth analysis

3. **DCF Valuation Model**
   - Transparent formulas (all visible)
   - 5-year projections
   - Terminal value calculation
   - Enterprise value

4. **Ratio Analysis**
   - Profitability ratios
   - Liquidity ratios
   - Leverage ratios
   - Efficiency ratios
   - Color-coded assessments

5. **Risk Assessment**
   - Financial red flags
   - Critical risks
   - Impact analysis

6. **Assumptions & Methodology**
   - DCF assumptions
   - Data sources
   - Analysis methodology

### Professional Features

✅ **Transparent Formulas**: All calculations use Excel formulas (not just values)
✅ **Color Coding**: Green for strong, red for weak, yellow for moderate
✅ **Charts**: Automatic generation of trend charts
✅ **Professional Formatting**: Corporate color scheme
✅ **Audit Trail**: All assumptions documented

## 🔧 Troubleshooting

### Common Issues

**1. Missing API Keys**
```
Error: API key not found for anthropic
```
**Solution**: Add `ANTHROPIC_API_KEY` to `.env` file

**2. Import Errors**
```
ModuleNotFoundError: No module named 'langgraph'
```
**Solution**: Reinstall dependencies
```bash
pip install -r requirements.txt
```

**3. FMP API Errors**
```
Failed to fetch financial data
```
**Solutions**:
- Check API key is valid
- Verify ticker symbol is correct
- Check API rate limits
- Ensure internet connection

**4. Configuration Errors**
```
Failed to load configuration
```
**Solution**: Verify `config/settings.yaml` syntax

### Debug Mode

Enable detailed logging:

```python
from loguru import logger
import sys

# Add detailed logging
logger.remove()
logger.add(sys.stderr, level="DEBUG")
```

## 🚀 Production Deployment

### GCP Deployment

**1. Setup GCP Project**
```bash
# Create project
gcloud projects create ma-diligence-prod

# Enable APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable bigquery.googleapis.com
```

**2. Deploy to Cloud Run**
```bash
# Build container
docker build -t gcr.io/PROJECT_ID/ma-diligence:latest .

# Push to registry
docker push gcr.io/PROJECT_ID/ma-diligence:latest

# Deploy
gcloud run deploy ma-diligence \
  --image gcr.io/PROJECT_ID/ma-diligence:latest \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --timeout 3600
```

### Environment Variables in Production

Use Secret Manager for sensitive data:

```bash
# Create secrets
gcloud secrets create anthropic-api-key --data-file=- < api_key.txt
gcloud secrets create fmp-api-key --data-file=- < fmp_key.txt

# Grant access to Cloud Run
gcloud secrets add-iam-policy-binding anthropic-api-key \
  --member=serviceAccount:SERVICE_ACCOUNT \
  --role=roles/secretmanager.secretAccessor
```

## 📈 Performance Optimization

### API Rate Limiting

Configure in `config/settings.yaml`:

```yaml
apis:
  fmp:
    rate_limit: 300  # requests per minute
```

### Concurrent Processing

Adjust in `config/settings.yaml`:

```yaml
processing:
  max_concurrent_tasks: 5  # Increase for better performance
  timeout_seconds: 300
  retry_attempts: 3
```

### Caching

Enable Redis caching:

```python
# Install Redis
pip install redis

# Configure in .env
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 🔐 Security Best Practices

1. **Never commit `.env` file**
   - Added to `.gitignore`
   - Use environment variables in production

2. **Use Secret Management**
   - GCP Secret Manager
   - AWS Secrets Manager
   - Azure Key Vault

3. **API Key Rotation**
   - Rotate keys regularly
   - Monitor usage
   - Set up alerts

4. **Access Control**
   - Limit API key permissions
   - Use service accounts
   - Implement authentication

## 📚 Next Steps

### Immediate Next Steps

1. **Run the demo** to verify setup
2. **Review generated Excel** report
3. **Test with different companies**
4. **Customize configuration** for your needs

### Development Roadmap

1. **Complete Remaining Agents**
   - Project Manager (orchestration)
   - Data Ingestion (document processing)
   - Legal Counsel (legal analysis)
   - Market Strategist (competitive analysis)
   - Integration Planner (post-merger)
   - Synthesis & Reporting (final deliverables)

2. **Add PDF Generation**
   - Executive summary PDF
   - Full report PDF
   - Presentation slides

3. **Build Dashboard**
   - Streamlit interface
   - Real-time progress tracking
   - Interactive visualizations

4. **Enhance Integrations**
   - Vector database for document search
   - Grok 4 for social media
   - OCR for document processing

## 🆘 Support

### Documentation
- [README.md](README.md) - Project overview
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Detailed architecture
- [blueprint.md](blueprint.md) - Original vision

### Getting Help
- Check troubleshooting section above
- Review error logs in console
- Verify API keys and configuration
- Check API rate limits

### Community
- GitHub Issues (coming soon)
- Documentation site (coming soon)
- Discord community (coming soon)

---

**Last Updated**: October 2025  
**Version**: 0.1.0-alpha  
**Status**: Ready for Demo and Development
