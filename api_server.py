"""
API Server Entry Point

Run with: python api_server.py
Or with uvicorn: uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
"""

import uvicorn
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
