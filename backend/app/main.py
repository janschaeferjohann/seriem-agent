"""FastAPI application entry point."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.settings import router as settings_router
from app.api.websocket import websocket_endpoint
from app.proposals import proposals_router

# Load environment variables from backend/.env (explicit path for reliability)
_backend_dir = Path(__file__).parent.parent
_env_file = _backend_dir / ".env"
load_dotenv(_env_file)

# Debug: verify API key is loaded (prints at startup)
_api_key = os.getenv("ANTHROPIC_API_KEY")
if _api_key:
    # Check for common issues
    _stripped = _api_key.strip().strip('"').strip("'")
    if _stripped != _api_key:
        print(f"[!] WARNING: API key has extra whitespace or quotes!")
        print(f"  Raw length: {len(_api_key)}, Stripped length: {len(_stripped)}")
        print(f"  Raw repr: {repr(_api_key[:20])}...")
        # Use the cleaned version
        os.environ["ANTHROPIC_API_KEY"] = _stripped
        _api_key = _stripped
        print(f"  Fixed: using stripped key")
    print(f"[OK] ANTHROPIC_API_KEY loaded ({len(_api_key)} chars)")
    print(f"  Starts with: {_api_key[:15]}...")
    print(f"  Ends with: ...{_api_key[-10:]}")
else:
    print(f"[X] ANTHROPIC_API_KEY not found! Check {_env_file}")

# Ensure storage directory exists - default to project root's storage folder
_default_storage = Path(__file__).parent.parent.parent / "storage"
STORAGE_ROOT = Path(os.getenv("STORAGE_PATH", str(_default_storage))).resolve()
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="Seriem Agent API",
    description="API for the Seriem coding agent",
    version="0.1.0",
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST routes
app.include_router(router)
app.include_router(settings_router)
app.include_router(proposals_router)

# WebSocket endpoint
app.websocket("/ws/chat")(websocket_endpoint)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "seriem-agent"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

