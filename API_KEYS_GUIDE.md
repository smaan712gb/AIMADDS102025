# API Keys Setup Guide

This guide provides detailed instructions for obtaining and configuring API keys for all AI models and services used in AIMADDS102025.

## 🚀 Quick Start

1. Copy `.env.example` to `.env`
2. Follow the sections below to obtain each API key
3. Paste your keys into the `.env` file
4. Run `python verify_setup.py` to verify your setup

---

## 🤖 AI Model API Keys

### 1. Claude Sonnet 4.5 (Anthropic)

**Current Model:** `claude-sonnet-4.5-20250514`

**How to Get Your API Key:**
1. Visit: https://console.anthropic.com/
2. Sign up or log in to your account
3. Navigate to "API Keys" section
4. Click "Create Key"
5. Copy your API key

**Add to .env:**
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxx
```

**Pricing:** Pay-as-you-go (check latest pricing at https://www.anthropic.com/pricing)

---

### 2. Gemini 2.5 Pro (Google)

**Current Model:** `gemini-2.5-pro`

**How to Get Your API Key:**
1. Visit: https://makersuite.google.com/app/apikey
   - OR: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Select a Google Cloud project (or create new)
5. Copy your API key

**Add to .env:**
```bash
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Pricing:** Free tier available, then pay-as-you-go

**Note:** Gemini 2.5 Pro has a 1M token context window!

---

### 3. Grok 4 (X.ai)

**Current Model:** `grok-4-latest`

**How to Get Your API Key:**
1. Visit: https://console.x.ai/
2. Sign up or log in with your X (Twitter) account
3. Navigate to API Keys section
4. Click "Create New Key"
5. Copy your API key (starts with `xai-`)

**Add to .env:**
```bash
OPENAI_API_KEY=xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Important Notes:**
- Grok API uses OpenAI-compatible endpoints at `https://api.x.ai/v1`
- Despite the variable name being `OPENAI_API_KEY`, this is for Grok
- The key should start with `xai-` prefix

**Example API Usage:**
```bash
curl https://api.x.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer xai-YOUR_API_KEY" \
  -d '{
    "messages": [
      {
        "role": "system",
        "content": "You are a test assistant."
      },
      {
        "role": "user",
        "content": "Testing. Just say hi and hello world and nothing else."
      }
    ],
    "model": "grok-4-latest",
    "stream": false,
    "temperature": 0
  }'
```

**Pricing:** Check https://x.ai/ for latest pricing

---

## 📊 Financial Data API Keys

### 4. Financial Modeling Prep (FMP)

**What it provides:** Company financials, ratios, key metrics, stock data

**How to Get Your API Key:**
1. Visit: https://financialmodelingprep.com/developer/docs/
2. Sign up for a free account
3. Navigate to Dashboard
4. Copy your API key

**Add to .env:**
```bash
FMP_API_KEY=your_fmp_api_key_here
```

**Free Tier:** 250 API calls per day

---

## 🔍 Web Research API Keys

### 5. Tavily (Optional but Recommended)

**What it provides:** Web search and research capabilities

**How to Get Your API Key:**
1. Visit: https://tavily.com/
2. Sign up for an account
3. Navigate to API Keys section
4. Copy your API key

**Add to .env:**
```bash
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Free Tier:** Available with usage limits

---

## ☁️ Google Cloud Platform (Optional)

### 6. Google Cloud Services

**Required for:** Cloud storage, BigQuery, AI Platform (optional features)

**How to Set Up:**
1. Visit: https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable required APIs:
   - Cloud Storage API
   - BigQuery API
   - Vertex AI API
4. Create a service account:
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Grant necessary roles
   - Create and download JSON key

**Add to .env:**
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
GCS_BUCKET_NAME=your-bucket-name
```

---

## 🗄️ Database Configuration (Optional)

### 7. PostgreSQL

If you want to use PostgreSQL for data storage:

**Add to .env:**
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ma_diligence
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
```

### 8. Redis

If you want to use Redis for caching:

**Add to .env:**
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
```

---

## ✅ Verification

After configuring all your API keys:

1. **Activate the conda environment:**
   ```bash
   conda activate AIMADDS102025
   ```

2. **Run the verification script:**
   ```bash
   python verify_setup.py
   ```

3. **Check the output:**
   - ✓ Green checks indicate properly configured keys
   - ❌ Red X's indicate missing or placeholder keys

---

## 🔒 Security Best Practices

1. **Never commit .env file to version control**
   - It's already in `.gitignore`
   - Double-check before pushing code

2. **Keep API keys secure**
   - Don't share them in screenshots or logs
   - Rotate keys if exposed

3. **Use environment-specific keys**
   - Different keys for development/production
   - Consider using key management services for production

4. **Monitor usage**
   - Check API dashboards regularly
   - Set up billing alerts
   - Track usage patterns

---

## 💰 Cost Optimization Tips

1. **Start with Free Tiers**
   - Most services offer free tiers
   - Great for development and testing

2. **Use Appropriate Models**
   - Use smaller/cheaper models for simple tasks
   - Reserve powerful models for complex analysis

3. **Implement Caching**
   - Cache API responses when possible
   - Reduces redundant API calls

4. **Set Rate Limits**
   - Configure `RATE_LIMIT_PER_MINUTE` in .env
   - Prevents accidental overuse

5. **Monitor Costs**
   - Check dashboards regularly
   - Set up billing alerts

---

## 🆘 Troubleshooting

### "API key not found" error
- Check that .env file exists in project root
- Verify no typos in key names
- Ensure no extra spaces around the equals sign

### "Invalid API key" error
- Verify you copied the entire key
- Check key hasn't been revoked
- Confirm you're using the correct key for each service

### "Rate limit exceeded" error
- Wait before retrying
- Consider upgrading your plan
- Implement better caching

### Import errors
- Ensure conda environment is activated
- Run: `conda activate AIMADDS102025`
- Check packages: `python verify_setup.py`

---

## 📚 Additional Resources

- **Anthropic Claude:** https://docs.anthropic.com/
- **Google Gemini:** https://ai.google.dev/docs
- **X.ai Grok:** https://docs.x.ai/
- **Financial Modeling Prep:** https://site.financialmodelingprep.com/developer/docs
- **Tavily:** https://docs.tavily.com/

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review error messages carefully
3. Verify all API keys are correctly configured
4. Run `python verify_setup.py` for diagnostic info

---

**Last Updated:** January 2025
**Project:** AIMADDS102025 - AI Multi-Agent Due Diligence System
