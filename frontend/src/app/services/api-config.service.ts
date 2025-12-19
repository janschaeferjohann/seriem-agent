/**
 * API Configuration Service
 * 
 * Centralizes all API URL configuration. In Electron mode, queries
 * the backend port from the main process. In browser mode, uses
 * the default development port.
 */

import { Injectable, signal } from '@angular/core';
import { isElectron } from '../utils/environment';

const DEFAULT_PORT = 8000;
const DEFAULT_HOST = 'localhost';

@Injectable({
  providedIn: 'root'
})
export class ApiConfigService {
  private _port = signal(DEFAULT_PORT);
  private _initialized = false;

  /**
   * Get the HTTP API base URL (e.g., http://localhost:8000/api)
   */
  get apiUrl(): string {
    return `http://${DEFAULT_HOST}:${this._port()}/api`;
  }

  /**
   * Get the WebSocket base URL (e.g., ws://localhost:8000)
   */
  get wsUrl(): string {
    return `ws://${DEFAULT_HOST}:${this._port()}`;
  }

  /**
   * Get just the base URL without /api suffix (e.g., http://localhost:8000)
   */
  get baseUrl(): string {
    return `http://${DEFAULT_HOST}:${this._port()}`;
  }

  /**
   * Get the current port number
   */
  get port(): number {
    return this._port();
  }

  /**
   * Initialize the service by querying the backend port from Electron.
   * This should be called early in app initialization.
   */
  async initialize(): Promise<void> {
    if (this._initialized) return;

    if (isElectron && window.electronAPI?.getBackendPort) {
      try {
        const port = await window.electronAPI.getBackendPort();
        if (port && port > 0) {
          this._port.set(port);
        }
      } catch {
        // Fall back to default port
      }
    }

    this._initialized = true;
  }
}

