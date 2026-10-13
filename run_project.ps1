Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   🚀 STARTING AURA FULL-STACK PLATFORM (PS-04)   " -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Start Python FastAPI AI Engine
Write-Host "[1/3] Starting Python FastAPI AI Engine on port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\BPUT_HACK_2026; Write-Host '--- PYTHON FASTAPI AI ENGINE (PORT 8000) ---' -ForegroundColor Green; python -m uvicorn ai_engine.api:app --host 127.0.0.1 --port 8000"

Start-Sleep -Seconds 3

# 2. Start Spring Boot Backend
Write-Host "[2/3] Starting Spring Boot Backend on port 8080..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\BPUT_HACK_2026; Write-Host '--- SPRING BOOT BACKEND (PORT 8080) ---' -ForegroundColor Green; & 'C:\Program Files\Java 21\jdk-21\bin\java.exe' -Xmx384m -XX:TieredStopAtLevel=1 -jar backend/target/aura-backend-1.0.0.jar"

Start-Sleep -Seconds 4

# 3. Start React Vite Frontend
Write-Host "[3/3] Starting React Vite Frontend on port 5173..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\BPUT_HACK_2026\frontend; Write-Host '--- REACT VITE FRONTEND (PORT 5173) ---' -ForegroundColor Green; npm run dev"

Write-Host "`nAll 3 services launched successfully! 🎉" -ForegroundColor Green
Write-Host "Open your browser at: http://localhost:5173/" -ForegroundColor Cyan
