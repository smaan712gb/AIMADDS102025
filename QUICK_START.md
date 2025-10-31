# Quick Start Guide - M&A Diligence Swarm

## Start Backend API Server

1. Open a PowerShell terminal
2. Activate conda environment:
```powershell
conda activate aimadds102025
```

3. Navigate to project directory and start server:
```powershell
cd C:\Users\smaan\OneDrive\AIMADDS102025
python -m src.api.server
```

Backend will run on: **http://localhost:8000**
API docs: **http://localhost:8000/docs**

## Start Frontend Development Server

1. Open a NEW PowerShell terminal
2. Navigate to frontend directory:
```powershell
cd C:\Users\smaan\OneDrive\AIMADDS102025\frontend
```

3. Install dependencies (first time only):
```powershell
npm install
```

4. Start development server:
```powershell
npm run dev
```

Frontend will run on: **http://localhost:5173**

## Default Login Credentials

- **Email**: smaan2011@gmail.com
- **Password**: admin123

## Access the Application

1. Open browser to: http://localhost:5173
2. You'll see the beautiful landing page
3. Click "Sign In" and use the default credentials
4. Explore the professional UI!

## What to Test

### Landing Page (Phase 1 - The Lobby)
- Professional marketing site
- "How It Works" animated sections
- Capabilities showcase
- Security information

### Login Page  
- Simple, elegant authentication
- Demo credentials displayed

### Dashboard (Phase 2 - Control Room - Input)
- Clean input form with 4 fields
- Optional details (thesis, rationale)
- "Start Analysis" button

### Analysis Page (Phase 2 - Control Room - Live Status)
- **🤖 Live Agentic Status Console** ← THE KILLER FEATURE
- Real-time agent progress
- Animated status updates
- Progress bar showing completion

### Results Page (Phase 3 - The Deliverable)
- Valuation range prominently displayed
- Top 3 Risks (red indicators)
- Top 3 Opportunities (green indicators)
- One-click report downloads (PDF, Excel, PowerPoint)
