"""FastAPI application entry point."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.websocket import websocket_endpoint

# Load environment variables
load_dotenv()

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

