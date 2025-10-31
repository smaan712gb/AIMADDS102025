# M&A Diligence Swarm - Production Test with Log Monitoring
# Starts backend API with full log visibility for testing

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  M&A Diligence Swarm" -ForegroundColor Cyan
Write-Host "  Production Test Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activate conda environment
Write-Host "Activating conda environment..." -ForegroundColor Yellow
conda activate aimadds102025

# Check if activation successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Conda environment activated: aimadds102025" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to activate conda environment" -ForegroundColor Red
    Write-Host "  Please ensure conda is installed and environment exists" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Backend API Server" -ForegroundColor Cyan
Write-Host "  with FULL LOG MONITORING" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""
Write-Host "Logs will appear below:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

# Start backend server with logs in current terminal
python -m src.api.server
