"""Workspace manager for dynamic workspace selection."""

import os
import subprocess
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class Workspace(BaseModel):
    """Current workspace information."""
    root_path: str
    git_enabled: bool = False
    git_remote: Optional[str] = None
    git_branch: Optional[str] = None


class WorkspaceManager:
    """
    Manages the current workspace state.
    
    Singleton pattern - use get_workspace_manager() to access.
    """
    
    _instance: Optional["WorkspaceManager"] = None
    
    def __init__(self):
        # Default to ./storage in project root
        default_storage = Path(__file__).parent.parent.parent.parent / "storage"
        self._workspace_root: Path = Path(os.getenv("STORAGE_PATH", str(default_storage))).resolve()
        self._workspace_root.mkdir(parents=True, exist_ok=True)
        self._git_enabled: bool = False
        self._git_remote: Optional[str] = None
        self._git_branch: Optional[str] = None
        
        # Detect git on initialization
        self._detect_git()
    
    @property
    def root(self) -> Path:
        """Get the current workspace root path."""
        return self._workspace_root
    
    @property
    def git_enabled(self) -> bool:
        """Check if git is enabled for current workspace."""
        return self._git_enabled
    
    @property
    def git_remote(self) -> Optional[str]:
        """Get the git remote URL if available."""
        return self._git_remote
    
    @property
    def git_branch(self) -> Optional[str]:
        """Get the current git branch if available."""
        return self._git_branch
    
    def select_workspace(self, path: str) -> Workspace:
        """
        Select a new workspace directory.
        
        Args:
            path: Absolute path to the workspace directory
            
        Returns:
            Workspace object with current state
            
        Raises:
            ValueError: If path is invalid or doesn't exist
        """
        resolved = Path(path).resolve()
        
        # Validate path
        if not resolved.exists():
            raise ValueError(f"Path does not exist: {path}")
        
        if not resolved.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        # Check for path traversal attacks
        try:
            # Ensure the path is absolute and normalized
            resolved = resolved.resolve()
        except Exception as e:
            raise ValueError(f"Invalid path: {e}")
        
        # Update workspace root
        self._workspace_root = resolved
        
        # Detect git repository
        self._detect_git()
        
        return self.get_current()
    
    def get_current(self) -> Workspace:
        """Get the current workspace information."""
        return Workspace(
            root_path=str(self._workspace_root),
            git_enabled=self._git_enabled,
            git_remote=self._git_remote,
            git_branch=self._git_branch,
        )
    
    def _detect_git(self) -> None:
        """Detect if the current workspace is a git repository."""
        git_dir = self._workspace_root / ".git"
        self._git_enabled = git_dir.exists() and git_dir.is_dir()
        self._git_remote = None
        self._git_branch = None
        
        if self._git_enabled:
            # Try to get remote URL
            try:
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=self._workspace_root,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    self._git_remote = result.stdout.strip()
            except Exception:
                pass
            
            # Try to get current branch
            try:
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=self._workspace_root,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    self._git_branch = result.stdout.strip()
            except Exception:
                pass
    
    def safe_path(self, relative_path: str) -> Path:
        """
        Resolve a path safely within the workspace root.
        
        Args:
            relative_path: Path relative to workspace root
            
        Returns:
            Resolved absolute path
            
        Raises:
            ValueError: If path escapes workspace root
        """
        # Handle empty path
        if not relative_path or relative_path == "/":
            return self._workspace_root
        
        # Remove leading slashes
        clean_path = relative_path.lstrip("/\\")
        
        # Resolve the path
        resolved = (self._workspace_root / clean_path).resolve()
        
        # Check it's still within workspace
        try:
            resolved.relative_to(self._workspace_root)
        except ValueError:
            raise ValueError(f"Path escapes workspace root: {relative_path}")
        
        return resolved


# Singleton instance
_workspace_manager: Optional[WorkspaceManager] = None


def get_workspace_manager() -> WorkspaceManager:
    """Get the singleton workspace manager instance."""
    global _workspace_manager
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManager()
    return _workspace_manager

