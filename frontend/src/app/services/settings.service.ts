/**
 * Settings Service
 * 
 * Manages global settings (via Electron IPC) and workspace settings (via HTTP API).
 * Falls back to localStorage when running outside Electron (dev mode).
 */

import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, catchError, tap, firstValueFrom } from 'rxjs';
import type { GlobalSettings, GitCredentials } from '../../electron';
import { ApiConfigService } from './api-config.service';
import { isElectron } from '../utils/environment';

// Workspace settings interfaces
export interface GitCredentialsOverride {
  username: string;
  token: string;
}

export interface WorkspaceSettings {
  use_global_git_credentials: boolean;
  git_credentials_override?: GitCredentialsOverride | null;
}

export interface WorkspaceSettingsResponse {
  settings: WorkspaceSettings;
  workspace_path: string;
  settings_file_exists: boolean;
}

export interface GitStatusResponse {
  is_git_repo: boolean;
  remote_url: string | null;
  current_branch: string | null;
  workspace_path: string;
}

@Injectable({
  providedIn: 'root'
})
export class SettingsService {
  private readonly apiConfig = inject(ApiConfigService);
  
  // Environment detection
  readonly isElectron = isElectron;
  
  // Reactive state signals
  readonly globalSettings = signal<GlobalSettings | null>(null);
  readonly workspaceSettings = signal<WorkspaceSettings | null>(null);
  readonly gitStatus = signal<GitStatusResponse | null>(null);
  readonly isLoading = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly isSettingsPanelOpen = signal<boolean>(false);
  
  // Computed values
  readonly hasApiKey = computed(() => {
    const settings = this.globalSettings();
    return !!settings?.anthropicApiKey && settings.anthropicApiKey.trim().length > 0;
  });
  
  readonly effectiveGitCredentials = computed(() => {
    const global = this.globalSettings();
    const workspace = this.workspaceSettings();
    
    // If workspace says use global, or no workspace settings exist
    if (!workspace || workspace.use_global_git_credentials) {
      return global?.gitCredentials || null;
    }
    
    // Use workspace-specific override
    return workspace.git_credentials_override || null;
  });
  
  constructor(private http: HttpClient) {}
  
  // ============================================================================
  // Global Settings (Electron secure storage / localStorage fallback)
  // ============================================================================
  
  /**
   * Load global settings from Electron secure storage or localStorage
   */
  async loadGlobalSettings(): Promise<GlobalSettings> {
    this.isLoading.set(true);
    this.error.set(null);
    
    try {
      let settings: GlobalSettings;
      
      if (this.isElectron && window.electronAPI) {
        // Production: use Electron secure storage
        settings = await window.electronAPI.getGlobalSettings();
      } else {
        // Dev mode: fall back to localStorage (NOT SECURE - dev only!)
        console.warn('Running outside Electron - using localStorage (insecure, dev only)');
        const stored = localStorage.getItem('seriem_dev_settings');
        settings = stored 
          ? JSON.parse(stored) 
          : { anthropicApiKey: '', gitCredentials: null, telemetryEnabled: true };
      }
      
      this.globalSettings.set(settings);
      return settings;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load settings';
      this.error.set(message);
      throw err;
    } finally {
      this.isLoading.set(false);
    }
  }
  
  /**
   * Save global settings to Electron secure storage or localStorage
   */
  async saveGlobalSettings(settings: Partial<GlobalSettings>): Promise<boolean> {
    this.isLoading.set(true);
    this.error.set(null);
    
    try {
      if (this.isElectron && window.electronAPI) {
        // Production: use Electron secure storage
        await window.electronAPI.setGlobalSettings(settings);
      } else {
        // Dev mode fallback
        const current = this.globalSettings() || { 
          anthropicApiKey: '', 
          gitCredentials: null, 
          telemetryEnabled: true 
        };
        const updated = { ...current, ...settings };
        localStorage.setItem('seriem_dev_settings', JSON.stringify(updated));
      }
      
      // Update local state
      const current = this.globalSettings();
      if (current) {
        this.globalSettings.set({ ...current, ...settings });
      }
      
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save settings';
      this.error.set(message);
      return false;
    } finally {
      this.isLoading.set(false);
    }
  }
  
  /**
   * Set API key (convenience method)
   */
  async setApiKey(key: string): Promise<boolean> {
    return this.saveGlobalSettings({ anthropicApiKey: key });
  }
  
