/**
 * Settings Component
 * 
 * A slide-out panel for managing global and workspace settings.
 * Includes API key configuration, Git credentials, and workspace info.
 */

import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatRadioModule } from '@angular/material/radio';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';

import { SettingsService, WorkspaceSettings } from '../../services/settings.service';
import { TelemetryService } from '../../services/telemetry.service';

// Check if running in Electron
const isElectron = typeof window !== 'undefined' && !!window.electronAPI;

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatRadioModule,
    MatSlideToggleModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
    MatDividerModule,
  ],
  template: `
    <div class="settings-panel" [class.open]="settingsService.isSettingsPanelOpen()">
      <!-- Header -->
      <div class="panel-header">
        <div class="header-left">
          <mat-icon>settings</mat-icon>
          <span class="header-title">Settings</span>
        </div>
        <button mat-icon-button 
                matTooltip="Close settings"
                (click)="settingsService.closeSettingsPanel()">
          <mat-icon>close</mat-icon>
        </button>
      </div>
      
      <!-- Content -->
      <div class="panel-content">
        @if (settingsService.isLoading()) {
          <div class="loading-overlay">
            <mat-spinner diameter="32"></mat-spinner>
          </div>
        }
        
        @if (settingsService.error()) {
          <div class="error-banner">
            <mat-icon>error_outline</mat-icon>
            <span>{{ settingsService.error() }}</span>
          </div>
        }
        
        <!-- API Configuration Section -->
        <section class="settings-section">
          <h3 class="section-title">
            <mat-icon>vpn_key</mat-icon>
            API Configuration
          </h3>
          
          <div class="form-group">
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Anthropic API Key</mat-label>
              <input matInput 
                     [type]="showApiKey() ? 'text' : 'password'"
                     [(ngModel)]="apiKey"
                     placeholder="sk-ant-..."
                     (blur)="saveApiKey()">
              <button mat-icon-button matSuffix 
                      (click)="toggleApiKeyVisibility()"
                      matTooltip="{{ showApiKey() ? 'Hide' : 'Show' }} API key">
                <mat-icon>{{ showApiKey() ? 'visibility_off' : 'visibility' }}</mat-icon>
              </button>
            </mat-form-field>
            
            @if (apiKeyStatus()) {
              <div class="field-status" [class.success]="apiKeyStatus() === 'saved'" [class.error]="apiKeyStatus() === 'error'">
                <mat-icon>{{ apiKeyStatus() === 'saved' ? 'check_circle' : 'error' }}</mat-icon>
                <span>{{ apiKeyStatus() === 'saved' ? 'API key saved' : 'Error saving API key' }}</span>
              </div>
            }
            
            <a href="https://console.anthropic.com/settings/keys" 
               target="_blank" 
               class="help-link"
               (click)="openExternal($event, 'https://console.anthropic.com/settings/keys')">
              <mat-icon>open_in_new</mat-icon>
              Get an API key from Anthropic Console
            </a>
          </div>
        </section>
        
        <mat-divider></mat-divider>
        
        <!-- Git Configuration Section -->
        <section class="settings-section">
          <h3 class="section-title">
            <mat-icon>source</mat-icon>
            Git Configuration
          </h3>
          
          <!-- Git Status -->
          <div class="git-status">
            @if (settingsService.gitStatus(); as gitStatus) {
              @if (gitStatus.is_git_repo) {
                <div class="status-indicator success">
                  <mat-icon>check_circle</mat-icon>
                  <span>Git repository detected</span>
                </div>
                @if (gitStatus.current_branch) {
                  <div class="git-info">
                    <span class="label">Branch:</span>
                    <span class="value">{{ gitStatus.current_branch }}</span>
                  </div>
                }
                @if (gitStatus.remote_url) {
                  <div class="git-info">
                    <span class="label">Remote:</span>
                    <span class="value remote-url">{{ gitStatus.remote_url }}</span>
                  </div>
                }
              } @else {
                <div class="status-indicator neutral">
                  <mat-icon>info</mat-icon>
                  <span>Not a git repository</span>
                </div>
              }
            } @else {
              <div class="status-indicator neutral">
                <mat-icon>hourglass_empty</mat-icon>
                <span>Checking git status...</span>
              </div>
            }
          </div>
          
          <!-- Git Credentials Mode -->
          <div class="form-group">
            <label class="group-label">Credentials Mode</label>
            <mat-radio-group [(ngModel)]="gitCredentialsMode" 
                             (change)="onGitModeChange()"
                             class="radio-group">
              <mat-radio-button value="system">
                <div class="radio-content">
                  <span class="radio-label">Use system git credentials</span>
                  <span class="radio-hint">Let git credential helper manage authentication</span>
                </div>
              </mat-radio-button>
              <mat-radio-button value="custom">
                <div class="radio-content">
                  <span class="radio-label">Use custom credentials</span>
                  <span class="radio-hint">Provide a username and personal access token</span>
                </div>
              </mat-radio-button>
            </mat-radio-group>
          </div>
          
          <!-- Custom Git Credentials -->
          @if (gitCredentialsMode === 'custom') {
            <div class="form-group nested">
              <mat-form-field appearance="outline" class="full-width">
                <mat-label>Git Username</mat-label>
                <input matInput 
                       [(ngModel)]="gitUsername"
                       placeholder="username">
              </mat-form-field>
              
              <mat-form-field appearance="outline" class="full-width">
                <mat-label>Git Token (PAT)</mat-label>
                <input matInput 
                       [type]="showGitToken() ? 'text' : 'password'"
                       [(ngModel)]="gitToken"
                       placeholder="ghp_... or personal access token">
                <button mat-icon-button matSuffix 
                        (click)="toggleGitTokenVisibility()"
                        matTooltip="{{ showGitToken() ? 'Hide' : 'Show' }} token">
                  <mat-icon>{{ showGitToken() ? 'visibility_off' : 'visibility' }}</mat-icon>
                </button>
              </mat-form-field>
              
              <!-- Scope Selector -->
              <div class="scope-selector">
                <label class="scope-label">Apply to:</label>
                <mat-radio-group [(ngModel)]="gitCredentialsScope" class="scope-radio-group">
                  <mat-radio-button value="global">All workspaces</mat-radio-button>
                  <mat-radio-button value="workspace">This workspace only</mat-radio-button>
                </mat-radio-group>
              </div>
              
              <button mat-stroked-button 
                      color="primary" 
                      (click)="saveGitCredentials()"
                      [disabled]="!gitUsername || !gitToken">
                <mat-icon>save</mat-icon>
                Save Git Credentials
              </button>
              
              @if (gitCredentialsStatus()) {
                <div class="field-status" 
                     [class.success]="gitCredentialsStatus() === 'saved'" 
                     [class.error]="gitCredentialsStatus() === 'error'">
                  <mat-icon>{{ gitCredentialsStatus() === 'saved' ? 'check_circle' : 'error' }}</mat-icon>
                  <span>{{ gitCredentialsStatus() === 'saved' ? 'Git credentials saved' : 'Error saving credentials' }}</span>
                </div>
              }
            </div>
          }
        </section>
        
        <mat-divider></mat-divider>
        
        <!-- Workspace Info Section -->
        <section class="settings-section">
          <h3 class="section-title">
            <mat-icon>folder</mat-icon>
            Workspace
          </h3>
          
          <div class="workspace-info">
            @if (settingsService.gitStatus(); as gitStatus) {
              <div class="info-row">
                <span class="label">Path:</span>
                <span class="value path">{{ gitStatus.workspace_path }}</span>
              </div>
            }
          </div>
        </section>
        
        <mat-divider></mat-divider>
        
        <!-- Advanced Section -->
        <section class="settings-section">
          <h3 class="section-title">
            <mat-icon>tune</mat-icon>
            Advanced
          </h3>
          
          <div class="form-group">
            <mat-slide-toggle [(ngModel)]="telemetryEnabled" (change)="saveTelemetryPreference()">
              Enable telemetry
            </mat-slide-toggle>
            <span class="toggle-hint">Help improve Seriem Agent by sharing anonymous usage data</span>
            
            <button mat-stroked-button 
                    class="view-telemetry-btn"
                    (click)="openTelemetryViewer()">
              <mat-icon>analytics</mat-icon>
              View Telemetry
            </button>
          </div>
          
          @if (isElectron) {
            <button mat-stroked-button 
                    (click)="restartBackend()"
                    [disabled]="isRestarting()">
              @if (isRestarting()) {
                <mat-spinner diameter="14"></mat-spinner>
              } @else {
                <mat-icon>refresh</mat-icon>
              }
              Restart Backend
            </button>
          }
        </section>
        
        <!-- Dev Mode Warning (at end of panel) -->
        @if (!isElectron) {
          <mat-divider></mat-divider>
          <div class="dev-mode-banner">
            <mat-icon>warning</mat-icon>
            <span>Running in browser dev mode. Settings stored in localStorage (not secure).</span>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
    
    .settings-panel {
      position: fixed;
      top: 0;
      right: 0;
      bottom: 0;
      width: 360px;
      max-width: 100vw;
      background: var(--bg-secondary);
      border-left: 1px solid var(--border-default);
      display: flex;
      flex-direction: column;
      transform: translateX(100%);
      transition: transform 0.25s ease-out;
      z-index: 100;
      
      &.open {
        transform: translateX(0);
      }
    }
    
    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 var(--spacing-md);
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border-default);
      height: 48px;
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
      }
      
      .header-title {
        font-size: 14px;
        font-weight: 600;
      }
      
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
    
    .panel-content {
      flex: 1;
      overflow-y: auto;
      padding: var(--spacing-md);
      
      &::-webkit-scrollbar {
        width: 6px;
      }
      
      &::-webkit-scrollbar-track {
        background: var(--bg-tertiary);
      }
      
      &::-webkit-scrollbar-thumb {
        background: var(--kw-darkgrey);
        border-radius: 3px;
      }
    }
    
    .loading-overlay {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: var(--spacing-xl);
    }
    
    .error-banner, .dev-mode-banner {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm) var(--spacing-md);
      border-radius: var(--radius-sm);
      font-size: 12px;
      margin-bottom: var(--spacing-md);
      
      mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
        flex-shrink: 0;
      }
    }
    
    .error-banner {
      background: rgba(248, 81, 73, 0.1);
      border: 1px solid var(--accent-error);
      color: var(--accent-error);
    }
    
    .dev-mode-banner {
      background: rgba(245, 158, 11, 0.1);
      border: 1px solid var(--accent-warning);
      color: var(--accent-warning);
    }
    
    .settings-section {
      padding: var(--spacing-md) 0;
      
      &:first-of-type {
        padding-top: 0;
      }
    }
    
    .section-title {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      margin: 0 0 var(--spacing-md) 0;
      
      mat-icon {
        font-size: 14px;
        width: 14px;
        height: 14px;
      }
    }
    
    .form-group {
      margin-bottom: var(--spacing-md);
      
      &.nested {
        margin-left: var(--spacing-md);
        padding-left: var(--spacing-md);
        border-left: 2px solid var(--border-subtle);
      }
    }
    
    .group-label {
      display: block;
      font-size: 12px;
      font-weight: 500;
      color: var(--text-secondary);
      margin-bottom: 6px;
    }
    
    .full-width {
      width: 100%;
    }
    
    /* Compact form fields */
    ::ng-deep .mat-mdc-form-field {
      .mat-mdc-text-field-wrapper {
        padding: 0 10px !important;
        height: 40px !important;
      }
      
      .mat-mdc-form-field-flex {
        height: 40px !important;
        align-items: center !important;
      }
      
      .mat-mdc-form-field-infix {
        min-height: 40px !important;
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
        --mdc-outlined-text-field-caret-color: #E30018;
      }
      
      input {
        font-size: 12px !important;
        line-height: 40px !important;
        height: 40px !important;
        padding: 0 !important;
      }
      
      .mdc-floating-label {
        top: 50% !important;
        transform: translateY(-50%) !important;
        font-size: 12px !important;
      }
      
      .mdc-floating-label--float-above {
        transform: translateY(-130%) scale(0.75) !important;
      }
      
      .mat-mdc-form-field-icon-suffix {
        display: flex;
        align-items: center;
        height: 40px;
        
        button {
          width: 24px !important;
          height: 24px !important;
          
          mat-icon {
            font-size: 16px !important;
            width: 16px !important;
            height: 16px !important;
          }
        }
      }
    }
    
    .field-status {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      font-size: 12px;
      margin-top: var(--spacing-xs);
      
      mat-icon {
        font-size: 14px;
        width: 14px;
        height: 14px;
      }
      
      &.success {
        color: var(--accent-secondary);
      }
      
      &.error {
        color: var(--accent-error);
      }
    }
    
    .help-link {
      display: inline-flex;
      align-items: center;
      gap: var(--spacing-xs);
      color: var(--kw-red);
      font-size: 11px;
      text-decoration: none;
      
      mat-icon {
        font-size: 12px;
        width: 12px;
        height: 12px;
      }
      
      &:hover {
        text-decoration: underline;
      }
    }
    
    .git-status {
      margin-bottom: var(--spacing-md);
    }
    
    .status-indicator {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 10px;
      border-radius: var(--radius-sm);
      font-size: 11px;
      margin-bottom: 6px;
      
      mat-icon {
        font-size: 14px;
        width: 14px;
        height: 14px;
      }
      
      &.success {
        background: rgba(81, 165, 86, 0.1);
        color: var(--accent-secondary);
      }
      
      &.neutral {
        background: var(--bg-tertiary);
        color: var(--text-secondary);
      }
    }
    
    .git-info {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      font-size: 10px;
      padding: 3px 10px;
      
      .label {
        color: var(--text-muted);
        font-weight: 500;
        min-width: 48px;
      }
      
      .value {
        color: var(--text-primary);
        font-family: var(--font-mono);
        
        &.remote-url {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }
    
    .radio-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    
    .radio-content {
      display: flex;
      flex-direction: column;
      margin-left: 4px;
      gap: 1px;
    }
    
    .radio-label {
      font-size: 12px;
      font-weight: 500;
      line-height: 1.3;
    }
    
    .radio-hint {
      font-size: 10px;
      color: var(--text-muted);
      line-height: 1.3;
    }
    
    .scope-selector {
      margin: var(--spacing-md) 0;
      
      .scope-label {
        display: block;
        font-size: 11px;
        color: var(--text-muted);
        margin-bottom: 6px;
      }
      
      .scope-radio-group {
        display: flex;
        gap: var(--spacing-md);
        
        mat-radio-button {
          font-size: 11px;
        }
      }
    }
    
    .workspace-info {
      background: var(--bg-tertiary);
      border-radius: var(--radius-sm);
      padding: 10px 12px;
    }
    
    .info-row {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      font-size: 11px;
      
      .label {
        color: var(--text-muted);
        font-weight: 500;
        flex-shrink: 0;
        min-width: 32px;
      }
      
      .value {
        color: var(--text-primary);
        
        &.path {
          font-family: var(--font-mono);
          font-size: 10px;
          word-break: break-all;
          line-height: 1.4;
        }
      }
    }
    
    .toggle-hint {
      display: block;
      font-size: 10px;
      color: var(--text-muted);
      margin-top: 4px;
      margin-left: 44px; /* Align with toggle label */
      line-height: 1.4;
    }
    
    .view-telemetry-btn {
      margin-top: 8px;
      margin-left: 44px;
      font-size: 11px;
      height: 28px;
      line-height: 28px;
      padding: 0 12px;
      
      mat-icon {
        font-size: 14px;
        width: 14px;
        height: 14px;
        margin-right: 4px;
      }
    }
    
    /* Compact slide toggle - override Material blue */
    ::ng-deep mat-slide-toggle {
      --mdc-switch-selected-handle-color: #E30018 !important;
      --mdc-switch-selected-track-color: rgba(227, 0, 24, 0.35) !important;
      --mdc-switch-selected-hover-handle-color: #E30018 !important;
      --mdc-switch-selected-focus-handle-color: #E30018 !important;
      --mdc-switch-selected-pressed-handle-color: #E30018 !important;
      --mdc-switch-selected-hover-track-color: rgba(227, 0, 24, 0.35) !important;
      --mdc-switch-selected-focus-track-color: rgba(227, 0, 24, 0.35) !important;
      --mdc-switch-selected-pressed-track-color: rgba(227, 0, 24, 0.35) !important;
      --mdc-switch-selected-icon-color: transparent !important;
      --mdc-switch-unselected-icon-color: transparent !important;
      
      .mdc-switch__icons {
        display: none !important;
      }
      
      .mdc-switch__track::after {
        background: rgba(227, 0, 24, 0.35) !important;
      }
      
      .mdc-switch--selected .mdc-switch__handle::after {
        background: #E30018 !important;
      }
      
      .mdc-label {
        font-size: 12px;
        margin-left: 8px;
      }
    }
    
    mat-divider {
      margin: var(--spacing-sm) 0;
    }
    
    /* Compact buttons */
    button[mat-stroked-button] {
      height: 28px;
      padding: 0 10px;
      font-size: 11px;
      border-color: var(--border-default);
      color: var(--text-secondary);
      
      mat-icon {
        font-size: 14px;
        width: 14px;
        height: 14px;
        margin-right: 4px;
      }
      
      mat-spinner {
        display: inline-block;
        margin-right: 4px;
      }
      
      &:hover {
        background: var(--bg-hover);
        color: var(--text-primary);
      }
    }
    
    /* Radio buttons styling - override Material blue */
    ::ng-deep mat-radio-button {
      --mdc-radio-selected-icon-color: #E30018 !important;
      --mdc-radio-selected-hover-icon-color: #E30018 !important;
      --mdc-radio-selected-pressed-icon-color: #E30018 !important;
      --mdc-radio-selected-focus-icon-color: #E30018 !important;
      --mat-radio-checked-ripple-color: rgba(227, 0, 24, 0.2) !important;
      
      .mdc-radio__outer-circle {
        border-color: var(--text-secondary) !important;
      }
      
      &.mat-mdc-radio-checked .mdc-radio__outer-circle {
        border-color: #E30018 !important;
      }
      
      &.mat-mdc-radio-checked .mdc-radio__inner-circle {
        background-color: #E30018 !important;
        border-color: #E30018 !important;
      }
      
      .mdc-label {
        font-size: 12px;
      }
    }
  `]
})
export class SettingsComponent implements OnInit {
  readonly isElectron = isElectron;
  
