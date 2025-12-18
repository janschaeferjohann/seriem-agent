import { Component, ElementRef, HostListener, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';

import { FileExplorerComponent } from './components/file-explorer/file-explorer.component';
import { ChatWindowComponent } from './components/chat-window/chat-window.component';
import { FilePreviewComponent } from './components/file-preview/file-preview.component';

import { FilePreviewService } from './services/file-preview.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FileExplorerComponent, FilePreviewComponent, ChatWindowComponent],
  template: `
    <div class="app-container">
      <header class="app-header">
        <div class="logo">
          <span class="logo-icon">◈</span>
          <span class="logo-text">Seriem Agent</span>
        </div>
        <div class="status">
          <span class="status-dot" [class.connected]="isConnected"></span>
          <span class="status-text">{{ isConnected ? 'Connected' : 'Disconnected' }}</span>
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

          <aside
            class="chat"
            [style.width.px]="filePreviewService.isPreviewOpen() ? chatWidthPx : null"
            [style.flex]="filePreviewService.isPreviewOpen() ? '0 0 auto' : '1 1 auto'">
            <app-chat-window (connectionChange)="onConnectionChange($event)" />
          </aside>
        </div>
      </main>
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
  `]
})
export class AppComponent {
  isConnected = false;

  @ViewChild('workbench') private workbenchRef!: ElementRef<HTMLElement>;

  private readonly minSidebarWidthPx = 200;
  private readonly minPreviewWidthPx = 360;
  private readonly minChatWidthPx = 320;
  private readonly splitterWidthPx = 6;

  sidebarWidthPx = 280;
  chatWidthPx = 420;

  private dragKind: 'sidebar' | 'chat' | null = null;
  private dragPointerId: number | null = null;
  private dragStartX = 0;
  private dragStartSidebarWidthPx = 0;
  private dragStartChatWidthPx = 0;

  constructor(public filePreviewService: FilePreviewService) {
    this.restoreLayout();
  }
  
  onConnectionChange(connected: boolean): void {
    this.isConnected = connected;
  }

  onSplitterPointerDown(kind: 'sidebar' | 'chat', event: PointerEvent): void {
    if (kind === 'chat' && !this.filePreviewService.isPreviewOpen()) return;
    event.preventDefault();

    this.dragKind = kind;
    this.dragPointerId = event.pointerId;
    this.dragStartX = event.clientX;
    this.dragStartSidebarWidthPx = this.sidebarWidthPx;
    this.dragStartChatWidthPx = this.chatWidthPx;
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
    } catch {
      // ignore
    }
  }

  private restoreLayout(): void {
    try {
      const sidebar = Number(localStorage.getItem('layout.sidebarWidthPx'));
      const chat = Number(localStorage.getItem('layout.chatWidthPx'));
      if (Number.isFinite(sidebar) && sidebar > 0) this.sidebarWidthPx = sidebar;
      if (Number.isFinite(chat) && chat > 0) this.chatWidthPx = chat;
    } catch {
      // ignore
    }
  }
}