  /**
   * Set Git credentials (convenience method)
   */
  async setGitCredentials(creds: GitCredentials | null): Promise<boolean> {
    if (this.isElectron && window.electronAPI) {
      try {
        await window.electronAPI.setGitCredentials(creds);
        const current = this.globalSettings();
        if (current) {
          this.globalSettings.set({ ...current, gitCredentials: creds });
        }
        return true;
      } catch {
        return false;
      }
    }
    return this.saveGlobalSettings({ gitCredentials: creds });
  }
  
  // ============================================================================
  // Workspace Settings (HTTP API)
  // ============================================================================
  
  /**
   * Load workspace-specific settings from backend
   */
  loadWorkspaceSettings(): Observable<WorkspaceSettingsResponse | null> {
    this.isLoading.set(true);
    this.error.set(null);
    
    return this.http.get<WorkspaceSettingsResponse>(`${this.apiConfig.apiUrl}/settings/workspace`).pipe(
      tap(response => {
        this.workspaceSettings.set(response.settings);
        this.isLoading.set(false);
      }),
      catchError(err => {
        const message = err.error?.detail || 'Failed to load workspace settings';
        this.error.set(message);
        this.isLoading.set(false);
        return of(null);
      })
    );
  }
  
  /**
   * Save workspace-specific settings to backend
   */
  saveWorkspaceSettings(settings: WorkspaceSettings): Observable<WorkspaceSettingsResponse | null> {
    this.isLoading.set(true);
    this.error.set(null);
    
    return this.http.put<WorkspaceSettingsResponse>(`${this.apiConfig.apiUrl}/settings/workspace`, settings).pipe(
      tap(response => {
        this.workspaceSettings.set(response.settings);
        this.isLoading.set(false);
      }),
      catchError(err => {
        const message = err.error?.detail || 'Failed to save workspace settings';
        this.error.set(message);
        this.isLoading.set(false);
        return of(null);
      })
    );
  }
  
  // ============================================================================
  // Git Status
  // ============================================================================
  
  /**
   * Check git status of current workspace
   */
  loadGitStatus(): Observable<GitStatusResponse | null> {
    return this.http.get<GitStatusResponse>(`${this.apiConfig.apiUrl}/settings/git/status`).pipe(
      tap(response => {
        this.gitStatus.set(response);
      }),
      catchError(err => {
        console.error('Failed to load git status:', err);
        return of(null);
      })
    );
  }
  
  // ============================================================================
  // API Key Validation
  // ============================================================================
  
  /**
   * Validate API key by calling health endpoint
   */
  async validateApiKey(key: string): Promise<{ valid: boolean; message: string }> {
    // Basic format check
    if (!key || !key.startsWith('sk-ant-')) {
      return { valid: false, message: 'API key must start with "sk-ant-"' };
    }
    
    if (key.length < 20) {
      return { valid: false, message: 'API key appears to be too short' };
    }
    
    // Try to verify with backend health check
    // Note: Full validation would require an actual API call to Anthropic
    try {
      const response = await firstValueFrom(
        this.http.get<{ status: string }>(`${this.apiConfig.baseUrl}/health`)
      );
      if (response?.status === 'healthy') {
        return { valid: true, message: 'API key format is valid' };
      }
    } catch {
      // Backend not running - just validate format
    }
    
    return { valid: true, message: 'API key format is valid (backend not running for full validation)' };
  }
  
  // ============================================================================
  // Folder Selection (with browser fallback)
  // ============================================================================
  
  /**
   * Select a workspace folder using native dialog or prompt
   */
  async selectFolder(): Promise<string | null> {
    if (this.isElectron && window.electronAPI) {
      return window.electronAPI.selectFolder();
    } else {
      // Dev mode: prompt for path
      const path = prompt('Enter workspace path (dev mode):', './storage');
      return path;
    }
  }
  
  // ============================================================================
  // Panel Controls
  // ============================================================================
  
  /**
   * Toggle settings panel visibility
   */
  toggleSettingsPanel(): void {
    const isOpen = this.isSettingsPanelOpen();
    this.isSettingsPanelOpen.set(!isOpen);
    
    if (!isOpen) {
      // Load settings when opening
      this.loadGlobalSettings();
      this.loadWorkspaceSettings().subscribe();
      this.loadGitStatus().subscribe();
    }
  }
  
  /**
   * Open settings panel
   */
  openSettingsPanel(): void {
    this.isSettingsPanelOpen.set(true);
    this.loadGlobalSettings();
    this.loadWorkspaceSettings().subscribe();
    this.loadGitStatus().subscribe();
  }
  
  /**
   * Close settings panel
   */
  closeSettingsPanel(): void {
    this.isSettingsPanelOpen.set(false);
    this.error.set(null);
  }
}

