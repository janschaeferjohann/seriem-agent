import { Component, ElementRef, HostListener, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';

import { FileExplorerComponent } from './components/file-explorer/file-explorer.component';
import { ChatWindowComponent } from './components/chat-window/chat-window.component';
import { FilePreviewComponent } from './components/file-preview/file-preview.component';
import { ChangeReviewComponent } from './components/change-review/change-review.component';
import { FirstRunWizardComponent } from './components/first-run-wizard/first-run-wizard.component';
import { SettingsComponent } from './components/settings/settings.component';
import { TelemetryViewerComponent } from './components/telemetry-viewer/telemetry-viewer.component';

import { FilePreviewService } from './services/file-preview.service';
import { ProposalService } from './services/proposal.service';
import { SettingsService } from './services/settings.service';
import { TelemetryService } from './services/telemetry.service';
import { isElectron } from './utils/environment';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    FileExplorerComponent,
    FilePreviewComponent,
    ChatWindowComponent,
    ChangeReviewComponent,
    FirstRunWizardComponent,
    SettingsComponent,
    TelemetryViewerComponent,
  ],
  template: `
    <!-- First-run wizard -->
    @if (showFirstRunWizard) {
      <app-first-run-wizard 
        (completed)="onWizardCompleted()"
        (skipped)="onWizardSkipped()" />
    }
    
    <div class="app-container">
      <header class="app-header">
        <div class="logo">
          <span class="logo-icon">◈</span>
          <span class="logo-text">Seriem Agent</span>
        </div>
        
        <div class="header-center">
          <!-- Pending Changes Button -->
          <button class="pending-changes-btn"
                  [class.has-changes]="proposalService.hasProposals()"
                  (click)="proposalService.toggleReviewPanel()"
                  matTooltip="Pending Changes">
            <mat-icon>rate_review</mat-icon>
            <span>Pending Changes</span>
            @if (proposalService.pendingCount() > 0) {
              <span class="badge">{{ proposalService.pendingCount() }}</span>
            }
          </button>
        </div>
        
        <div class="header-right">
          <!-- Settings Button -->
          <button class="settings-btn" 
                  (click)="settingsService.toggleSettingsPanel()" 
                  matTooltip="Settings"
                  [class.active]="settingsService.isSettingsPanelOpen()">
            <mat-icon>settings</mat-icon>
          </button>
          
          <div class="status">
            <span class="status-dot" [class.connected]="isConnected"></span>
            <span class="status-text">{{ isConnected ? 'Connected' : 'Disconnected' }}</span>
          </div>
        </div>
      </header>
      
      <main class="app-main">
        <div class="workbench" #workbench>
          <aside class="sidebar" [style.width.px]="sidebarWidthPx">
            <app-file-explorer />
          </aside>

          <div
            class="splitter"
            role="separator"
            aria-label="Resize sidebar"
            title="Drag to resize"
            (pointerdown)="onSplitterPointerDown('sidebar', $event)"></div>

          @if (filePreviewService.isPreviewOpen()) {
            <section class="preview">
              <app-file-preview />
            </section>

            <div
              class="splitter"
              role="separator"
              aria-label="Resize chat"
              title="Drag to resize"
              (pointerdown)="onSplitterPointerDown('chat', $event)"></div>
          }

          @if (chatCollapsed) {
            <aside class="chat-collapsed" (click)="chatCollapsed = false" matTooltip="Expand Chat">
              <mat-icon>chat</mat-icon>
            </aside>
          } @else {
            <aside
              class="chat"
              [style.width.px]="filePreviewService.isPreviewOpen() ? chatWidthPx : null"
              [style.flex]="filePreviewService.isPreviewOpen() ? '0 0 auto' : '1 1 auto'">
              <app-chat-window 
                (connectionChange)="onConnectionChange($event)"
                (collapse)="chatCollapsed = true" />
            </aside>
          }
        </div>
        
        <!-- Change Review Panel (slides in from right) -->
        @if (proposalService.isReviewPanelOpen()) {
          @if (proposalService.isReviewPanelCollapsed()) {
            <aside class="review-panel-collapsed" (click)="proposalService.expandReviewPanel()" matTooltip="Expand Pending Changes">
              <mat-icon>rate_review</mat-icon>
              @if (proposalService.pendingCount() > 0) {
                <span class="collapsed-badge">{{ proposalService.pendingCount() }}</span>
              }
            </aside>
          } @else {
            <div
              class="splitter review-splitter"
              role="separator"
              aria-label="Resize review panel"
              title="Drag to resize"
              (pointerdown)="onSplitterPointerDown('review', $event)"></div>
            <aside class="review-panel" [style.width.px]="reviewPanelWidthPx">
              <app-change-review />
            </aside>
          }
        }
      </main>
      
      <!-- Settings Panel (slides in from right) -->
      <app-settings />
      
      <!-- Telemetry Viewer Panel (slides in from right) -->
      <app-telemetry-viewer />
    </div>
  `,
  styles: [`
    .app-container {
      display: flex;
      flex-direction: column;
      height: 100vh;
      background: var(--bg-primary);
    }
    
    .app-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--spacing-sm) var(--spacing-md);
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border-default);
      height: 48px;
      flex-shrink: 0;
    }
    
    .logo {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
    }
    
    .logo-icon {
      font-size: 20px;
      color: var(--accent-primary);
    }
    
    .logo-text {
      font-weight: 600;
      font-size: 15px;
      letter-spacing: -0.3px;
    }
    
    .header-center {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
    }
    
    .header-right {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
    }
    
    .settings-btn {
      width: 32px;
      height: 32px;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: transparent;
      border: none;
      border-radius: var(--radius-sm);
      color: var(--text-secondary);
      cursor: pointer;
      transition: all var(--transition-fast);
      
      mat-icon {
        font-size: 20px;
        width: 20px;
        height: 20px;
        transition: transform 0.3s ease;
      }
      
      &:hover {
        background: var(--bg-hover);
        color: var(--text-primary);
        
        mat-icon {
          transform: rotate(45deg);
        }
      }
      
      &.active {
        color: var(--kw-red);
        
        mat-icon {
          transform: rotate(45deg);
        }
      }
    }
    
    .pending-changes-btn {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      padding: var(--spacing-xs) var(--spacing-sm);
      background: transparent;
      border: 1px solid var(--border-default);
      border-radius: var(--radius-sm);
      color: var(--text-secondary);
      font-family: inherit;
      font-size: 12px;
      cursor: pointer;
      transition: all var(--transition-fast);
      
      mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
      
      &:hover {
        background: var(--bg-hover);
        color: var(--text-primary);
      }
      
      &.has-changes {
        border-color: var(--accent-primary);
        color: var(--accent-primary);
        
        &:hover {
          background: rgba(99, 102, 241, 0.1);
        }
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
    }
    
    .status {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      font-size: 12px;
      color: var(--text-secondary);
    }
    
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-error);
      transition: background var(--transition-fast);
      
      &.connected {
        background: var(--accent-secondary);
      }
    }
    
    .app-main {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    .workbench {
      display: flex;
      flex: 1;
      overflow: hidden;
      min-width: 0;
    }
    
    .sidebar {
      flex: 0 0 auto;
      min-width: 200px;
      background: var(--bg-secondary);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      min-height: 0;
    }

    .splitter {
      flex: 0 0 auto;
      width: 6px;
      cursor: col-resize;
      background: transparent;
      position: relative;

      &:hover {
        background: var(--bg-hover);
      }

      &::after {
        content: "";
        position: absolute;
        top: 0;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 1px;
        background: var(--border-default);
        opacity: 0.7;
      }
    }

    .preview {
      flex: 1 1 auto;
      min-width: 360px;
      min-height: 0;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      background: var(--bg-primary);
    }

    .chat {
      flex: 0 0 auto;
      min-width: 320px;
      min-height: 0;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      background: var(--bg-primary);
    }
    
    .chat-collapsed {
      flex: 0 0 auto;
      width: 40px;
      min-height: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--bg-secondary);
      border-left: 1px solid var(--border-default);
      cursor: pointer;
      transition: background var(--transition-fast);
      
      mat-icon {
        color: var(--text-muted);
        transform: rotate(0deg);
        transition: all var(--transition-fast);
      }
      
      &:hover {
        background: var(--bg-hover);
        
        mat-icon {
          color: var(--accent-primary);
        }
      }
    }
    
    .review-splitter {
      flex-shrink: 0;
    }
    
    .review-panel {
      flex: 0 0 auto;
      min-width: 320px;
      max-width: 500px;
      min-height: 0;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      background: var(--bg-secondary);
    }
    
    .review-panel-collapsed {
      flex: 0 0 auto;
      width: 40px;
      min-height: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding-top: var(--spacing-md);
      gap: var(--spacing-xs);
      background: var(--bg-secondary);
      border-left: 1px solid var(--border-default);
      cursor: pointer;
      transition: background var(--transition-fast);
      
      mat-icon {
        color: var(--text-muted);
        transition: color var(--transition-fast);
      }
      
      .collapsed-badge {
        background: var(--accent-primary);
        color: white;
        font-size: 10px;
        font-weight: 600;
        padding: 1px 5px;
        border-radius: 8px;
        min-width: 16px;
        text-align: center;
      }
      
      &:hover {
        background: var(--bg-hover);
        
        mat-icon {
          color: var(--accent-primary);
        }
      }
    }
  `]
})
export class AppComponent {
  isConnected = false;
  showFirstRunWizard = false;
  readonly isElectron = isElectron;
  
