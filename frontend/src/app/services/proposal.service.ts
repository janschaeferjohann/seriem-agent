import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of, tap, interval, switchMap } from 'rxjs';

export interface FileChange {
  path: string;
  operation: 'create' | 'update' | 'delete';
  before: string | null;
  after: string | null;
  lines_added: number;
  lines_removed: number;
}

export interface ProposalSummary {
  proposal_id: string;
  summary: string;
  file_count: number;
  lines_added: number;
  lines_removed: number;
  created_at: string;
}

export interface ProposalDetail {
  proposal_id: string;
  summary: string;
  files: FileChange[];
  created_at: string;
}

export interface ProposalResult {
  proposal_id: string;
  action: 'approved' | 'rejected';
  files_affected: string[];
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class ProposalService {
  private readonly apiUrl = 'http://localhost:8000/api/proposals';
  
  // Signals for reactive state
  readonly proposals = signal<ProposalSummary[]>([]);
  readonly selectedProposal = signal<ProposalDetail | null>(null);
  readonly isLoading = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly isReviewPanelOpen = signal<boolean>(false);
  readonly isReviewPanelCollapsed = signal<boolean>(false);
  
  // Computed values
  readonly pendingCount = computed(() => this.proposals().length);
  readonly hasProposals = computed(() => this.proposals().length > 0);
  
  // Polling subscription
  private pollingActive = false;
  
  constructor(private http: HttpClient) {
    // Start polling for proposals
    this.startPolling();
  }
  
  /**
   * Start polling for pending proposals
   */
  startPolling(intervalMs: number = 3000): void {
    if (this.pollingActive) return;
    this.pollingActive = true;
    
    // Initial load
    this.loadProposals();
    
    // Poll periodically
    interval(intervalMs).pipe(
      switchMap(() => this.fetchProposals())
    ).subscribe(proposals => {
      if (proposals) {
        const current = this.proposals();
        const hasChanges = proposals.length !== current.length ||
          proposals.some((p, i) => p.proposal_id !== current[i]?.proposal_id);
        
        if (hasChanges) {
          this.proposals.set(proposals);
          // Auto-open review panel if there are new proposals
          if (proposals.length > 0 && !this.isReviewPanelOpen()) {
            this.isReviewPanelOpen.set(true);
          }
        }
      }
    });
  }
  
  /**
   * Load all pending proposals
   */
  loadProposals(): void {
    this.isLoading.set(true);
    this.error.set(null);
    
    this.fetchProposals().subscribe(proposals => {
      if (proposals) {
        this.proposals.set(proposals);
      }
      this.isLoading.set(false);
    });
  }
  
  /**
   * Fetch proposals from API
   */
  private fetchProposals(): Observable<ProposalSummary[] | null> {
    return this.http.get<{ proposals: ProposalSummary[], total: number }>(`${this.apiUrl}/pending`).pipe(
      catchError(err => {
        console.error('Failed to fetch proposals:', err);
        return of(null);
      }),
      switchMap(response => of(response?.proposals ?? null))
    );
  }
  
  /**
   * Get detailed information about a specific proposal
   */
  loadProposalDetail(proposalId: string): void {
    this.isLoading.set(true);
    this.error.set(null);
    
    this.http.get<ProposalDetail>(`${this.apiUrl}/${proposalId}`).pipe(
      catchError(err => {
        this.error.set(err.error?.detail || 'Failed to load proposal');
        return of(null);
      })
    ).subscribe(proposal => {
      this.selectedProposal.set(proposal);
      this.isLoading.set(false);
    });
  }
  
  /**
   * Approve a proposal
   */
  approveProposal(proposalId: string, commit: boolean = false, commitMessage?: string): Observable<ProposalResult | null> {
    return this.http.post<ProposalResult>(`${this.apiUrl}/${proposalId}/approve`, {
      commit,
      commit_message: commitMessage,
    }).pipe(
      tap(() => {
        // Remove from local state
        this.proposals.update(list => list.filter(p => p.proposal_id !== proposalId));
        if (this.selectedProposal()?.proposal_id === proposalId) {
          this.selectedProposal.set(null);
        }
      }),
      catchError(err => {
        this.error.set(err.error?.detail || 'Failed to approve proposal');
        return of(null);
      })
    );
  }
  
  /**
   * Reject a proposal
   */
  rejectProposal(proposalId: string): Observable<ProposalResult | null> {
    return this.http.post<ProposalResult>(`${this.apiUrl}/${proposalId}/reject`, {}).pipe(
      tap(() => {
        // Remove from local state
        this.proposals.update(list => list.filter(p => p.proposal_id !== proposalId));
        if (this.selectedProposal()?.proposal_id === proposalId) {
          this.selectedProposal.set(null);
        }
      }),
      catchError(err => {
        this.error.set(err.error?.detail || 'Failed to reject proposal');
        return of(null);
      })
    );
  }
  
  /**
   * Clear all proposals
   */
  clearAll(): Observable<boolean> {
    return this.http.delete<{ cleared: number, message: string }>(`${this.apiUrl}/all`).pipe(
      tap(() => {
        this.proposals.set([]);
        this.selectedProposal.set(null);
      }),
      switchMap(() => of(true)),
      catchError(err => {
        this.error.set(err.error?.detail || 'Failed to clear proposals');
        return of(false);
      })
    );
  }
  
  /**
   * Toggle the review panel
   */
  toggleReviewPanel(): void {
    this.isReviewPanelOpen.update(open => !open);
    // Trigger resize after Angular re-renders to let Monaco adjust
    requestAnimationFrame(() => window.dispatchEvent(new Event('resize')));
  }
  
  /**
   * Open the review panel
   */
  openReviewPanel(): void {
    this.isReviewPanelOpen.set(true);
    requestAnimationFrame(() => window.dispatchEvent(new Event('resize')));
  }
  
  /**
   * Close the review panel
   */
  closeReviewPanel(): void {
    this.isReviewPanelOpen.set(false);
    this.isReviewPanelCollapsed.set(false);
    this.selectedProposal.set(null);
    requestAnimationFrame(() => window.dispatchEvent(new Event('resize')));
  }

  /**
   * Collapse the review panel to a thin bar
   */
  collapseReviewPanel(): void {
    this.isReviewPanelCollapsed.set(true);
    // Trigger resize after Angular re-renders
    requestAnimationFrame(() => window.dispatchEvent(new Event('resize')));
  }

  /**
   * Expand the review panel from collapsed state
   */
  expandReviewPanel(): void {
    this.isReviewPanelCollapsed.set(false);
    // Trigger resize after Angular re-renders
    requestAnimationFrame(() => window.dispatchEvent(new Event('resize')));
  }
}

