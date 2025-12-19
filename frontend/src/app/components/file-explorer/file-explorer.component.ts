import { Component, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { FileService, TreeNode } from '../../services/file.service';
import { FilePreviewService } from '../../services/file-preview.service';
import { WorkspaceService } from '../../services/workspace.service';

@Component({
  selector: 'app-file-explorer',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="file-explorer">
      <!-- Workspace selector -->
      <div class="workspace-header">
        <button class="workspace-selector"
                matTooltip="Change workspace"
                (click)="changeWorkspace()"
                [disabled]="workspaceService.isLoading()">
          <mat-icon class="workspace-icon">folder_special</mat-icon>
          <span class="workspace-name">{{ workspaceService.workspaceName() }}</span>
          @if (workspaceService.isGitRepo()) {
            <span class="git-branch">
              <mat-icon>commit</mat-icon>
              {{ workspaceService.gitBranch() || 'unknown' }}
            </span>
          }
          <mat-icon class="workspace-dropdown">unfold_more</mat-icon>
        </button>
      </div>
      
      <div class="explorer-header">
        <span class="header-title">Files</span>
        <div class="header-actions">
          <button mat-icon-button 
                  matTooltip="Refresh"
                  (click)="refresh()"
                  [disabled]="fileService.isLoading()">
            <mat-icon>refresh</mat-icon>
          </button>
        </div>
      </div>
      
      @if (fileService.isLoading() && visibleNodes().length === 0) {
        <div class="loading">
          <mat-spinner diameter="24"></mat-spinner>
        </div>
      }
      
      @if (fileService.error()) {
        <div class="error">
          <mat-icon>error_outline</mat-icon>
          <span>{{ fileService.error() }}</span>
        </div>
      }
      
      <div class="file-list">
        @for (node of visibleNodes(); track node.path) {
          <div class="tree-item" 
               [class.selected]="isSelected(node)"
               [class.directory]="node.is_directory"
               [style.padding-left.px]="getIndent(node)"
               (click)="onNodeClick(node, $event)">
            
            <!-- Expand/collapse toggle for directories -->
            @if (node.is_directory) {
              <span class="toggle-icon" (click)="toggleExpand(node, $event)">
                @if (node.isLoading) {
                  <mat-spinner diameter="12"></mat-spinner>
                } @else {
                  <mat-icon>{{ node.isExpanded ? 'expand_more' : 'chevron_right' }}</mat-icon>
                }
              </span>
            } @else {
              <span class="toggle-spacer"></span>
            }
            
            <!-- File/folder icon -->
            <mat-icon class="file-icon">
              {{ node.is_directory ? (node.isExpanded ? 'folder_open' : 'folder') : getFileIcon(node.name) }}
            </mat-icon>
            
            <!-- Name -->
            <span class="file-name">{{ node.name }}</span>
            
            <!-- Size for files -->
            @if (!node.is_directory && node.size !== undefined) {
              <span class="file-size">{{ formatSize(node.size) }}</span>
            }
          </div>
        } @empty {
          @if (!fileService.isLoading() && !fileService.error()) {
            <div class="empty-state">
              <mat-icon>folder_open</mat-icon>
              <span>Empty directory</span>
            </div>
          }
        }
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: flex;
      flex-direction: column;
      flex: 1 1 auto;
      height: 100%;
      min-height: 0;
    }

    .file-explorer {
      display: flex;
      flex-direction: column;
      height: 100%;
      min-height: 0;
      overflow: hidden;
    }
    
    .workspace-header {
      padding: var(--spacing-xs) var(--spacing-sm);
      border-bottom: 1px solid var(--border-default);
      flex-shrink: 0;
    }
    
    .workspace-selector {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      width: 100%;
      padding: var(--spacing-xs) var(--spacing-sm);
      background: var(--bg-tertiary);
      border: 1px solid var(--border-default);
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: all var(--transition-fast);
      color: var(--text-primary);
      font-family: inherit;
      font-size: 12px;
      text-align: left;
      
      &:hover {
        background: var(--bg-hover);
        border-color: var(--border-subtle);
      }
      
      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
    }
    
    .workspace-icon {
      font-size: 16px;
      width: 16px;
      height: 16px;
      color: var(--accent-primary);
      flex-shrink: 0;
    }
    
    .workspace-name {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-weight: 500;
    }
    
    .git-branch {
      display: flex;
      align-items: center;
      gap: 2px;
      font-size: 11px;
      color: var(--accent-secondary);
      flex-shrink: 0;
      
      mat-icon {
        font-size: 12px;
        width: 12px;
        height: 12px;
      }
    }
    
    .workspace-dropdown {
      font-size: 16px;
      width: 16px;
      height: 16px;
      color: var(--text-muted);
      flex-shrink: 0;
    }
    
    .explorer-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 6px var(--spacing-md);
      border-bottom: 1px solid var(--border-default);
      height: 36px;
      flex-shrink: 0;
      flex-wrap: nowrap;
    }
    
    .header-title {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-secondary);
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      flex-shrink: 0;
      
      button {
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        
        mat-icon {
          font-size: 16px;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
      }
    }
    
    .loading {
      display: flex;
      justify-content: center;
      padding: var(--spacing-lg);
    }
    
    .error {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-md);
      color: var(--accent-error);
      font-size: 12px;
      
      mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
    }
    
    .file-list {
      flex: 1 1 auto;
      min-height: 0;
      overflow-y: auto;
      padding: var(--spacing-xs) 0;
    }
    
    .tree-item {
      display: flex;
      align-items: center;
      gap: 2px;
      padding: 3px var(--spacing-sm);
      padding-right: var(--spacing-md);
      cursor: pointer;
      transition: background var(--transition-fast);
      min-height: 26px;
      
      &:hover {
        background: var(--bg-hover);
      }
      
      &.selected {
        background: var(--bg-tertiary);
      }
      
      &.directory .file-icon {
        color: var(--accent-warning);
      }
    }
    
    .toggle-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      flex-shrink: 0;
      
      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
        color: var(--text-muted);
      }
      
      mat-spinner {
        margin: 3px;
      }
      
      &:hover mat-icon {
        color: var(--text-primary);
      }
    }
    
    .toggle-spacer {
      width: 18px;
      flex-shrink: 0;
    }
    
    .file-icon {
      font-size: 16px;
      width: 16px;
      height: 16px;
      color: var(--text-secondary);
      flex-shrink: 0;
      margin-right: 4px;
    }
    
    .file-name {
      flex: 1;
      font-size: 13px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .file-size {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-muted);
      flex-shrink: 0;
    }
    
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-xl);
      color: var(--text-muted);
      
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
export class FileExplorerComponent implements OnInit {
  // Computed signal for visible nodes
  visibleNodes = computed(() => this.fileService.getVisibleNodes());
  