  private _chatCollapsed = false;
  get chatCollapsed(): boolean { return this._chatCollapsed; }
  set chatCollapsed(value: boolean) {
    const oldValue = this._chatCollapsed;
    this._chatCollapsed = value;
    if (oldValue !== value) {
      // Trigger window resize after Angular re-renders the DOM
      // This lets Monaco's automaticLayout detect the container size change
      requestAnimationFrame(() => window.dispatchEvent(new Event('resize')));
    }
  }

  @ViewChild('workbench') private workbenchRef!: ElementRef<HTMLElement>;

  private readonly minSidebarWidthPx = 200;
  private readonly minPreviewWidthPx = 360;
  private readonly minChatWidthPx = 320;
  private readonly minReviewPanelWidthPx = 320;
  private readonly collapsedWidthPx = 40;
  private readonly splitterWidthPx = 6;

  sidebarWidthPx = 280;
  chatWidthPx = 420;
  reviewPanelWidthPx = 360;

  private dragKind: 'sidebar' | 'chat' | 'review' | null = null;
  private dragPointerId: number | null = null;
  private dragStartX = 0;
  private dragStartSidebarWidthPx = 0;
  private dragStartChatWidthPx = 0;
  private dragStartReviewPanelWidthPx = 0;

  constructor(
    public filePreviewService: FilePreviewService,
    public proposalService: ProposalService,
    public settingsService: SettingsService,
    public telemetryService: TelemetryService,
  ) {
    this.restoreLayout();
    // TODO: Re-enable when first-run wizard is needed
    // this.checkFirstRun();
  }
  
