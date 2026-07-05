# TaskFlow Pro — Windows setup helper
# Run from project root:  powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"
Write-Host "`n=== TaskFlow Pro Setup ===`n" -ForegroundColor Cyan

# 1. Backend dependencies
Write-Host "[1/5] Installing Python dependencies..." -ForegroundColor Yellow
Set-Location "$PSScriptRoot\backend"
pip install -r requirements.txt --user -q

# 2. Database
Write-Host "[2/5] Setting up MySQL database..." -ForegroundColor Yellow
python setup_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nMySQL is not running. Install/start MySQL first, then re-run this script.`n" -ForegroundColor Red
    exit 1
}

# 3. Frontend dependencies
Write-Host "[3/5] Installing Node dependencies..." -ForegroundColor Yellow
Set-Location "$PSScriptRoot\frontend"
npm install --silent

Write-Host "[4/5] Setup complete!" -ForegroundColor Green
Write-Host "`nTo run the app, open TWO terminals:`n" -ForegroundColor Cyan
Write-Host "  Terminal 1 (Backend):" -ForegroundColor White
Write-Host "    cd backend" -ForegroundColor Gray
Write-Host "    python run.py`n" -ForegroundColor Gray
Write-Host "  Terminal 2 (Frontend):" -ForegroundColor White
Write-Host "    cd frontend" -ForegroundColor Gray
Write-Host "    npm run dev`n" -ForegroundColor Gray
Write-Host "  Then open: http://localhost:3000" -ForegroundColor Green
Write-Host "  Login: admin@taskflow.pro / Admin@123`n" -ForegroundColor Green