  constructor(
    public fileService: FileService,
    private filePreviewService: FilePreviewService,
    public workspaceService: WorkspaceService
  ) {}
  
  ngOnInit(): void {
    this.fileService.initTree();
  }
  
  /**
   * Open folder picker to change workspace
   */
  async changeWorkspace(): Promise<void> {
    const success = await this.workspaceService.selectWorkspace();
    if (success) {
      // Refresh file tree after workspace change
      this.fileService.initTree();
      // Close any open file previews
      this.filePreviewService.closeAll();
    }
  }
  
  onNodeClick(node: TreeNode, event: Event): void {
    if (node.is_directory) {
      // Toggle expand/collapse for directories
      this.fileService.toggleNode(node);
    } else {
      // Open file in preview tabs
      this.filePreviewService.openFile(node);
    }
  }
  
  toggleExpand(node: TreeNode, event: Event): void {
    event.stopPropagation();
    this.fileService.toggleNode(node);
  }
  
  refresh(): void {
    this.fileService.refresh();
  }
  
  isSelected(node: TreeNode): boolean {
    return this.filePreviewService.activePath() === node.path;
  }
  
  getIndent(node: TreeNode): number {
    // Base padding (8px) + 16px per level
    return 8 + (node.level * 16);
  }
  
  getFileIcon(filename: string): string {
    const ext = filename.split('.').pop()?.toLowerCase();
    
    const iconMap: Record<string, string> = {
      'ts': 'code',
      'js': 'javascript',
      'py': 'code',
      'json': 'data_object',
      'md': 'description',
      'txt': 'article',
      'html': 'html',
      'css': 'css',
      'scss': 'css',
      'yml': 'settings',
      'yaml': 'settings',
      'xml': 'code',
      'xsd': 'code',
    };
    
    return iconMap[ext || ''] || 'insert_drive_file';
  }
  
  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
}
