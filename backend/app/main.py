import os
import sys

# Ensure backend directory is in sys.path for robust imports across all environments
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="SmartPay Payment Reconciliation Engine",
    description="Deterministic, explainable payment reconciliation between platform transactions and bank settlements.",
    version="1.0.0"
)

# Configure CORS via environment variable with safe local dev fallback
cors_env = os.getenv("CORS_ORIGINS", "")
if cors_env.strip():
    allowed_origins = [orig.strip() for orig in cors_env.split(",") if orig.strip()]
else:
    # Default development origins
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

# Do not combine wildcard with credentials to respect CORS specification
allow_all = "*" in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else allowed_origins,
    allow_credentials=not allow_all,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "smartpay-reconciliation",
        "version": "1.0.0",
        "mode": "deterministic_in_memory"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)

