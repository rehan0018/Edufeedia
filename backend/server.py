import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import asyncio
import uvicorn
from app.main import app

async def main():
    print("Starting Edufeedia FastAPI Server on http://127.0.0.1:8000 ...")
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, log_level="info", loop="asyncio", http="h11")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
