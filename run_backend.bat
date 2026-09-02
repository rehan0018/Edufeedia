@echo off
cd /d "c:\Users\Rehan Shaikh\Downloads\web dev\projects\edufeedia"
set PYTHONPATH=backend
"c:\Users\Rehan Shaikh\Downloads\web dev\projects\edufeedia\venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir "c:\Users\Rehan Shaikh\Downloads\web dev\projects\edufeedia\backend" --host 127.0.0.1 --port 8000 --loop asyncio --http h11