  // API Key
  apiKey = '';
  showApiKey = signal(false);
  apiKeyStatus = signal<'saved' | 'error' | null>(null);
  
  // Git Credentials
  gitCredentialsMode: 'system' | 'custom' = 'system';
  gitUsername = '';
  gitToken = '';
  showGitToken = signal(false);
  gitCredentialsScope: 'global' | 'workspace' = 'global';
  gitCredentialsStatus = signal<'saved' | 'error' | null>(null);
  
  // Advanced
  telemetryEnabled = true;
  isRestarting = signal(false);
  
  constructor(
    public settingsService: SettingsService,
    private telemetryService: TelemetryService,
  ) {}
  
  ngOnInit(): void {
    // Load settings when component initializes
    this.loadSettings();
  }
  
  async loadSettings(): Promise<void> {
    try {
      // Load global settings
      const global = await this.settingsService.loadGlobalSettings();
      this.apiKey = global.anthropicApiKey || '';
      this.telemetryEnabled = global.telemetryEnabled ?? true;
      
      if (global.gitCredentials) {
        this.gitCredentialsMode = 'custom';
        this.gitUsername = global.gitCredentials.username;
        this.gitToken = global.gitCredentials.token;
      }
      
      // Load workspace settings
      this.settingsService.loadWorkspaceSettings().subscribe(response => {
        if (response?.settings) {
          if (!response.settings.use_global_git_credentials && response.settings.git_credentials_override) {
            this.gitCredentialsMode = 'custom';
            this.gitCredentialsScope = 'workspace';
            this.gitUsername = response.settings.git_credentials_override.username;
            this.gitToken = response.settings.git_credentials_override.token;
          }
        }
      });
      
      // Load git status
      this.settingsService.loadGitStatus().subscribe();
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  }
  
  toggleApiKeyVisibility(): void {
    this.showApiKey.update(v => !v);
  }
  
  toggleGitTokenVisibility(): void {
    this.showGitToken.update(v => !v);
  }
  
  async saveApiKey(): Promise<void> {
    if (!this.apiKey) return;
    
    try {
      const success = await this.settingsService.setApiKey(this.apiKey);
      this.apiKeyStatus.set(success ? 'saved' : 'error');
      
      // Clear status after a few seconds
      setTimeout(() => this.apiKeyStatus.set(null), 3000);
    } catch {
      this.apiKeyStatus.set('error');
    }
  }
  
  onGitModeChange(): void {
    if (this.gitCredentialsMode === 'system') {
      // Clear custom credentials when switching to system mode
      this.saveSystemGitMode();
    }
  }
  
  async saveSystemGitMode(): Promise<void> {
    try {
      // Clear global git credentials
      await this.settingsService.setGitCredentials(null);
      
      // Update workspace settings
      const workspaceSettings: WorkspaceSettings = {
        use_global_git_credentials: true,
        git_credentials_override: null,
      };
      this.settingsService.saveWorkspaceSettings(workspaceSettings).subscribe();
      
      this.gitCredentialsStatus.set('saved');
      setTimeout(() => this.gitCredentialsStatus.set(null), 3000);
    } catch {
      this.gitCredentialsStatus.set('error');
    }
  }
  
  async saveGitCredentials(): Promise<void> {
    if (!this.gitUsername || !this.gitToken) return;
    
    try {
      const credentials = {
        username: this.gitUsername,
        token: this.gitToken,
      };
      
      if (this.gitCredentialsScope === 'global') {
        // Save to global settings
        const success = await this.settingsService.setGitCredentials(credentials);
        
        // Also update workspace to use global
        const workspaceSettings: WorkspaceSettings = {
          use_global_git_credentials: true,
          git_credentials_override: null,
        };
        this.settingsService.saveWorkspaceSettings(workspaceSettings).subscribe();
        
        this.gitCredentialsStatus.set(success ? 'saved' : 'error');
      } else {
        // Save to workspace settings only
        const workspaceSettings: WorkspaceSettings = {
          use_global_git_credentials: false,
          git_credentials_override: credentials,
        };
        
        this.settingsService.saveWorkspaceSettings(workspaceSettings).subscribe({
          next: () => this.gitCredentialsStatus.set('saved'),
          error: () => this.gitCredentialsStatus.set('error'),
        });
      }
      
      // Clear status after a few seconds
      setTimeout(() => this.gitCredentialsStatus.set(null), 3000);
    } catch {
      this.gitCredentialsStatus.set('error');
    }
  }
  
  async saveTelemetryPreference(): Promise<void> {
    await this.settingsService.saveGlobalSettings({ telemetryEnabled: this.telemetryEnabled });
  }
  
  openTelemetryViewer(): void {
    // Close settings panel and open telemetry viewer
    this.settingsService.closeSettingsPanel();
    this.telemetryService.openViewer();
  }
  
  async restartBackend(): Promise<void> {
    if (!isElectron || !window.electronAPI?.restartBackend) return;
    
    this.isRestarting.set(true);
    try {
      await window.electronAPI.restartBackend();
    } catch (err) {
      console.error('Failed to restart backend:', err);
    } finally {
      this.isRestarting.set(false);
    }
  }
  
  openExternal(event: Event, url: string): void {
    if (isElectron && window.electronAPI?.openExternal) {
      event.preventDefault();
      window.electronAPI.openExternal(url);
    }
    // In browser mode, let the link open normally
  }
}

