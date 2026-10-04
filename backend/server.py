import sys
import os

# Ensure _asyncio is disabled on Windows Python 3.14 to use stable pure-Python asyncio
if sys.platform == "win32":
    sys.modules["_asyncio"] = None

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("Starting Edufeedia FastAPI Server on http://127.0.0.1:8000 ...", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info", loop="asyncio", http="h11")
