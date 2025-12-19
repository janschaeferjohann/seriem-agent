"""API endpoints for workspace settings management."""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.workspace import get_workspace_manager


router = APIRouter(prefix="/api/settings")


# ============================================================================
# Request/Response Models
# ============================================================================

class GitCredentialsOverride(BaseModel):
    """Git credentials for workspace override."""
    username: str
    token: str


class WorkspaceSettings(BaseModel):
    """Workspace-specific settings stored in .seriem/settings.json"""
    use_global_git_credentials: bool = True
    git_credentials_override: Optional[GitCredentialsOverride] = None


class WorkspaceSettingsResponse(BaseModel):
    """Response for workspace settings."""
    settings: WorkspaceSettings
    workspace_path: str
    settings_file_exists: bool


class GitStatusResponse(BaseModel):
    """Response for git status check."""
    is_git_repo: bool
    remote_url: Optional[str] = None
    current_branch: Optional[str] = None
    workspace_path: str


# ============================================================================
# Settings File Management
# ============================================================================

def _get_settings_file_path() -> Path:
    """Get the path to the workspace settings file."""
    workspace = get_workspace_manager()
    return workspace.root / ".seriem" / "settings.json"


def _load_workspace_settings() -> WorkspaceSettings:
    """Load workspace settings from .seriem/settings.json"""
    settings_path = _get_settings_file_path()
    
    if not settings_path.exists():
        return WorkspaceSettings()
    
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return WorkspaceSettings(**data)
    except (json.JSONDecodeError, ValueError) as e:
        # Return defaults if file is corrupted
        print(f"Warning: Could not parse workspace settings: {e}")
        return WorkspaceSettings()


def _save_workspace_settings(settings: WorkspaceSettings) -> None:
    """Save workspace settings to .seriem/settings.json"""
    settings_path = _get_settings_file_path()
    
    # Create .seriem directory if it doesn't exist
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save settings
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings.model_dump(exclude_none=True), f, indent=2)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/workspace", response_model=WorkspaceSettingsResponse)
async def get_workspace_settings():
    """
    Get workspace-specific settings.
    
    Returns settings from {workspace_root}/.seriem/settings.json
    """
    workspace = get_workspace_manager()
    settings = _load_workspace_settings()
    settings_path = _get_settings_file_path()
    
    return WorkspaceSettingsResponse(
        settings=settings,
        workspace_path=str(workspace.root),
        settings_file_exists=settings_path.exists(),
    )


@router.put("/workspace", response_model=WorkspaceSettingsResponse)
async def update_workspace_settings(settings: WorkspaceSettings):
    """
    Update workspace-specific settings.
    
    Saves settings to {workspace_root}/.seriem/settings.json
    """
    try:
        _save_workspace_settings(settings)
        workspace = get_workspace_manager()
        settings_path = _get_settings_file_path()
        
        return WorkspaceSettingsResponse(
            settings=settings,
            workspace_path=str(workspace.root),
            settings_file_exists=settings_path.exists(),
        )
    except PermissionError:
        raise HTTPException(
            status_code=403, 
            detail="Cannot write to workspace settings - permission denied"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/git/status", response_model=GitStatusResponse)
async def get_git_status():
    """
    Check if current workspace is a git repository.
    
    Returns git status including remote URL and current branch.
    """
    workspace = get_workspace_manager()
    
    return GitStatusResponse(
        is_git_repo=workspace.git_enabled,
        remote_url=workspace.git_remote,
        current_branch=workspace.git_branch,
        workspace_path=str(workspace.root),
    )

