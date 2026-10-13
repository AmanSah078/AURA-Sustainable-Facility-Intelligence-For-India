Write-Host "Stopping AURA project services..." -ForegroundColor Yellow

# Kill Python uvicorn
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Kill Java backend
Get-Process -Name "java" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Kill Node frontend
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "All AURA services stopped cleanly. ✅" -ForegroundColor Green
