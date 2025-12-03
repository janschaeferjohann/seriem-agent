"""REST API routes for chat and file operations."""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from app.agents import get_agent_executor

router = APIRouter(prefix="/api")

# Storage root - default to project root's storage folder
_default_storage = Path(__file__).parent.parent.parent.parent / "storage"
STORAGE_ROOT = Path(os.getenv("STORAGE_PATH", str(_default_storage))).resolve()


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    chat_history: Optional[list] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    

class FileInfo(BaseModel):
    """File information model."""
    name: str
    path: str
    is_directory: bool
    size: Optional[int] = None


class FileListResponse(BaseModel):
    """Response model for file listing."""
    files: list[FileInfo]
    current_path: str


class FileContentResponse(BaseModel):
    """Response model for file content."""
    path: str
    content: str


def _safe_path(path: str) -> Path:
    """Resolve path safely within storage root."""
    resolved = (STORAGE_ROOT / path).resolve()
    if not str(resolved).startswith(str(STORAGE_ROOT)):
        raise HTTPException(status_code=400, detail="Invalid path")
    return resolved


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the agent and get a response."""
    try:
        agent = get_agent_executor()
        
        # Build messages list
        messages = []
        
        # Add chat history if provided
        if request.chat_history:
            for msg in request.chat_history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Add current message
        messages.append(HumanMessage(content=request.message))
        
        # Invoke the agent
        result = agent.invoke({"messages": messages})
        
        # Extract the final response
        final_message = result["messages"][-1]
        response_text = final_message.content if hasattr(final_message, 'content') else str(final_message)
        
        return ChatResponse(response=response_text)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files", response_model=FileListResponse)
async def list_files(path: str = ""):
    """List files in the storage directory."""
    try:
        target = _safe_path(path)
        
        # Ensure storage root exists
        STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
        
        if not target.exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        
        if not target.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        files = []
        for entry in sorted(target.iterdir()):
            rel_path = str(entry.relative_to(STORAGE_ROOT))
            files.append(FileInfo(
                name=entry.name,
                path=rel_path,
                is_directory=entry.is_dir(),
                size=entry.stat().st_size if entry.is_file() else None,
            ))
        
        return FileListResponse(
            files=files,
            current_path=path or "/",
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{path:path}", response_model=FileContentResponse)
async def read_file(path: str):
    """Read content of a file."""
    try:
        target = _safe_path(path)
        
        if not target.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not target.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        content = target.read_text(encoding="utf-8")
        
        return FileContentResponse(
            path=path,
            content=content,
        )
    
    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not a text file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
