"""Filesystem tools for the agent to interact with local storage.

Write operations create proposals that must be approved by the user
before changes are applied to the filesystem.
"""

from pathlib import Path

from langchain_core.tools import tool

from app.workspace import get_workspace_manager
from app.proposals import get_proposal_store, OperationType


def _safe_path(path: str) -> Path:
    """Resolve path safely within workspace root."""
    workspace = get_workspace_manager()
    return workspace.safe_path(path)


def _get_workspace_root() -> Path:
    """Get the current workspace root path."""
    return get_workspace_manager().root


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
    
    NOTE: This creates a proposal that must be approved by the user before
    the changes are applied to the filesystem.
    
    Args:
        path: File path relative to workspace root.
        content: Content to write to the file.
        
    Returns:
        Confirmation that a proposal was created, pending user approval.
    """
    try:
        target = _safe_path(path)
        store = get_proposal_store()
        
        # Determine operation type and get existing content
        if target.exists() and target.is_file():
            try:
                before = target.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                return f"Error: Cannot modify '{path}' - it is not a text file"
            operation = OperationType.UPDATE
        else:
            before = None
            operation = OperationType.CREATE
        
        # Create proposal
        proposal = store.create_proposal(
            path=path,
            operation=operation,
            before=before,
            after=content,
        )
        
        op_verb = "Update" if operation == OperationType.UPDATE else "Create"
        return (
            f"Proposed {op_verb.lower()} to '{path}' "
            f"(proposal_id: {proposal.proposal_id}). "
            f"Awaiting user approval."
        )
    
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error creating proposal: {e}"


@tool
def edit_file(path: str, old_str: str, new_str: str) -> str:
    """Edit a file by replacing a string. The old_str must match exactly.
    
    NOTE: This creates a proposal that must be approved by the user before
    the changes are applied to the filesystem.
    
    Args:
        path: File path relative to workspace root.
        old_str: The exact string to find and replace.
        new_str: The string to replace it with.
        
    Returns:
        Confirmation that a proposal was created, pending user approval.
    """
    try:
        target = _safe_path(path)
        store = get_proposal_store()
        
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
        
        # Compute new content
        new_content = content.replace(old_str, new_str)
        
        # Create proposal
        proposal = store.create_proposal(
            path=path,
            operation=OperationType.UPDATE,
            before=content,
            after=new_content,
            summary=f"Edit {path}: replace text",
        )
        
        return (
            f"Proposed edit to '{path}' "
            f"(proposal_id: {proposal.proposal_id}). "
            f"Awaiting user approval."
        )
    
    except ValueError as e:
        return f"Error: {e}"
    except UnicodeDecodeError:
        return f"Error: File '{path}' is not a text file"
    except Exception as e:
        return f"Error creating proposal: {e}"


@tool
def delete_file(path: str) -> str:
    """Delete a file from the workspace.
    
    NOTE: This creates a proposal that must be approved by the user before
    the file is actually deleted.
    
    Args:
        path: File path relative to workspace root.
        
    Returns:
        Confirmation that a proposal was created, pending user approval.
    """
    try:
        target = _safe_path(path)
        store = get_proposal_store()
        
        if not target.exists():
            return f"Error: File '{path}' does not exist"
        
        if not target.is_file():
            return f"Error: '{path}' is not a file. Use delete_directory for directories."
        
        # Get current content for the proposal
        try:
            content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = "(binary file)"
        
        # Create proposal
        proposal = store.create_proposal(
            path=path,
            operation=OperationType.DELETE,
            before=content,
            after=None,
        )
        
        return (
            f"Proposed deletion of '{path}' "
            f"(proposal_id: {proposal.proposal_id}). "
            f"Awaiting user approval."
        )
    
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error creating proposal: {e}"


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
        
        # Prevent deleting the workspace root itself
        if target == _get_workspace_root():
            return "Error: Cannot delete the workspace root directory"
        
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
