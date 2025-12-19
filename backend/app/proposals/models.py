"""Pydantic models for change proposals."""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class OperationType(str, Enum):
    """Type of file operation."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class FileChange(BaseModel):
    """A single file change within a proposal."""
    path: str = Field(..., description="File path relative to workspace root")
    operation: OperationType = Field(..., description="Type of operation")
    before: Optional[str] = Field(None, description="Original content (None for create)")
    after: Optional[str] = Field(None, description="New content (None for delete)")
    
    @property
    def lines_added(self) -> int:
        """Count of lines added."""
        if self.after is None:
            return 0
        if self.before is None:
            return len(self.after.splitlines())
        # For updates, count net additions
        before_lines = set(self.before.splitlines())
        after_lines = self.after.splitlines()
        return sum(1 for line in after_lines if line not in before_lines)
    
    @property
    def lines_removed(self) -> int:
        """Count of lines removed."""
        if self.before is None:
            return 0
        if self.after is None:
            return len(self.before.splitlines())
        # For updates, count net removals
        after_lines = set(self.after.splitlines())
        before_lines = self.before.splitlines()
        return sum(1 for line in before_lines if line not in after_lines)


class ChangeProposal(BaseModel):
    """A proposal for one or more file changes."""
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    files: List[FileChange] = Field(default_factory=list)
    summary: str = Field("", description="Human-readable summary of changes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def file_count(self) -> int:
        """Number of files in this proposal."""
        return len(self.files)
    
    @property
    def total_lines_added(self) -> int:
        """Total lines added across all files."""
        return sum(f.lines_added for f in self.files)
    
    @property
    def total_lines_removed(self) -> int:
        """Total lines removed across all files."""
        return sum(f.lines_removed for f in self.files)


class ProposalSummary(BaseModel):
    """Summary view of a proposal for listing."""
    proposal_id: str
    summary: str
    file_count: int
    lines_added: int
    lines_removed: int
    created_at: datetime
    
    @classmethod
    def from_proposal(cls, proposal: ChangeProposal) -> "ProposalSummary":
        """Create summary from full proposal."""
        return cls(
            proposal_id=proposal.proposal_id,
            summary=proposal.summary,
            file_count=proposal.file_count,
            lines_added=proposal.total_lines_added,
            lines_removed=proposal.total_lines_removed,
            created_at=proposal.created_at,
        )


class ProposalResult(BaseModel):
    """Result of a proposal action (approve/reject)."""
    proposal_id: str
    action: str  # "approved" or "rejected"
    files_affected: List[str] = Field(default_factory=list)
    message: str = ""

