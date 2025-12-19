/**
 * TypeScript definitions for the Electron API
 * Exposed via preload.js contextBridge
 */

export interface GitCredentials {
  username: string;
  token: string;
}

export interface GlobalSettings {
  anthropicApiKey: string;
  gitCredentials: GitCredentials | null;
  telemetryEnabled: boolean;
}

export interface ElectronAPI {
  // Dialog APIs
  selectFolder(): Promise<string | null>;

  // Configuration APIs
  getApiKey(): Promise<string>;
  setApiKey(key: string): Promise<boolean>;
  getBackendPort(): Promise<number>;

  // Settings APIs
  getGlobalSettings(): Promise<GlobalSettings>;
  setGlobalSettings(settings: Partial<GlobalSettings>): Promise<boolean>;
  setGitCredentials(creds: GitCredentials | null): Promise<boolean>;

  // Shell APIs
  openExternal(url: string): Promise<void>;

  // Application APIs
  isFirstRun(): Promise<boolean>;
  restartBackend(): Promise<boolean>;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}

export {};

