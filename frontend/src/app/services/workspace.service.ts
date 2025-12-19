import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, from, of, catchError, switchMap, tap } from 'rxjs';

export interface WorkspaceInfo {
  root_path: string;
  git_enabled: boolean;
  git_remote?: string;
  git_branch?: string;
}

@Injectable({
  providedIn: 'root'
})
export class WorkspaceService {
  // Signals for reactive state
  readonly workspace = signal<WorkspaceInfo | null>(null);
  readonly isLoading = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  
  // Computed values
  readonly workspaceName = computed(() => {
    const ws = this.workspace();
    if (!ws) return 'No workspace';
    // Get the last part of the path
    const parts = ws.root_path.replace(/\\/g, '/').split('/');
    return parts[parts.length - 1] || ws.root_path;
  });
  
  readonly isGitRepo = computed(() => this.workspace()?.git_enabled ?? false);
  readonly gitBranch = computed(() => this.workspace()?.git_branch ?? null);
  
  // Check if running in Electron
  readonly isElectron = typeof window !== 'undefined' && !!window.electronAPI;
  
  private readonly apiUrl = this.getApiUrl();
  
  constructor(private http: HttpClient) {
    // Load current workspace on init
    this.loadCurrentWorkspace();
  }
  
  /**
   * Get the API URL, using Electron IPC to get port if available
   */
  private getApiUrl(): string {
    // Default URL for browser dev mode
    return 'http://localhost:8000/api';
  }
  
  /**
   * Initialize the API URL by getting the backend port from Electron
   */
  async initializeApiUrl(): Promise<void> {
    if (this.isElectron && window.electronAPI?.getBackendPort) {
      try {
        const port = await window.electronAPI.getBackendPort();
        // Note: We can't change the readonly apiUrl here, 
        // so we'd need to make requests with the port directly
      } catch (e) {
        console.warn('Failed to get backend port from Electron:', e);
      }
    }
  }
  
  /**
   * Load the current workspace from the backend
   */
  loadCurrentWorkspace(): void {
    this.isLoading.set(true);
    this.error.set(null);
    
    this.http.get<WorkspaceInfo>(`${this.apiUrl}/workspace/current`).pipe(
      catchError(err => {
        console.error('Failed to load current workspace:', err);
        this.error.set(err.error?.detail || 'Failed to load workspace');
        return of(null);
      })
    ).subscribe(workspace => {
      this.workspace.set(workspace);
      this.isLoading.set(false);
    });
  }
  
  /**
   * Open folder picker and select workspace
   * Uses Electron's native dialog if available, falls back to prompt
   */
  async selectWorkspace(): Promise<boolean> {
    let folderPath: string | null = null;
    
    if (this.isElectron && window.electronAPI?.selectFolder) {
      // Use Electron's native folder picker
      try {
        folderPath = await window.electronAPI.selectFolder();
      } catch (e) {
        console.error('Electron folder picker failed:', e);
        this.error.set('Failed to open folder picker');
        return false;
      }
    } else {
      // Fallback for browser dev mode: prompt for path
      folderPath = prompt(
        'Enter workspace folder path:\n\n' +
        '(Note: In the Electron app, a native folder picker will be shown)'
      );
    }
    
    if (!folderPath) {
      return false; // User cancelled
    }
    
    return this.setWorkspace(folderPath);
  }
  
  /**
   * Set workspace to a specific path
   */
  async setWorkspace(path: string): Promise<boolean> {
    this.isLoading.set(true);
    this.error.set(null);
    
    return new Promise((resolve) => {
      this.http.post<WorkspaceInfo>(`${this.apiUrl}/workspace/select`, { path }).pipe(
        catchError(err => {
          console.error('Failed to select workspace:', err);
          this.error.set(err.error?.detail || 'Failed to select workspace');
          this.isLoading.set(false);
          resolve(false);
          return of(null);
        })
      ).subscribe(workspace => {
        if (workspace) {
          this.workspace.set(workspace);
          this.isLoading.set(false);
          resolve(true);
        }
      });
    });
  }
  
  /**
   * Refresh current workspace info
   */
  refresh(): void {
    this.loadCurrentWorkspace();
  }
}

