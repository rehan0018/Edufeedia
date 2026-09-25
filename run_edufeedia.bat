@echo off
echo ===================================================
echo Starting Edufeedia Services...
echo Backend:  http://127.0.0.1:8000 (API & Docs: /docs)
echo Frontend: http://localhost:3000
echo ===================================================

start "Edufeedia-Backend" "%~dp0venv\Scripts\python.exe" "%~dp0backend\server.py"
cd /d "%~dp0frontend"
start "Edufeedia-Frontend" cmd /c npm run dev

echo Servers launched successfully in dedicated console windows!
