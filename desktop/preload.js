/**
 * Seriem Agent - Preload Script
 * 
 * Exposes a secure API to the renderer process (Angular frontend)
 * using contextBridge for context isolation.
 */

const { contextBridge, ipcRenderer } = require('electron');

/**
 * Electron API exposed to the frontend
 * Access via window.electronAPI in the renderer
 */
contextBridge.exposeInMainWorld('electronAPI', {
  // ============================================================================
  // Dialog APIs
  // ============================================================================
  
  /**
   * Open native folder picker dialog
   * @returns {Promise<string|null>} Selected folder path or null if cancelled
   */
  selectFolder: () => ipcRenderer.invoke('dialog:selectFolder'),

  // ============================================================================
  // Configuration APIs
  // ============================================================================
  
  /**
   * Get the stored Anthropic API key
   * @returns {Promise<string>} The API key (may be empty)
   */
  getApiKey: () => ipcRenderer.invoke('config:getApiKey'),
  
  /**
   * Set the Anthropic API key
   * @param {string} key - The API key to store
   * @returns {Promise<boolean>} True if successful
   */
  setApiKey: (key) => ipcRenderer.invoke('config:setApiKey', key),
  
  /**
   * Get the port the backend is running on
   * @returns {Promise<number>} The backend port number
   */
  getBackendPort: () => ipcRenderer.invoke('config:getBackendPort'),

  // ============================================================================
  // Settings APIs
  // ============================================================================
  
  /**
   * Get all global settings
   * @returns {Promise<GlobalSettings>} Global settings object
   */
  getGlobalSettings: () => ipcRenderer.invoke('settings:getGlobal'),
  
  /**
   * Update global settings
   * @param {Partial<GlobalSettings>} settings - Settings to update
   * @returns {Promise<boolean>} True if successful
   */
  setGlobalSettings: (settings) => ipcRenderer.invoke('settings:setGlobal', settings),
  
  /**
   * Set Git credentials
   * @param {GitCredentials|null} creds - Git credentials or null to clear
   * @returns {Promise<boolean>} True if successful
   */
  setGitCredentials: (creds) => ipcRenderer.invoke('settings:setGitCredentials', creds),

  // ============================================================================
  // Shell APIs
  // ============================================================================
  
  /**
   * Open a URL in the default browser
   * @param {string} url - URL to open
   * @returns {Promise<void>}
   */
  openExternal: (url) => ipcRenderer.invoke('shell:openExternal', url),

  // ============================================================================
  // Application APIs
  // ============================================================================
  
  /**
   * Check if this is the first run (no API key configured)
   * @returns {Promise<boolean>} True if first run
   */
  isFirstRun: () => ipcRenderer.invoke('app:isFirstRun'),
  
  /**
   * Restart the backend server
   * @returns {Promise<boolean>} True if backend restarted successfully
   */
  restartBackend: () => ipcRenderer.invoke('app:restartBackend'),
});

// Log that preload script loaded successfully
console.log('Seriem Agent preload script loaded');

