"""Proposal management module for change review workflow."""

from .models import (
    FileChange,
    ChangeProposal,
    ProposalSummary,
    OperationType,
)
from .store import (
    ProposalStore,
    get_proposal_store,
)
from .routes import router as proposals_router

__all__ = [
    "FileChange",
    "ChangeProposal",
    "ProposalSummary",
    "OperationType",
    "ProposalStore",
    "get_proposal_store",
    "proposals_router",
]

