import { Component, OnInit, signal, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { HttpClient } from '@angular/common/http';
import { catchError, of } from 'rxjs';

import { WorkspaceService } from '../../services/workspace.service';
import { isElectron } from '../../utils/environment';

@Component({
  selector: 'app-first-run-wizard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="wizard-overlay">
      <div class="wizard-panel">
        <!-- Step indicator -->
        <div class="step-indicator">
          @for (s of [1, 2, 3]; track s) {
            <div class="step-dot" [class.active]="step() >= s" [class.current]="step() === s"></div>
          }
        </div>
        
        @switch (step()) {
          @case (1) {
            <div class="wizard-content">
              <div class="wizard-icon">
                <span class="logo-icon">◈</span>
              </div>
              <h2>Welcome to Seriem Agent</h2>
              <p class="wizard-description">
                Your AI-powered coding assistant. Let's get you set up in a few quick steps.
              </p>
              <div class="wizard-actions">
                <button mat-raised-button color="primary" (click)="nextStep()">
                  Get Started
                  <mat-icon>arrow_forward</mat-icon>
                </button>
              </div>
            </div>
          }
          
          @case (2) {
            <div class="wizard-content">
              <div class="wizard-icon">
                <mat-icon>key</mat-icon>
              </div>
              <h2>API Key</h2>
              <p class="wizard-description">
                Enter your Anthropic API key to enable the AI assistant.
              </p>
              
              <mat-form-field appearance="outline" class="api-key-field">
                <mat-label>Anthropic API Key</mat-label>
                <input matInput 
                       type="password" 
                       [(ngModel)]="apiKey" 
                       placeholder="sk-ant-..."
                       [disabled]="isValidating()">
                <mat-icon matSuffix>vpn_key</mat-icon>
              </mat-form-field>
              
              @if (validationError()) {
                <div class="error-message">
                  <mat-icon>error</mat-icon>
                  {{ validationError() }}
                </div>
              }
              
              <a href="https://console.anthropic.com/settings/keys" 
                 target="_blank" 
                 class="help-link"
                 (click)="openExternal($event, 'https://console.anthropic.com/settings/keys')">
                <mat-icon>open_in_new</mat-icon>
                Get an API key from Anthropic Console
              </a>
              
              <div class="wizard-actions">
                <button mat-button (click)="prevStep()">
                  <mat-icon>arrow_back</mat-icon>
                  Back
                </button>
                <button mat-raised-button 
                        color="primary" 
                        (click)="validateAndNext()"
                        [disabled]="!apiKey || isValidating()">
                  @if (isValidating()) {
                    <mat-spinner diameter="20"></mat-spinner>
                  } @else {
                    <ng-container>
                      Continue
                      <mat-icon>arrow_forward</mat-icon>
                    </ng-container>
                  }
                </button>
              </div>
            </div>
          }
          
          @case (3) {
            <div class="wizard-content">
              <div class="wizard-icon">
                <mat-icon>folder_open</mat-icon>
              </div>
              <h2>Select Workspace</h2>
              <p class="wizard-description">
                Choose a folder to work with. This is where the agent will be able to read and write files.
              </p>
              
              <div class="workspace-selector">
                @if (selectedFolder()) {
                  <div class="selected-folder">
                    <mat-icon>folder</mat-icon>
                    <span class="folder-path">{{ selectedFolder() }}</span>
                  </div>
                }
                
                <button mat-stroked-button (click)="selectFolder()">
                  <mat-icon>folder_open</mat-icon>
                  {{ selectedFolder() ? 'Change Folder' : 'Browse...' }}
                </button>
              </div>
              
              <div class="wizard-actions">
                <button mat-button (click)="prevStep()">
                  <mat-icon>arrow_back</mat-icon>
                  Back
                </button>
                <button mat-raised-button 
                        color="primary" 
                        (click)="finish()"
                        [disabled]="!selectedFolder()">
                  Start Using Seriem
                  <mat-icon>check</mat-icon>
                </button>
              </div>
            </div>
          }
        }
        
        <!-- Skip option -->
        @if (step() > 1) {
          <div class="skip-option">
            <button mat-button color="primary" (click)="skip()">
              Skip for now
            </button>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .wizard-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.8);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      backdrop-filter: blur(4px);
    }
    
    .wizard-panel {
      background: var(--bg-secondary);
      border: 1px solid var(--border-default);
      border-radius: var(--radius-lg);
      padding: var(--spacing-xl);
      width: 100%;
      max-width: 480px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
    }
    
    .step-indicator {
      display: flex;
      justify-content: center;
      gap: var(--spacing-sm);
      margin-bottom: var(--spacing-xl);
    }
    
    .step-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--bg-tertiary);
      transition: all var(--transition-fast);
      
      &.active {
        background: var(--accent-primary);
      }
      
      &.current {
        width: 24px;
        border-radius: 4px;
      }
    }
    
    .wizard-content {
      text-align: center;
    }
    
    .wizard-icon {
      margin-bottom: var(--spacing-lg);
      
      .logo-icon {
        font-size: 48px;
        color: var(--accent-primary);
      }
      
      mat-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
        color: var(--accent-primary);
      }
    }
    
    h2 {
      font-size: 24px;
      font-weight: 600;
      margin: 0 0 var(--spacing-sm) 0;
      color: var(--text-primary);
    }
    
    .wizard-description {
      color: var(--text-secondary);
      font-size: 14px;
      line-height: 1.6;
      margin: 0 0 var(--spacing-lg) 0;
    }
    
    .api-key-field {
      width: 100%;
      margin-bottom: var(--spacing-sm);
    }
    
    .error-message {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--spacing-xs);
      color: var(--accent-error);
      font-size: 13px;
      margin-bottom: var(--spacing-md);
      
      mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
    }
    
    .help-link {
      display: inline-flex;
      align-items: center;
      gap: var(--spacing-xs);
      color: var(--accent-primary);
      font-size: 13px;
      text-decoration: none;
      margin-bottom: var(--spacing-lg);
      
      mat-icon {
        font-size: 14px;
        width: 14px;
        height: 14px;
      }
      
      &:hover {
        text-decoration: underline;
      }
    }
    
    .workspace-selector {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--spacing-md);
      margin-bottom: var(--spacing-lg);
    }
    
    .selected-folder {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm) var(--spacing-md);
      background: var(--bg-tertiary);
      border-radius: var(--radius-sm);
      max-width: 100%;
      
      mat-icon {
        color: var(--accent-warning);
        flex-shrink: 0;
      }
      
      .folder-path {
        font-family: var(--font-mono);
        font-size: 12px;
        color: var(--text-secondary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
    
    .wizard-actions {
      display: flex;
      justify-content: center;
      gap: var(--spacing-md);
      margin-top: var(--spacing-lg);
      
      button {
        mat-icon {
          margin-left: 4px;
          
          &:first-child {
            margin-left: 0;
            margin-right: 4px;
          }
        }
      }
    }
    
    .skip-option {
      text-align: center;
      margin-top: var(--spacing-lg);
      padding-top: var(--spacing-md);
      border-top: 1px solid var(--border-subtle);
    }
    
    mat-spinner {
      display: inline-block;
    }
  `]
})
export class FirstRunWizardComponent implements OnInit {
  @Output() completed = new EventEmitter<void>();
  @Output() skipped = new EventEmitter<void>();
  
  step = signal(1);
  apiKey = '';
  isValidating = signal(false);
  validationError = signal<string | null>(null);
  selectedFolder = signal<string | null>(null);
  
  constructor(
    private http: HttpClient,
    private workspaceService: WorkspaceService,
  ) {}
  
  ngOnInit(): void {
    // Check if we should show the wizard
    this.checkFirstRun();
  }
  
  async checkFirstRun(): Promise<void> {
    if (isElectron && window.electronAPI?.isFirstRun) {
      const isFirst = await window.electronAPI.isFirstRun();
      if (!isFirst) {
        this.completed.emit();
      }
    }
    // In browser mode, always show wizard for demo
  }
  
  nextStep(): void {
    this.step.update(s => Math.min(s + 1, 3));
  }
  
  prevStep(): void {
    this.step.update(s => Math.max(s - 1, 1));
    this.validationError.set(null);
  }
  
  async validateAndNext(): Promise<void> {
    if (!this.apiKey) return;
    
    this.isValidating.set(true);
    this.validationError.set(null);
    
    try {
      // First, save the API key
      if (isElectron && window.electronAPI?.setApiKey) {
        await window.electronAPI.setApiKey(this.apiKey);
      } else {
        // Browser fallback: store in localStorage
        localStorage.setItem('anthropic_api_key', this.apiKey);
      }
      
      // Validate by making a test request to the health endpoint
      // (In a real implementation, you might want to test the actual API)
      const valid = await this.validateApiKey(this.apiKey);
      
      if (valid) {
        this.nextStep();
      } else {
        this.validationError.set('Invalid API key. Please check and try again.');
      }
    } catch (e) {
      this.validationError.set('Failed to validate API key. Please try again.');
    } finally {
      this.isValidating.set(false);
    }
  }
  
  private async validateApiKey(key: string): Promise<boolean> {
    // Basic format validation
    if (!key.startsWith('sk-ant-')) {
      return false;
    }
    if (key.length < 50) {
      return false;
    }
    
    // For now, accept if format looks valid
    // In production, you'd want to make a test API call
    return true;
  }
  
  async selectFolder(): Promise<void> {
    let folderPath: string | null = null;
    
    if (isElectron && window.electronAPI?.selectFolder) {
      folderPath = await window.electronAPI.selectFolder();
    } else {
      // Browser fallback
      folderPath = prompt('Enter workspace folder path:');
    }
    
    if (folderPath) {
      this.selectedFolder.set(folderPath);
      
      // Also set the workspace in the service
      await this.workspaceService.setWorkspace(folderPath);
    }
  }
  
  async finish(): Promise<void> {
    // Restart the backend if needed to pick up the new API key
    if (isElectron && window.electronAPI?.restartBackend) {
      await window.electronAPI.restartBackend();
    }
    
    this.completed.emit();
  }
  
  skip(): void {
    this.skipped.emit();
  }
  
  openExternal(event: Event, url: string): void {
    if (isElectron && window.electronAPI?.openExternal) {
      event.preventDefault();
      window.electronAPI.openExternal(url);
    }
    // In browser mode, let the link open normally
  }
}

