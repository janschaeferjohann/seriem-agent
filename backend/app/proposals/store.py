"""In-memory store for pending proposals."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Lock

from .models import ChangeProposal, FileChange, OperationType, ProposalSummary


class ProposalStore:
    """
    Thread-safe in-memory store for pending change proposals.
    
    Singleton pattern - use get_proposal_store() to access.
    """
    
    _instance: Optional["ProposalStore"] = None
    
    def __init__(self):
        self._proposals: Dict[str, ChangeProposal] = {}
        self._lock = Lock()
        # Auto-expire proposals after 1 hour
        self._expiry_hours = 1
    
    def create_proposal(
        self,
        path: str,
        operation: OperationType,
        before: Optional[str],
        after: Optional[str],
        summary: str = ""
    ) -> ChangeProposal:
        """
        Create a new proposal with a single file change.
        
        Args:
            path: File path relative to workspace
            operation: Type of operation
            before: Original content (None for create)
            after: New content (None for delete)
            summary: Human-readable summary
            
        Returns:
            The created proposal
        """
        file_change = FileChange(
            path=path,
            operation=operation,
            before=before,
            after=after,
        )
        
        # Generate summary if not provided
        if not summary:
            summary = self._generate_summary(file_change)
        
        proposal = ChangeProposal(
            files=[file_change],
            summary=summary,
        )
        
        with self._lock:
            self._proposals[proposal.proposal_id] = proposal
        
        return proposal
    
    def add_file_to_proposal(
        self,
        proposal_id: str,
        path: str,
        operation: OperationType,
        before: Optional[str],
        after: Optional[str],
    ) -> Optional[ChangeProposal]:
        """
        Add a file change to an existing proposal.
        
        Returns:
            Updated proposal or None if not found
        """
        file_change = FileChange(
            path=path,
            operation=operation,
            before=before,
            after=after,
        )
        
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if proposal is None:
                return None
            
            proposal.files.append(file_change)
            return proposal
    
    def get(self, proposal_id: str) -> Optional[ChangeProposal]:
        """Get a proposal by ID."""
        with self._lock:
            return self._proposals.get(proposal_id)
    
    def list_pending(self) -> List[ProposalSummary]:
        """List all pending proposals as summaries."""
        self._cleanup_expired()
        
        with self._lock:
            return [
                ProposalSummary.from_proposal(p)
                for p in sorted(
                    self._proposals.values(),
                    key=lambda x: x.created_at,
                    reverse=True
                )
            ]
    
    def remove(self, proposal_id: str) -> Optional[ChangeProposal]:
        """
        Remove and return a proposal.
        
        Returns:
            The removed proposal or None if not found
        """
        with self._lock:
            return self._proposals.pop(proposal_id, None)
    
    def clear(self) -> int:
        """
        Clear all proposals.
        
        Returns:
            Number of proposals cleared
        """
        with self._lock:
            count = len(self._proposals)
            self._proposals.clear()
            return count
    
    @property
    def count(self) -> int:
        """Number of pending proposals."""
        with self._lock:
            return len(self._proposals)
    
    def _cleanup_expired(self) -> None:
        """Remove expired proposals."""
        cutoff = datetime.utcnow() - timedelta(hours=self._expiry_hours)
        
        with self._lock:
            expired = [
                pid for pid, p in self._proposals.items()
                if p.created_at < cutoff
            ]
            for pid in expired:
                del self._proposals[pid]
    
    def _generate_summary(self, file_change: FileChange) -> str:
        """Generate a summary for a single file change."""
        op = file_change.operation.value.capitalize()
        return f"{op} {file_change.path}"


# Singleton instance
_proposal_store: Optional[ProposalStore] = None


def get_proposal_store() -> ProposalStore:
    """Get the singleton proposal store instance."""
    global _proposal_store
    if _proposal_store is None:
        _proposal_store = ProposalStore()
    return _proposal_store

