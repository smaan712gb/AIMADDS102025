# 🏢 AIMADDS - AI-Powered M&A Due Diligence Platform

[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production-green.svg)](https://aimadds-backend-zex5qoe5gq-uc.a.run.app/api/health)
[![Platform](https://img.shields.io/badge/Platform-Google_Cloud-4285F4.svg)](https://cloud.google.com)

> **⚠️ PROPRIETARY SOFTWARE - ALL RIGHTS RESERVED**
> 
> This repository is publicly visible for transparency and educational purposes only.
> **You are NOT permitted to copy, use, or distribute this code without explicit written permission.**
> See [LICENSE](LICENSE) for full terms.

## Overview

AIMADDS is an enterprise-grade M&A due diligence platform that leverages 18 specialized AI agents to automate comprehensive deal analysis. The system processes SEC filings, financial statements, and market data to generate investment committee-ready reports.

### 🚀 Live Demo

**Production Platform:** https://storage.googleapis.com/amadds102025-frontend/index.html

**API Documentation:** https://aimadds-backend-zex5qoe5gq-uc.a.run.app/docs

## Key Features

### 🤖 18 Specialized AI Agents
- **Project Manager** - Deal orchestration and task planning
- **Financial Analyst** - DCF valuation with Monte Carlo simulation
- **Financial Deep Dive** - Working capital and cash conversion analysis
- **Legal Counsel** - Risk factor extraction and compliance review
- **Market Strategist** - Competitive positioning and sentiment analysis
- **Competitive Benchmarking** - Peer comparison and market share analysis
- **Macroeconomic Analyst** - Interest rate and economic scenario modeling
- **Risk Assessment** - Comprehensive risk matrix and mitigation strategies
- **Tax Structuring** - Deal structure optimization for tax efficiency
- **Deal Structuring** - Purchase vs. asset sale analysis
- **Accretion/Dilution** - EPS impact and pro forma modeling
- **Sources & Uses** - Capital structure and funding analysis
- **Contribution Analysis** - Value attribution and ownership fairness
- **Exchange Ratio** - Share exchange fairness analysis
- **Integration Planner** - Day 1/100/365 roadmap with synergy quantification
- **External Validator** - Wall Street research cross-validation
- **Synthesis & Reporting** - Executive summary and recommendations

### 📊 Revolutionary Output Formats
- **Glass Box Excel** - Transparent formulas with 6 specialized tabs
- **C-Suite PowerPoint** - Investment committee presentation
- **Diligence Bible PDF** - Comprehensive due diligence report

### 🔐 Enterprise Security
- Multi-user authentication with JWT tokens
- Role-based access control (Admin/User)
- PostgreSQL database with encryption
- Google Cloud Secret Manager integration
- Auto-scaling infrastructure (0-10 instances)

### 🌐 Production Architecture
```
┌──────────────────────────────────────────┐
│         Custom Domain (HTTPS)            │
└────────────────┬─────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼────┐           ┌────────▼────────┐
│Frontend│           │   Backend API    │
│Storage │           │   (Cloud Run)    │
│ + CDN  │           │   Auto-scaling   │
└────────┘           └─────────┬────────┘
                               │
              ┌────────────────┴────────────┐
              │                             │
       ┌──────▼──────┐           ┌─────────▼────────┐
       │  Cloud SQL  │           │  Cloud Storage   │
       │ PostgreSQL  │           │  (Reports/Files) │
       └─────────────┘           └──────────────────┘
```

## Technology Stack

### AI/ML
- **Anthropic Claude** - Legal analysis, synthesis, advanced reasoning
- **Google Gemini** - External validation, research, web search
- **OpenAI GPT** - General AI capabilities
- **X.AI Grok** - Market sentiment and social media analysis
- **LangChain** - AI workflow orchestration
- **ChromaDB** - Vector database for document retrieval

### Backend
- **FastAPI** - High-performance API framework
- **Python 3.11** - Core language
- **PostgreSQL** - Relational database (Cloud SQL)
- **SQLAlchemy** - ORM
- **WebSockets** - Real-time updates
- **Uvicorn** - ASGI server

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Zustand** - State management
- **Axios** - HTTP client

### Infrastructure
- **Google Cloud Run** - Serverless containers
- **Cloud SQL** - Managed PostgreSQL
- **Cloud Storage** - Static assets & reports
- **Secret Manager** - API key management
- **Cloud Build** - CI/CD pipeline

### Data Sources
- **SEC EDGAR** - 10-K, 10-Q, 8-K filings
- **Financial Modeling Prep** - Financial statements & market data
- **Tavily** - Web research and news aggregation

## Project Structure

```
AIMADDS102025/
├── src/
│   ├── agents/          # 18 specialized AI agents
│   ├── api/             # FastAPI backend
│   ├── core/            # LLM factory, state management
│   ├── database/        # PostgreSQL models
│   ├── integrations/    # FMP, SEC, Tavily clients
│   ├── outputs/         # Report generators
│   └── utils/           # Validators, helpers
├── frontend/            # React application
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── pages/       # Route pages
│   │   ├── services/    # API clients
│   │   └── store/       # State management
├── scripts/             # Deployment automation
├── Dockerfile           # Container configuration
├── requirements.txt     # Python dependencies (210+ packages)
└── environment.yml      # Conda environment specification
```

## Documentation

- **[Deployment Guide](GOOGLE_CLOUD_DEPLOYMENT_GUIDE.md)** - Complete 11-phase deployment
- **[Quick Start](DEPLOYMENT_QUICK_START.md)** - 30-minute deployment guide
- **[API Documentation](https://aimadds-backend-zex5qoe5gq-uc.a.run.app/docs)** - Interactive API docs

## System Requirements

### For Development:
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- 16GB RAM minimum
- Conda (recommended)

### For Production (Google Cloud):
- GCP account with billing enabled
- Cloud SQL PostgreSQL instance
- Cloud Run service
- ~$50-200/month depending on usage

## Deployment

**⚠️ This is proprietary software. Deployment requires explicit permission.**

For authorized users with deployment rights:

```powershell
# Navigate to project
cd AIMADDS102025

# Run automated deployment
.\scripts\deploy_to_gcloud.ps1
```

See [DEPLOYMENT_QUICK_START.md](DEPLOYMENT_QUICK_START.md) for detailed instructions.

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - Add user (admin only)
- `GET /api/auth/me` - Current user info
- `GET /api/auth/users` - List all users (admin only)
- `DELETE /api/auth/users/{user_id}` - Delete user (admin only)

### Analysis
- `POST /api/analysis/start` - Start new analysis
- `GET /api/analysis/{job_id}/progress` - Get progress
- `GET /api/analysis/{job_id}/result` - Get results
- `GET /api/analysis/list` - List analyses
- `GET /api/analysis/{job_id}/download/{file_type}` - Download reports

### Real-Time
- `WS /ws/analysis/{job_id}` - WebSocket for live updates

## Security & Compliance

- **Data Encryption**: All data encrypted at rest and in transit (TLS 1.3)
- **Access Control**: JWT-based authentication with role-based permissions
- **Secret Management**: API keys stored in Google Secret Manager
- **Audit Logging**: Complete audit trail in Cloud Logging
- **Backup**: Daily automated backups with 7-day retention
- **DDoS Protection**: Cloud Armor integration available
- **SOC 2 Compliant Infrastructure**: Google Cloud's certified infrastructure

## Performance

- **Response Time**: < 2 seconds for API calls
- **Analysis Time**: 15-30 minutes for complete due diligence
- **Concurrent Users**: Supports 100+ simultaneous users
- **Auto-Scaling**: 0-10 instances (configurable up to 100+)
- **Uptime**: 99.95% SLA from Google Cloud Run

## Cost Structure

### Infrastructure Costs (Monthly)
- **Light Usage** (1-5 analyses/week): $20-40
- **Moderate Usage** (10-20 analyses/week): $100-180
- **Heavy Usage** (50+ analyses/week): $350-670

### What's Included:
- Unlimited users
- Automatic backups
- SSL/HTTPS certificates
- Global CDN
- DDoS protection
- Monitoring & logging

## License

**This software is proprietary and confidential.**

Copyright © 2025 AIMADDS. All rights reserved.

Viewing this repository does NOT grant you rights to use, copy, or distribute the code. See [LICENSE](LICENSE) for complete terms.

### Licensing Inquiries

For commercial licensing, partnerships, or authorization to use this software:
- Email: smaan2011@gmail.com
- Include: Company name, use case, expected volume

## Support

This is proprietary software with limited public support.

For authorized users:
- **Documentation**: See `/docs` folder
- **API Issues**: Check `/api/health` endpoint
- **Deployment**: Review deployment guides

## Acknowledgments

Built with cutting-edge AI technologies:
- Anthropic Claude for legal analysis
- Google Gemini for research validation
- X.AI Grok for market sentiment
- OpenAI for general capabilities
- LangChain for orchestration

## Disclaimer

This software is provided for authorized use only. Unauthorized copying, distribution, or use may result in legal action. The software is provided "AS IS" without warranty of any kind.

---

**© 2025 AIMADDS. All Rights Reserved.**

**This is proprietary software. Public visibility ≠ Open Source.**
