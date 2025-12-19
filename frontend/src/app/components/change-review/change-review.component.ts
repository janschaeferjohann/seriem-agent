import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { ProposalService, ProposalSummary } from '../../services/proposal.service';
import { FileService } from '../../services/file.service';
import { FilePreviewService } from '../../services/file-preview.service';

@Component({
  selector: 'app-change-review',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="change-review-panel" [class.open]="proposalService.isReviewPanelOpen()">
      <!-- Panel Header -->
      <div class="panel-header">
        <div class="header-left">
          <mat-icon>rate_review</mat-icon>
          <span class="header-title">Pending Changes</span>
          @if (proposalService.pendingCount() > 0) {
            <span class="badge">{{ proposalService.pendingCount() }}</span>
          }
        </div>
        <div class="header-actions">
          <button mat-icon-button 
                  matTooltip="Refresh"
                  (click)="refresh()"
                  [disabled]="proposalService.isLoading()">
            <mat-icon>refresh</mat-icon>
          </button>
          <button mat-icon-button 
                  matTooltip="Collapse panel"
                  (click)="collapsePanel()">
            <mat-icon>chevron_right</mat-icon>
          </button>
          <button mat-icon-button 
                  matTooltip="Close panel"
                  (click)="closePanel()">
            <mat-icon>close</mat-icon>
          </button>
        </div>
      </div>
      
      @if (proposalService.isLoading() && proposalService.proposals().length === 0) {
        <div class="loading">
          <mat-spinner diameter="24"></mat-spinner>
          <span>Loading proposals...</span>
        </div>
      }
      
      @if (proposalService.error()) {
        <div class="error-message">
          <mat-icon>error_outline</mat-icon>
          <span>{{ proposalService.error() }}</span>
        </div>
      }
      
      <div class="panel-content">
        <div class="proposal-list">
          @for (proposal of proposalService.proposals(); track proposal.proposal_id) {
            <div class="proposal-item">
              <div class="proposal-info">
                <div class="proposal-header">
                  <mat-icon class="operation-icon update">edit</mat-icon>
                  <span class="proposal-text">{{ proposal.summary }}</span>
                </div>
                <div class="proposal-meta">
                  <span class="proposal-id">#{{ proposal.proposal_id.slice(0, 8) }}</span>
                  <span class="stat files">{{ proposal.file_count }} file(s)</span>
                  <span class="stat additions">+{{ proposal.lines_added }}</span>
                  <span class="stat deletions">-{{ proposal.lines_removed }}</span>
                </div>
              </div>
              <div class="proposal-actions">
                <button class="action-btn view"
                        matTooltip="View diff"
                        (click)="viewProposal(proposal)"
                        [disabled]="isProcessing">
                  <mat-icon>visibility</mat-icon>
                </button>
                <button class="action-btn reject"
                        matTooltip="Reject"
                        (click)="rejectProposal(proposal.proposal_id)"
                        [disabled]="isProcessing">
                  <mat-icon>close</mat-icon>
                </button>
                <button class="action-btn approve"
                        matTooltip="Approve"
                        (click)="approveProposal(proposal.proposal_id)"
                        [disabled]="isProcessing">
                  <mat-icon>check</mat-icon>
                </button>
              </div>
            </div>
          } @empty {
            @if (!proposalService.isLoading()) {
              <div class="empty-state">
                <mat-icon>check_circle</mat-icon>
                <span>No pending changes</span>
              </div>
            }
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .change-review-panel {
      display: flex;
      flex-direction: column;
      width: 100%;
      height: 100%;
      background: var(--bg-secondary);
      border-left: 1px solid var(--border-default);
    }
    
    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 6px var(--spacing-md);
      border-bottom: 1px solid var(--border-default);
      height: 36px;
      flex-shrink: 0;
    }
    
    .header-left {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      
      mat-icon {
        color: var(--accent-primary);
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
    }
    
    .header-title {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-secondary);
    }
    
    .badge {
      background: var(--accent-primary);
      color: white;
      font-size: 10px;
      font-weight: 600;
      padding: 1px 5px;
      border-radius: 8px;
      min-width: 16px;
      text-align: center;
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: 2px;
      
      button {
        width: 24px;
        height: 24px;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        
        mat-icon {
          font-size: 16px;
          width: 16px;
          height: 16px;
          line-height: 16px;
        }
      }
    }
    
    .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--spacing-md);
      padding: var(--spacing-xl);
      color: var(--text-secondary);
    }
    
    .error-message {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-md);
      background: rgba(239, 68, 68, 0.1);
      color: var(--accent-error);
      font-size: 13px;
      
      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }
    }
    
    .panel-content {
      flex: 1;
      overflow-y: auto;
      padding: var(--spacing-sm);
    }
    
    .proposal-list {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
    }
    
    .proposal-item {
      padding: var(--spacing-sm) var(--spacing-md);
      background: var(--bg-tertiary);
      border: 1px solid var(--border-default);
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
    }
    
    .proposal-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
      flex: 1;
      min-width: 0;
    }
    
    .proposal-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
    }
    
    .proposal-text {
      font-size: 12px;
      font-weight: 500;
      color: var(--text-primary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .proposal-meta {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      font-size: 10px;
    }
    
    .proposal-id {
      font-family: var(--font-mono);
      color: var(--text-muted);
    }
    
    .stat {
      &.files { color: var(--text-secondary); }
      &.additions { color: var(--accent-secondary); }
      &.deletions { color: var(--accent-error); }
    }
    
    .proposal-actions {
      display: flex;
      gap: 4px;
      margin-left: auto;
    }
    
    .action-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      padding: 0;
      border: none;
      border-radius: var(--radius-sm);
      background: transparent;
      color: var(--text-muted);
      cursor: pointer;
      transition: all var(--transition-fast);
      
      mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
      
      &:hover:not(:disabled) {
        background: var(--bg-hover);
        color: var(--text-primary);
      }
      
      &:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }
      
      &.view:hover:not(:disabled) {
        color: var(--text-primary);
      }
      
      &.reject:hover:not(:disabled) {
        color: var(--accent-error);
        background: rgba(239, 68, 68, 0.1);
      }
      
      &.approve:hover:not(:disabled) {
        color: var(--accent-secondary);
        background: rgba(34, 197, 94, 0.1);
      }
    }
    
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: var(--spacing-xl);
      text-align: center;
      color: var(--text-muted);
      
      mat-icon {
        font-size: 32px;
        width: 32px;
        height: 32px;
        margin-bottom: var(--spacing-sm);
        color: var(--accent-secondary);
      }
      
      span {
        font-size: 13px;
      }
    }
    
    .operation-icon {
      font-size: 14px;
      width: 14px;
      height: 14px;
      
      &.create { color: var(--accent-secondary); }
      &.update { color: var(--accent-warning); }
      &.delete { color: var(--accent-error); }
    }
  `]
})
export class ChangeReviewComponent implements OnInit {
  isProcessing = false;
  
  constructor(
    public proposalService: ProposalService,
    private fileService: FileService,
    private filePreviewService: FilePreviewService,
  ) {}
  
  ngOnInit(): void {
    this.proposalService.loadProposals();
  }
  
  refresh(): void {
    this.proposalService.loadProposals();
  }
  
  closePanel(): void {
    this.proposalService.closeReviewPanel();
  }
  
  collapsePanel(): void {
    this.proposalService.collapseReviewPanel();
  }
  
  /**
   * Open the proposal diff in the file preview area
   */
  viewProposal(proposal: ProposalSummary): void {
    // Load full proposal details, then open in preview
    this.proposalService.loadProposalDetail(proposal.proposal_id);
    
    // Subscribe to get the full proposal and open diff
    const checkAndOpen = () => {
      const fullProposal = this.proposalService.selectedProposal();
      if (fullProposal && fullProposal.proposal_id === proposal.proposal_id && fullProposal.files) {
        // Open first file's diff in preview
        if (fullProposal.files.length > 0) {
          const file = fullProposal.files[0];
          this.filePreviewService.openDiff(
            file.path,
            file.before || '',
            file.after || '',
            proposal.proposal_id
          );
        }
      } else {
        // Wait a bit and check again
        setTimeout(checkAndOpen, 100);
      }
    };
    setTimeout(checkAndOpen, 50);
  }
  
  approveProposal(proposalId: string): void {
    this.isProcessing = true;
    this.proposalService.approveProposal(proposalId, false).subscribe({
      next: (result) => {
        this.isProcessing = false;
        if (result) {
          // Close diff tab if open for this proposal
          this.filePreviewService.closeDiffForProposal(proposalId);
          // Refresh file explorer after changes are applied
          this.fileService.refresh();
        }
      },
      error: () => {
        this.isProcessing = false;
      }
    });
  }
  
  rejectProposal(proposalId: string): void {
    this.isProcessing = true;
    this.proposalService.rejectProposal(proposalId).subscribe({
      next: () => {
        this.isProcessing = false;
        // Close diff tab if open for this proposal
        this.filePreviewService.closeDiffForProposal(proposalId);
      },
      error: () => {
        this.isProcessing = false;
      }
    });
  }
}

