"""API routes for proposal management."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.workspace import get_workspace_manager
from app.telemetry import get_telemetry_client
from .models import ChangeProposal, ProposalSummary, ProposalResult, FileChange
from .store import get_proposal_store

router = APIRouter(prefix="/api/proposals", tags=["proposals"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ApproveRequest(BaseModel):
    """Request model for approving a proposal."""
    commit: bool = False
    commit_message: Optional[str] = None


class ProposalListResponse(BaseModel):
    """Response model for listing proposals."""
    proposals: List[ProposalSummary]
    total: int


class FileChangeResponse(BaseModel):
    """Response model for a file change."""
    path: str
    operation: str
    before: Optional[str]
    after: Optional[str]
    lines_added: int
    lines_removed: int


class ProposalDetailResponse(BaseModel):
    """Response model for proposal details."""
    proposal_id: str
    summary: str
    files: List[FileChangeResponse]
    created_at: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/pending", response_model=ProposalListResponse)
async def list_pending_proposals():
    """
    List all pending proposals.
    
    Returns summaries of proposals awaiting approval.
    """
    store = get_proposal_store()
    proposals = store.list_pending()
    
    return ProposalListResponse(
        proposals=proposals,
        total=len(proposals),
    )


@router.get("/count")
async def get_proposal_count():
    """Get the count of pending proposals."""
    store = get_proposal_store()
    return {"count": store.count}


@router.get("/{proposal_id}", response_model=ProposalDetailResponse)
async def get_proposal(proposal_id: str):
    """
    Get detailed information about a specific proposal.
    
    Includes full file contents for diff display.
    """
    store = get_proposal_store()
    proposal = store.get(proposal_id)
    
    if proposal is None:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")
    
    files = [
        FileChangeResponse(
            path=f.path,
            operation=f.operation.value,
            before=f.before,
            after=f.after,
            lines_added=f.lines_added,
            lines_removed=f.lines_removed,
        )
        for f in proposal.files
    ]
    
    return ProposalDetailResponse(
        proposal_id=proposal.proposal_id,
        summary=proposal.summary,
        files=files,
        created_at=proposal.created_at.isoformat(),
    )


@router.post("/{proposal_id}/approve", response_model=ProposalResult)
async def approve_proposal(proposal_id: str, request: ApproveRequest = ApproveRequest()):
    """
    Approve a proposal and apply the changes to the filesystem.
    
    Optionally commits the changes if the workspace is a git repository.
    """
    store = get_proposal_store()
    workspace = get_workspace_manager()
    
    proposal = store.get(proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")
    
    # Apply changes
    files_affected = []
    try:
        for file_change in proposal.files:
            target_path = workspace.safe_path(file_change.path)
            
            if file_change.operation.value == "delete":
                if target_path.exists():
                    target_path.unlink()
                    files_affected.append(file_change.path)
            else:
                # Create or update
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if file_change.after is not None:
                    target_path.write_text(file_change.after, encoding="utf-8")
                    files_affected.append(file_change.path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply changes: {str(e)}"
        )
    
    # Handle git commit if requested
    if request.commit and workspace.git_enabled:
        try:
            import subprocess
            
            # Stage the affected files
            for path in files_affected:
                subprocess.run(
                    ["git", "add", path],
                    cwd=workspace.root,
                    capture_output=True,
                    timeout=10,
                )
            
            # Commit
            message = request.commit_message or proposal.summary or f"Applied proposal {proposal_id}"
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=workspace.root,
                capture_output=True,
                timeout=30,
            )
        except Exception as e:
            # Log but don't fail - changes are already applied
            print(f"Git commit failed: {e}")
    
    # Remove from pending
    store.remove(proposal_id)
    
    # Emit telemetry for proposal approval
    telemetry = get_telemetry_client()
    if telemetry:
        telemetry.emit_proposal_decision(
            proposal_id=proposal_id,
            decision="approved",
        )
    
    return ProposalResult(
        proposal_id=proposal_id,
        action="approved",
        files_affected=files_affected,
        message=f"Applied {len(files_affected)} file(s)",
    )


@router.post("/{proposal_id}/reject", response_model=ProposalResult)
async def reject_proposal(proposal_id: str):
    """
    Reject a proposal and discard the changes.
    """
    store = get_proposal_store()
    
    proposal = store.remove(proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")
    
    # Emit telemetry for proposal rejection
    telemetry = get_telemetry_client()
    if telemetry:
        telemetry.emit_proposal_decision(
            proposal_id=proposal_id,
            decision="rejected",
        )
    
    return ProposalResult(
        proposal_id=proposal_id,
        action="rejected",
        files_affected=[f.path for f in proposal.files],
        message=f"Discarded {len(proposal.files)} file change(s)",
    )


@router.delete("/all")
async def clear_all_proposals():
    """
    Clear all pending proposals.
    
    Use with caution - this cannot be undone.
    """
    store = get_proposal_store()
    count = store.clear()
    
    return {"cleared": count, "message": f"Cleared {count} proposal(s)"}

