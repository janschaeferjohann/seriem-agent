import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

import { FileExplorerComponent } from './components/file-explorer/file-explorer.component';
import { ChatWindowComponent } from './components/chat-window/chat-window.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FileExplorerComponent, ChatWindowComponent],
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
        <aside class="sidebar">
          <app-file-explorer />
        </aside>
        
        <section class="content">
          <app-chat-window (connectionChange)="onConnectionChange($event)" />
        </section>
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
    
    .sidebar {
      width: 280px;
      min-width: 200px;
      background: var(--bg-secondary);
      border-right: 1px solid var(--border-default);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      min-height: 0;
    }
    
    .content {
      flex: 1;
      min-height: 0;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
  `]
})
export class AppComponent {
  isConnected = false;
  
  onConnectionChange(connected: boolean): void {
    this.isConnected = connected;
  }
}

