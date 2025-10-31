# Frontend Production Test - Complete Guide

## Overview
Start both backend API and frontend servers to test the complete system with UI.

---

## Step-by-Step Instructions

### 1. Start Backend API Server (Terminal 1)

Open PowerShell in project directory and run:

```powershell
.\start_production_test.ps1
```

**What it does:**
- Activates conda environment (aimadds102025)
- Starts backend API on http://localhost:8000
- Shows ALL logs in real-time for monitoring

**Wait for this message:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

### 2. Start Frontend Server (Terminal 2 - New PowerShell)

Open a NEW PowerShell terminal and run:

```powershell
cd frontend
npm run dev
```

**Wait for this message:**
```
VITE v... ready in ... ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

### 3. Start Dashboard Server (Terminal 3 - New PowerShell)

Open a THIRD PowerShell terminal and run:

```powershell
conda activate aimadds102025
python revolutionary_dashboard.py
```

**Wait for this message:**
```
🚀 LAUNCHING REVOLUTIONARY AGENTIC INSIGHTS DASHBOARD
Dashboard URL: http://localhost:8050
```

**Note:** Dashboard will show data after analysis completes

---

### 4. Access the Application

Open your browser and navigate to:
```
http://localhost:5173
```

**Login Credentials:**
- Email: `smaan2011@gmail.com`
- Password: `admin123`

---

### 5. Run Analysis from UI

Once logged in:

1. Click **"New Analysis"** button
2. Fill in the form:
   - **Acquirer Ticker:** JPM (or any acquirer)
   - **Target Ticker:** GS (or any target company)
   - **Deal Type:** Merger
   - **Deal Value:** $50B (optional)
3. Click **"Start Analysis"**

---

### 6. Monitor Progress

**In Terminal 1 (Backend Logs):**
Watch for these key events:

```
✓ Analysis started for job: JPM-GS-...
✓ Financial Analyst completed
✓ Synthesis & Reporting Agent started
✓ Synthesis completed successfully
INFO | ✓ Validation PASSED with 0 non-blocking issues
✓ Reports generated successfully
```

**In Browser (Frontend UI):**
- Progress bar shows agent completion
- Real-time status updates
- Download buttons appear when complete

---

### 7. Verify Fixes

**Look for these in Terminal 1 logs:**

✅ **DCF Validation Pass:**
```
INFO | Found synthesized data, version: 1.0
INFO | ✓ Validation PASSED with 0 non-blocking issues
```

✅ **No DCF Errors:**
Should NOT see:
```
ERROR | DCF valuation missing  ❌ (This was the bug - now FIXED)
```

✅ **Report Generation:**
```
INFO | Generating reports for job JPM-GS-...
INFO | Running pre-report data consistency validation...
INFO | ✓ Validation PASSED
```

---

### 8. Download Reports

Once analysis completes, you'll see download buttons in the UI:
- 📄 PDF Report
- 📊 Excel Workbook  
- 📈 PowerPoint Presentation

---

### 9. View Dashboard

Once analysis completes, open the dashboard in a new browser tab:
```
http://localhost:8050
```

**Dashboard Features:**
- 📊 KPI Header with key metrics
- 🎯 Valuation Football Field
- 🚩 Risks & Red Flags
- 💡 Synergies & Opportunities
- 📈 Financial Proof Charts

---

## Troubleshooting

### Backend Not Starting?
```powershell
# Check conda environment
conda env list

# Ensure aimadds102025 exists
conda activate aimadds102025
python --version  # Should be Python 3.11+
```

### Frontend Not Starting?
```powershell
cd frontend
npm install  # Reinstall dependencies
npm run dev
```

### Port Already in Use?
```powershell
# Backend (port 8000)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Frontend (port 5173)
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Dashboard (port 8050)
netstat -ano | findstr :8050
taskkill /PID <PID> /F
```

### Dashboard Not Showing Data?
- Dashboard loads AFTER analysis completes
- Refresh the page after reports are generated
- Check Terminal 1 for "✓ Reports generated successfully"

---

## What to Test

### Critical Test Cases:

1. **Validation Test**
   - ✅ Analysis completes without validation errors
   - ✅ Reports generate successfully
   - ✅ DCF data appears in reports

2. **Data Completeness**
   - ✅ Synthesis collects all agent data
   - ✅ Financial section has dcf_outputs
   - ✅ Enterprise value is populated

3. **Report Quality**
   - ✅ PDF contains DCF analysis
   - ✅ Excel has financial data
   - ✅ PowerPoint has charts

---

## Quick Start Commands

**Terminal 1 (Backend with Logs):**
```powershell
.\start_production_test.ps1
```

**Terminal 2 (Frontend UI):**
```powershell
cd frontend
npm run dev
```

**Terminal 3 (Dashboard):**
```powershell
conda activate aimadds102025
python revolutionary_dashboard.py
```

**Browser:**
```
Main App:   http://localhost:5173
Dashboard:  http://localhost:8050
API Docs:   http://localhost:8000/docs
```

---

## Expected Timeline

- Backend startup: 5-10 seconds
- Frontend startup: 10-15 seconds
- Dashboard startup: 5 seconds  
- Analysis runtime: 2-5 minutes
- Report generation: 10-30 seconds
- Dashboard data load: Automatic after analysis

---

## Success Indicators

✅ **Backend:**
```
INFO | ✓ Validation PASSED with 0 non-blocking issues
```

✅ **Frontend:**
- Progress bar reaches 100%
- "Analysis Complete" message
- Download buttons enabled

✅ **Reports:**
- All 3 report types generated
- DCF data present and accurate
- No placeholder data

---

*Ready to test the complete system with all fixes validated!*
