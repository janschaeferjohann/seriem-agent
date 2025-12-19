"""REST API routes for chat and file operations."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from app.agents import get_agent_executor
from app.workspace import get_workspace_manager, Workspace

router = APIRouter(prefix="/api")


# ============================================================================
# Request/Response Models
# ============================================================================

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


class WorkspaceSelectRequest(BaseModel):
    """Request model for workspace selection."""
    path: str


class WorkspaceResponse(BaseModel):
    """Response model for workspace info."""
    root_path: str
    git_enabled: bool
    git_remote: Optional[str] = None
    git_branch: Optional[str] = None


def _safe_path(path: str) -> Path:
    """Resolve path safely within workspace root."""
    workspace = get_workspace_manager()
    try:
        return workspace.safe_path(path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Workspace Endpoints
# ============================================================================

@router.post("/workspace/select", response_model=WorkspaceResponse)
async def select_workspace(request: WorkspaceSelectRequest):
    """
    Select a workspace directory.
    
    This changes the root directory for all file operations.
    """
    try:
        workspace = get_workspace_manager()
        result = workspace.select_workspace(request.path)
        return WorkspaceResponse(
            root_path=result.root_path,
            git_enabled=result.git_enabled,
            git_remote=result.git_remote,
            git_branch=result.git_branch,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/current", response_model=WorkspaceResponse)
async def get_current_workspace():
    """Get the current workspace information."""
    workspace = get_workspace_manager()
    result = workspace.get_current()
    return WorkspaceResponse(
        root_path=result.root_path,
        git_enabled=result.git_enabled,
        git_remote=result.git_remote,
        git_branch=result.git_branch,
    )


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
    """List files in the workspace directory."""
    try:
        workspace = get_workspace_manager()
        target = _safe_path(path)
        
        # Ensure workspace root exists
        workspace.root.mkdir(parents=True, exist_ok=True)
        
        if not target.exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        
        if not target.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        files = []
        for entry in sorted(target.iterdir()):
            rel_path = str(entry.relative_to(workspace.root))
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
