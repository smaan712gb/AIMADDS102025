# Start Revolutionary M&A System - All Servers
# Launches backend, frontend, and revolutionary dashboard

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  REVOLUTIONARY M&A SYSTEM - STARTUP SCRIPT" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory (project root)
$projectRoot = "c:\Users\smaan\OneDrive\AIMADDS102025"
Set-Location $projectRoot

# Initialize conda for PowerShell if not already done
$condaPath = "C:\Users\smaan\anaconda3"
if (Test-Path "$condaPath\Scripts\conda.exe") {
    & "$condaPath\shell\condabin\conda-hook.ps1"
}

# Activate conda environment
Write-Host "Activating conda environment: AIMADDS102025" -ForegroundColor Yellow
conda activate AIMADDS102025

Write-Host ""
Write-Host "System Components:" -ForegroundColor Green
Write-Host "  1. Backend API (FastAPI)" -ForegroundColor White
Write-Host "  2. Frontend Dashboard (React)" -ForegroundColor White
Write-Host "  3. Revolutionary Agentic Insights Dashboard (Dash)" -ForegroundColor White
Write-Host ""

# Create log directory
$logDir = Join-Path $projectRoot "logs"
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Start Backend API
Write-Host "Starting Backend API..." -ForegroundColor Cyan
$backendCmd = "cd '$projectRoot'; conda activate AIMADDS102025; python -m uvicorn src.api.server:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting Frontend Dashboard..." -ForegroundColor Cyan
$frontendPath = Join-Path $projectRoot "frontend"
$frontendCmd = "cd '$frontendPath'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal

Start-Sleep -Seconds 3

# Start Revolutionary Dashboard
Write-Host "Starting Revolutionary Agentic Insights Dashboard..." -ForegroundColor Cyan
$dashboardCmd = "cd '$projectRoot'; conda activate AIMADDS102025; python revolutionary_dashboard.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $dashboardCmd -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "  ALL SERVERS STARTED SUCCESSFULLY" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Access Points:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Backend API:              http://localhost:8000" -ForegroundColor White
Write-Host "  API Documentation:        http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "  Frontend Dashboard:       http://localhost:5173" -ForegroundColor White
Write-Host "  (or check console for actual Vite port)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Revolutionary Dashboard:  http://localhost:8050" -ForegroundColor Yellow
Write-Host "  (Agentic Insights - Glass Box Visualization)" -ForegroundColor Gray
Write-Host ""

Write-Host "Revolutionary Features Available:" -ForegroundColor Green
Write-Host "  - Glass Box Excel with 6 revolutionary tabs" -ForegroundColor White
Write-Host "  - C-Suite PowerPoint with agent showcase" -ForegroundColor White
Write-Host "  - Diligence Bible PDF with embedded evidence" -ForegroundColor White
Write-Host "  - Agentic Insights Dashboard (Answer First design)" -ForegroundColor White
Write-Host ""

Write-Host "After Analysis Completes:" -ForegroundColor Cyan
Write-Host "  Revolutionary reports auto-generate and appear in:" -ForegroundColor White
Write-Host "  - outputs/revolutionary/ (Revolutionary Glass Box reports)" -ForegroundColor Gray
Write-Host "  - Dashboard shows download links automatically" -ForegroundColor Gray
Write-Host ""

Write-Host "Quick Start:" -ForegroundColor Yellow
Write-Host "  1. Navigate to http://localhost:5173" -ForegroundColor White
Write-Host "  2. Run an analysis for ORCL acquisition" -ForegroundColor White
Write-Host "  3. Watch 13 AI agents execute in real-time" -ForegroundColor White
Write-Host "  4. Download revolutionary reports when complete" -ForegroundColor White
Write-Host "  5. View Agentic Insights at http://localhost:8050" -ForegroundColor White
Write-Host ""

Write-Host "================================================================================" -ForegroundColor Green
Write-Host "  REVOLUTIONARY SYSTEM OPERATIONAL" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Press Ctrl+C to stop this script (servers will continue running)" -ForegroundColor Yellow
Write-Host "To stop all servers, close their terminal windows" -ForegroundColor Yellow
Write-Host ""

# Keep script running
while ($true) {
    Start-Sleep -Seconds 10
}