  /**
   * Check if this is the first run (no API key configured)
   */
  async checkFirstRun(): Promise<void> {
    if (isElectron && window.electronAPI?.isFirstRun) {
      this.showFirstRunWizard = await window.electronAPI.isFirstRun();
    } else {
      // In browser mode, check localStorage
      const hasKey = !!localStorage.getItem('anthropic_api_key');
      this.showFirstRunWizard = !hasKey;
    }
  }
  
  onWizardCompleted(): void {
    this.showFirstRunWizard = false;
  }
  
  onWizardSkipped(): void {
    this.showFirstRunWizard = false;
    // Mark as skipped so we don't show again this session
    sessionStorage.setItem('wizard_skipped', 'true');
  }
  
  onConnectionChange(connected: boolean): void {
    this.isConnected = connected;
  }

  onSplitterPointerDown(kind: 'sidebar' | 'chat' | 'review', event: PointerEvent): void {
    if (kind === 'chat' && !this.filePreviewService.isPreviewOpen()) return;
    if (kind === 'review' && !this.proposalService.isReviewPanelOpen()) return;
    event.preventDefault();

    this.dragKind = kind;
    this.dragPointerId = event.pointerId;
    this.dragStartX = event.clientX;
    this.dragStartSidebarWidthPx = this.sidebarWidthPx;
    this.dragStartChatWidthPx = this.chatWidthPx;
    this.dragStartReviewPanelWidthPx = this.reviewPanelWidthPx;
  }

