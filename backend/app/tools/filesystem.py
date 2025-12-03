"""Filesystem tools for the agent to interact with local storage."""

import os
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

# Storage root - all operations are relative to this
# Default to ../storage (project root's storage folder when running from backend/)
_default_storage = Path(__file__).parent.parent.parent.parent / "storage"
STORAGE_ROOT = Path(os.getenv("STORAGE_PATH", str(_default_storage))).resolve()


def _safe_path(path: str) -> Path:
    """Resolve path safely within storage root."""
    # Normalize and resolve the path
    resolved = (STORAGE_ROOT / path).resolve()
    
    # Ensure it's within storage root (prevent directory traversal)
    if not str(resolved).startswith(str(STORAGE_ROOT)):
        raise ValueError(f"Path '{path}' is outside storage directory")
    
    return resolved


@tool
def ls(path: str = ".") -> str:
    """List directory contents.
    
    Args:
        path: Directory path relative to storage root. Defaults to root.
        
    Returns:
        Formatted listing of files and directories.
    """
    try:
        target = _safe_path(path)
        
        if not target.exists():
            return f"Error: Directory '{path}' does not exist"
        
        if not target.is_dir():
            return f"Error: '{path}' is not a directory"
        
        entries = []
        for entry in sorted(target.iterdir()):
            if entry.is_dir():
                entries.append(f"[DIR]  {entry.name}/")
            else:
                size = entry.stat().st_size
                entries.append(f"[FILE] {entry.name} ({size} bytes)")
        
        if not entries:
            return f"Directory '{path}' is empty"
        
        return "\n".join(entries)
    
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error listing directory: {e}"


@tool
def read_file(path: str) -> str:
    """Read the contents of a file.
    
    Args:
        path: File path relative to storage root.
        
    Returns:
        File contents as string.
    """
    try:
        target = _safe_path(path)
        
        if not target.exists():
            return f"Error: File '{path}' does not exist"
        
        if not target.is_file():
            return f"Error: '{path}' is not a file"
        
        content = target.read_text(encoding="utf-8")
        return content if content else "(empty file)"
    
    except ValueError as e:
        return f"Error: {e}"
    except UnicodeDecodeError:
        return f"Error: File '{path}' is not a text file"
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates the file if it doesn't exist, overwrites if it does.
    
    Args:
        path: File path relative to storage root.
        content: Content to write to the file.
        
    Returns:
        Success or error message.
    """
    try:
        target = _safe_path(path)
        
        # Create parent directories if needed
        target.parent.mkdir(parents=True, exist_ok=True)
        
        target.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} bytes to '{path}'"
    
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def edit_file(path: str, old_str: str, new_str: str) -> str:
    """Edit a file by replacing a string. The old_str must match exactly.
    
    Args:
        path: File path relative to storage root.
        old_str: The exact string to find and replace.
        new_str: The string to replace it with.
        
    Returns:
        Success or error message.
    """
    try:
        target = _safe_path(path)
        
        if not target.exists():
            return f"Error: File '{path}' does not exist"
        
        if not target.is_file():
            return f"Error: '{path}' is not a file"
        
        content = target.read_text(encoding="utf-8")
        
        if old_str not in content:
            return f"Error: Could not find the specified text in '{path}'"
        
        # Count occurrences
        count = content.count(old_str)
        if count > 1:
            return f"Error: Found {count} occurrences of the text. Please provide more context to make it unique."
        
        # Perform replacement
        new_content = content.replace(old_str, new_str)
        target.write_text(new_content, encoding="utf-8")
        
        return f"Successfully edited '{path}'"
    
    except ValueError as e:
        return f"Error: {e}"
    except UnicodeDecodeError:
        return f"Error: File '{path}' is not a text file"
    except Exception as e:
        return f"Error editing file: {e}"


@tool
def delete_file(path: str) -> str:
    """Delete a file from storage.
    
    Args:
        path: File path relative to storage root.
        
    Returns:
        Success or error message.
    """
    try:
        target = _safe_path(path)
        
        if not target.exists():
            return f"Error: File '{path}' does not exist"
        
        if not target.is_file():
            return f"Error: '{path}' is not a file. Use delete_directory for directories."
        
        target.unlink()
        return f"Successfully deleted file '{path}'"
    
    except ValueError as e:
        return f"Error: {e}"
    except PermissionError:
        return f"Error: Permission denied to delete '{path}'"
    except Exception as e:
        return f"Error deleting file: {e}"


@tool
def delete_directory(path: str, recursive: bool = False) -> str:
    """Delete a directory from storage.
    
    Args:
        path: Directory path relative to storage root.
        recursive: If True, delete directory and all contents. If False, only delete if empty.
        
    Returns:
        Success or error message.
    """
    import shutil
    
    try:
        target = _safe_path(path)
        
        if not target.exists():
            return f"Error: Directory '{path}' does not exist"
        
        if not target.is_dir():
            return f"Error: '{path}' is not a directory. Use delete_file for files."
        
        # Prevent deleting the storage root itself
        if target == STORAGE_ROOT:
            return "Error: Cannot delete the storage root directory"
        
        if recursive:
            shutil.rmtree(target)
            return f"Successfully deleted directory '{path}' and all its contents"
        else:
            # Check if directory is empty
            if any(target.iterdir()):
                return f"Error: Directory '{path}' is not empty. Set recursive=True to delete with contents."
            target.rmdir()
            return f"Successfully deleted empty directory '{path}'"
    
    except ValueError as e:
        return f"Error: {e}"
    except PermissionError:
        return f"Error: Permission denied to delete '{path}'"
    except Exception as e:
        return f"Error deleting directory: {e}"
