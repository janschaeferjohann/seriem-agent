/**
 * Telemetry Viewer Component
 * 
 * A panel for viewing local telemetry data including stats and event log.
 */

import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { TelemetryService, TelemetryEvent, TelemetryStats } from '../../services/telemetry.service';

@Component({
  selector: 'app-telemetry-viewer',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatSelectModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="telemetry-panel" [class.open]="telemetryService.isViewerOpen()">
      <!-- Header -->
      <div class="panel-header">
        <div class="header-left">
          <mat-icon>analytics</mat-icon>
          <span class="header-title">Telemetry</span>
        </div>
        <div class="header-actions">
          <button mat-icon-button 
                  matTooltip="Export JSONL"
                  (click)="exportEvents()">
            <mat-icon>download</mat-icon>
          </button>
          <button mat-icon-button 
                  matTooltip="Refresh"
                  (click)="refresh()">
            <mat-icon>refresh</mat-icon>
          </button>
          <button mat-icon-button 
                  matTooltip="Close"
                  (click)="telemetryService.closeViewer()">
            <mat-icon>close</mat-icon>
          </button>
        </div>
      </div>
      
      <!-- Content -->
      <div class="panel-content">
        @if (telemetryService.isLoading()) {
          <div class="loading-overlay">
            <mat-spinner diameter="32"></mat-spinner>
          </div>
        }
        
        @if (!telemetryService.stats()?.enabled) {
          <div class="disabled-notice">
            <mat-icon>info_outline</mat-icon>
            <span>Telemetry is disabled. Enable it in settings to collect usage data.</span>
          </div>
        } @else {
          <!-- Stats Cards -->
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ telemetryService.stats()?.total_sessions || 0 }}</div>
              <div class="stat-label">Sessions</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ telemetryService.stats()?.total_chat_turns || 0 }}</div>
              <div class="stat-label">Chat Turns</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">
                {{ telemetryService.stats()?.proposals_approved || 0 }}/{{ telemetryService.stats()?.total_proposals || 0 }}
              </div>
              <div class="stat-label">Proposals Approved</div>
            </div>
            <div class="stat-card" [class.error]="(telemetryService.stats()?.total_errors || 0) > 0">
              <div class="stat-value">{{ telemetryService.stats()?.total_errors || 0 }}</div>
              <div class="stat-label">Errors</div>
            </div>
          </div>
          
          <!-- Filters -->
          <div class="filters-row">
            <mat-form-field appearance="outline" class="filter-field">
              <mat-label>Event Type</mat-label>
              <mat-select [(ngModel)]="selectedEventType" (selectionChange)="applyFilters()">
                <mat-option value="">All Events</mat-option>
                <mat-option value="SessionStart">SessionStart</mat-option>
                <mat-option value="SessionEnd">SessionEnd</mat-option>
                <mat-option value="ChatTurn">ChatTurn</mat-option>
                <mat-option value="ProposalCreated">ProposalCreated</mat-option>
                <mat-option value="ProposalDecision">ProposalDecision</mat-option>
                <mat-option value="Error">Error</mat-option>
              </mat-select>
            </mat-form-field>
            
            <mat-form-field appearance="outline" class="filter-field search-field">
              <mat-label>Search</mat-label>
              <input matInput [(ngModel)]="searchQuery" (input)="onSearchInput()" placeholder="Search events...">
              @if (searchQuery) {
                <button mat-icon-button matSuffix (click)="clearSearch()">
                  <mat-icon>close</mat-icon>
                </button>
              }
            </mat-form-field>
          </div>
          
          <!-- Event Log -->
          <div class="event-log">
            <div class="log-header">
              <span class="col-time">Time</span>
              <span class="col-type">Type</span>
              <span class="col-details">Details</span>
            </div>
            
            <div class="log-body">
              @for (event of telemetryService.events(); track event.timestamp) {
                <div class="event-row" [class]="'event-' + event.event_type.toLowerCase()" (click)="toggleExpand(event)">
                  <span class="col-time">{{ formatTime(event.timestamp) }}</span>
                  <span class="col-type">
                    <span class="event-badge" [class]="'badge-' + event.event_type.toLowerCase()">
                      {{ event.event_type }}
                    </span>
                  </span>
                  <span class="col-details">
                    <span class="summary">{{ getEventSummary(event) }}</span>
                    <mat-icon class="expand-icon" [class.expanded]="isExpanded(event)">expand_more</mat-icon>
                  </span>
                </div>
                @if (isExpanded(event)) {
                  <div class="event-payload">
                    <pre>{{ event.payload | json }}</pre>
                  </div>
                }
              } @empty {
                <div class="empty-state">
                  <mat-icon>inbox</mat-icon>
                  <span>No events found</span>
                </div>
              }
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .telemetry-panel {
      position: fixed;
      top: 0;
      right: -450px;
      width: 450px;
      height: 100vh;
      background: var(--bg-secondary);
      border-left: 1px solid var(--border-default);
      z-index: 1000;
      display: flex;
      flex-direction: column;
      transition: right 0.3s ease;
      
      &.open {
        right: 0;
      }
    }
    
    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 var(--spacing-md);
      height: 48px;
      border-bottom: 1px solid var(--border-default);
      background: var(--bg-primary);
      flex-shrink: 0;
      
      .header-left {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        
        mat-icon {
          color: var(--kw-red);
          font-size: 18px;
          width: 18px;
          height: 18px;
        }
        
        .header-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary);
        }
      }
      
      .header-actions {
        display: flex;
        align-items: center;
        gap: 2px;
        
        button {
          width: 28px;
          height: 28px;
          padding: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          
          mat-icon {
            font-size: 18px;
            width: 18px;
            height: 18px;
            line-height: 18px;
          }
        }
      }
    }
    
    .panel-content {
      flex: 1;
      overflow-y: auto;
      padding: var(--spacing-md);
      display: flex;
      flex-direction: column;
      gap: var(--spacing-md);
    }
    
    .loading-overlay {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: var(--spacing-xl);
    }
    
    .disabled-notice {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-md);
      background: var(--bg-tertiary);
      border-radius: var(--radius-md);
      color: var(--text-secondary);
      font-size: 12px;
      
      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }
    }
    
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: var(--spacing-sm);
    }
    
    .stat-card {
      background: var(--bg-tertiary);
      border-radius: var(--radius-md);
      padding: var(--spacing-md);
      text-align: center;
      
      .stat-value {
        font-size: 20px;
        font-weight: 600;
        color: var(--text-primary);
        font-family: var(--font-mono);
      }
      
      .stat-label {
        font-size: 10px;
        color: var(--text-muted);
        text-transform: uppercase;
        margin-top: 2px;
      }
      
      &.error .stat-value {
        color: var(--accent-error);
      }
    }
    
    .filters-row {
      display: flex;
      gap: var(--spacing-sm);
      
      .filter-field {
        flex: 1;
      }
      
      .search-field {
        flex: 2;
      }
    }
    
    /* Compact form fields */
    ::ng-deep .mat-mdc-form-field {
      .mat-mdc-text-field-wrapper {
        padding: 0 10px !important;
        height: 36px !important;
      }
      
      .mat-mdc-form-field-flex {
        height: 36px !important;
        align-items: center !important;
      }
      
      .mat-mdc-form-field-infix {
        min-height: 36px !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        display: flex !important;
        align-items: center !important;
        border-top: 0 !important;
      }
      
      .mdc-text-field--outlined {
        --mdc-outlined-text-field-container-shape: 4px;
        --mdc-outlined-text-field-focus-outline-color: #E30018;
        --mdc-outlined-text-field-focus-label-text-color: #E30018;
      }
      
      input, .mat-mdc-select-value {
        font-size: 12px !important;
      }
      
      .mdc-floating-label {
        font-size: 12px !important;
      }
    }
    
    .event-log {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-height: 200px;
      border: 1px solid var(--border-default);
      border-radius: var(--radius-md);
      overflow: hidden;
    }
    
    .log-header {
      display: flex;
      padding: var(--spacing-sm) var(--spacing-md);
      background: var(--bg-tertiary);
      border-bottom: 1px solid var(--border-default);
      font-size: 10px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      
      .col-time { width: 70px; }
      .col-type { width: 120px; }
      .col-details { flex: 1; }
    }
    
    .log-body {
      flex: 1;
      overflow-y: auto;
    }
    
    .event-row {
      display: flex;
      padding: var(--spacing-sm) var(--spacing-md);
      border-bottom: 1px solid var(--border-subtle);
      font-size: 11px;
      cursor: pointer;
      transition: background 0.15s;
      
      &:hover {
        background: var(--bg-hover);
      }
      
      .col-time {
        width: 70px;
        color: var(--text-muted);
        font-family: var(--font-mono);
        font-size: 10px;
      }
      
      .col-type {
        width: 120px;
      }
      
      .col-details {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--spacing-sm);
        min-width: 0;
        
        .summary {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: var(--text-secondary);
        }
        
        .expand-icon {
          font-size: 16px;
          width: 16px;
          height: 16px;
          color: var(--text-muted);
          transition: transform 0.2s;
          
          &.expanded {
            transform: rotate(180deg);
          }
        }
      }
    }
    
    .event-badge {
      display: inline-block;
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 9px;
      font-weight: 600;
      text-transform: uppercase;
      
      &.badge-sessionstart, &.badge-sessionend {
        background: rgba(81, 165, 86, 0.15);
        color: var(--accent-secondary);
      }
      
      &.badge-chatturn {
        background: rgba(227, 0, 24, 0.1);
        color: var(--kw-red);
      }
      
      &.badge-proposalcreated {
        background: rgba(66, 133, 244, 0.15);
        color: #4285f4;
      }
      
      &.badge-proposaldecision {
        background: rgba(156, 39, 176, 0.15);
        color: #9c27b0;
      }
      
      &.badge-error {
        background: rgba(244, 67, 54, 0.15);
        color: var(--accent-error);
      }
    }
    
    .event-payload {
      padding: var(--spacing-sm) var(--spacing-md);
      background: var(--bg-tertiary);
      border-bottom: 1px solid var(--border-default);
      
      pre {
        margin: 0;
        font-size: 10px;
        font-family: var(--font-mono);
        color: var(--text-secondary);
        white-space: pre-wrap;
        word-break: break-all;
      }
    }
    
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: var(--spacing-xl);
      color: var(--text-muted);
      gap: var(--spacing-sm);
      
      mat-icon {
        font-size: 32px;
        width: 32px;
        height: 32px;
      }
      
      span {
        font-size: 12px;
      }
    }
  `]
})
export class TelemetryViewerComponent implements OnInit {
  selectedEventType = '';
  searchQuery = '';
  expandedEvents = new Set<TelemetryEvent>();
  
  private searchDebounceTimer: any;

  constructor(public telemetryService: TelemetryService) {}

  ngOnInit(): void {
    // Load data when opened
    this.refresh();
  }

  refresh(): void {
    this.telemetryService.loadStats();
    this.applyFilters();
  }

  applyFilters(): void {
    const eventTypes = this.selectedEventType ? [this.selectedEventType] : undefined;
    this.telemetryService.loadEvents(eventTypes, this.searchQuery || undefined);
  }

  onSearchInput(): void {
    // Debounce search
    clearTimeout(this.searchDebounceTimer);
    this.searchDebounceTimer = setTimeout(() => {
      this.applyFilters();
    }, 300);
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.applyFilters();
  }

  exportEvents(): void {
    this.telemetryService.exportEvents();
  }

  toggleExpand(event: TelemetryEvent): void {
    if (this.expandedEvents.has(event)) {
      this.expandedEvents.delete(event);
    } else {
      this.expandedEvents.add(event);
    }
  }

  isExpanded(event: TelemetryEvent): boolean {
    return this.expandedEvents.has(event);
  }

  formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  }

  getEventSummary(event: TelemetryEvent): string {
    const payload = event.payload;
    
    switch (event.event_type) {
      case 'SessionStart':
        return `OS: ${payload['os'] || 'unknown'}`;
      case 'SessionEnd':
        return `Duration: ${payload['duration_seconds'] || 0}s, Turns: ${payload['chat_turns'] || 0}`;
      case 'ChatTurn':
        const tools = payload['tool_count'] || 0;
        return tools > 0 ? `${tools} tool(s) called` : 'No tools';
      case 'ProposalCreated':
        return `${payload['file_count'] || 1} file(s): ${(payload['operations'] || []).join(', ')}`;
      case 'ProposalDecision':
        return payload['decision'] === 'approved' ? 'Approved' : 'Rejected';
      case 'Error':
        return payload['message'] || 'Unknown error';
      default:
        return JSON.stringify(payload).slice(0, 50);
    }
  }
}