  @HostListener('window:pointermove', ['$event'])
  onWindowPointerMove(event: PointerEvent): void {
    if (!this.dragKind || this.dragPointerId !== event.pointerId) return;

    const workbenchEl = this.workbenchRef?.nativeElement;
    if (!workbenchEl) return;

    const totalWidth = workbenchEl.getBoundingClientRect().width;
    const isPreviewOpen = this.filePreviewService.isPreviewOpen();

    if (this.dragKind === 'sidebar') {
      const delta = event.clientX - this.dragStartX;
      const desired = this.dragStartSidebarWidthPx + delta;
      const maxSidebar = isPreviewOpen
        ? totalWidth - (2 * this.splitterWidthPx) - this.chatWidthPx - this.minPreviewWidthPx
        : totalWidth - this.splitterWidthPx - this.minChatWidthPx;
      this.sidebarWidthPx = this.clamp(desired, this.minSidebarWidthPx, Math.max(this.minSidebarWidthPx, maxSidebar));
      return;
    }

    if (this.dragKind === 'chat' && isPreviewOpen) {
      const delta = this.dragStartX - event.clientX;
      const desired = this.dragStartChatWidthPx + delta;
      const maxChat = totalWidth - (2 * this.splitterWidthPx) - this.sidebarWidthPx - this.minPreviewWidthPx;
      this.chatWidthPx = this.clamp(desired, this.minChatWidthPx, Math.max(this.minChatWidthPx, maxChat));
      return;
    }

    if (this.dragKind === 'review') {
      // Review panel resizes from the left (dragging left increases width)
      const delta = this.dragStartX - event.clientX;
      const desired = this.dragStartReviewPanelWidthPx + delta;
      // Max width is 40% of total app width or 500px, whichever is smaller
      const maxReview = Math.min(500, window.innerWidth * 0.4);
      this.reviewPanelWidthPx = this.clamp(desired, this.minReviewPanelWidthPx, maxReview);
    }
  }

  @HostListener('window:pointerup', ['$event'])
  @HostListener('window:pointercancel', ['$event'])
  onWindowPointerUp(event: PointerEvent): void {
    if (this.dragPointerId !== event.pointerId) return;
    if (!this.dragKind) return;

    this.dragKind = null;
    this.dragPointerId = null;
    this.persistLayout();
  }

  private clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, value));
  }

  private persistLayout(): void {
    try {
      localStorage.setItem('layout.sidebarWidthPx', String(Math.round(this.sidebarWidthPx)));
      localStorage.setItem('layout.chatWidthPx', String(Math.round(this.chatWidthPx)));
      localStorage.setItem('layout.reviewPanelWidthPx', String(Math.round(this.reviewPanelWidthPx)));
    } catch {
      // ignore
    }
  }

  private restoreLayout(): void {
    try {
      const sidebar = Number(localStorage.getItem('layout.sidebarWidthPx'));
      const chat = Number(localStorage.getItem('layout.chatWidthPx'));
      const review = Number(localStorage.getItem('layout.reviewPanelWidthPx'));
      if (Number.isFinite(sidebar) && sidebar > 0) this.sidebarWidthPx = sidebar;
      if (Number.isFinite(chat) && chat > 0) this.chatWidthPx = chat;
      if (Number.isFinite(review) && review > 0) this.reviewPanelWidthPx = review;
    } catch {
      // ignore
    }
  }
}

