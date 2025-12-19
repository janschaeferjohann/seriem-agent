---
name: Frontend Settings Page
overview: Add a settings page to configure API keys and Git credentials, with global defaults and per-workspace overrides. Settings will be accessible via a gear icon in the header and stored using Electron's secure storage for sensitive data.
todos:
  - id: electron-store
    content: Add electron-store to desktop/package.json and implement IPC handlers in main.js
    status: pending
  - id: preload-ipc
    content: Update preload.js with settings IPC bridge methods
    status: pending
  - id: backend-settings-api
    content: Create backend/app/api/settings.py with workspace settings endpoints
    status: pending
  - id: settings-service
    content: Create frontend settings.service.ts with Electron IPC and browser fallback
    status: pending
  - id: settings-component
    content: Create settings panel component with API key and Git credential forms
    status: pending
  - id: header-integration
    content: Add settings gear icon to app header and wire up panel toggle
    status: pending
  - id: electron-types
    content: Add TypeScript definitions for window.electronAPI
    status: pending
  - id: browser-fallback
    content: Implement localStorage fallback for dev mode + dev mode warning banner
    status: pending
---

# Frontend Settings Page

## Architecture Overview

Settings will have two layers:

- **Global settings**: Stored in Electron secure storage (API keys, default Git credentials)
- **Per-workspace settings**: Stored as `.seriem/settings.json` in the workspace root (overrides global)
````mermaid
flowchart TD
  subgraph electron [Electron Layer]
    secureStore[Electron_Secure_Storage]
    preload[preload.js_IPC_Bridge]
  end
  
  subgraph frontend [Angular Frontend]
    settingsUI[Settings_Panel_Component]
    settingsService[Settings_Service]
  end
  
  subgraph backend [FastAPI Backend]
    settingsAPI[Settings_API_Endpoints]
    workspaceSettings[Workspace_Settings_File]
  end
  
  settingsUI --> settingsService
  settingsService -->|global_settings_IPC| preload
  preload --> secureStore
  settingsService -->|workspace_settings_HTTP| settingsAPI
  settingsAPI --> workspaceSettings
```




## Settings Structure

```typescript
interface GlobalSettings {
  anthropicApiKey: string;          // Required for LLM calls
  gitCredentials?: {                // Optional override for system git
    username: string;
    token: string;                  // PAT or password
  };
}

interface WorkspaceSettings {
  useGlobalGitCredentials: boolean; // true = use global, false = use system git
  gitCredentialsOverride?: {        // Only if useGlobalGitCredentials is true
    username: string;
    token: string;
  };
}
```



## Git Handling Logic

1. **Default**: Use system git (credential helpers handle auth automatically)
2. **Global override**: If `gitCredentials` set in global settings, use for all workspaces (unless workspace opts out)
3. **Per-workspace override**: Workspace can override with its own credentials or explicitly use system git

## Implementation

### Phase 1: Electron IPC for Secure Storage

**Modify** [`desktop/preload.js`](desktop/preload.js) (per the plan, this file is NEW):

```javascript
contextBridge.exposeInMainWorld('electronAPI', {
  // Existing
  selectFolder: () => ipcRenderer.invoke('dialog:selectFolder'),
  
  // Settings - global (secure storage)
  getGlobalSettings: () => ipcRenderer.invoke('settings:getGlobal'),
  setGlobalSettings: (settings) => ipcRenderer.invoke('settings:setGlobal', settings),
  
  // Individual sensitive fields (for partial updates)
  setApiKey: (key) => ipcRenderer.invoke('settings:setApiKey', key),
  setGitCredentials: (creds) => ipcRenderer.invoke('settings:setGitCredentials', creds),
});
```

**Modify** `desktop/main.js` - add IPC handlers using `electron-store` with encryption:

```javascript
const Store = require('electron-store');
const store = new Store({ encryptionKey: 'seriem-agent-key' });

ipcMain.handle('settings:getGlobal', () => ({
  anthropicApiKey: store.get('anthropicApiKey', ''),
  gitCredentials: store.get('gitCredentials', null),
}));

ipcMain.handle('settings:setGlobal', (_, settings) => {
  if (settings.anthropicApiKey !== undefined) store.set('anthropicApiKey', settings.anthropicApiKey);
  if (settings.gitCredentials !== undefined) store.set('gitCredentials', settings.gitCredentials);
  return true;
});
```



### Phase 2: Backend API for Workspace Settings

**New file** `backend/app/api/settings.py`:| Endpoint | Method | Description ||----------|--------|-------------|| `/api/settings/workspace` | GET | Get current workspace settings || `/api/settings/workspace` | PUT | Update workspace settings || `/api/settings/git/status` | GET | Check if workspace is a git repo, detect remote |Settings file location: `{workspace_root}/.seriem/settings.json`

### Phase 3: Frontend Settings Service

**New file** `frontend/src/app/services/settings.service.ts`:

- `getGlobalSettings()` - calls Electron IPC
- `setGlobalSettings(settings)` - calls Electron IPC
- `getWorkspaceSettings()` - HTTP to backend
- `setWorkspaceSettings(settings)` - HTTP to backend
- `getEffectiveGitCredentials()` - resolves which credentials to use
- Signals for reactive state: `globalSettings`, `workspaceSettings`, `isLoading`

### Phase 4: Settings UI Component

**New file** `frontend/src/app/components/settings/settings.component.ts`:Modal/slide-out panel with sections:

1. **API Configuration**

- Anthropic API Key (password field with show/hide toggle)
- Connection test button (calls `/health` or a test endpoint)

2. **Git Configuration**

- Status indicator: "Git detected" / "Not a git repository"
- Radio: "Use system git credentials" / "Use custom credentials"
- If custom: Username + Token fields
- Scope selector: "Apply to all workspaces" / "This workspace only"

3. **Workspace Info** (read-only)

- Current workspace path
- Git remote URL (if detected)

**UI Pattern**: Slide-out panel from the right (consistent with potential future "Pending Changes" panel from the proposal layer plan).

### Phase 5: Header Integration

**Modify** [`frontend/src/app/app.component.ts`](frontend/src/app/app.component.ts):Add settings gear icon to header between logo and status:

```html
<button class="settings-btn" (click)="openSettings()" title="Settings">
  <span class="settings-icon">⚙</span>
</button>
```

Add `showSettings` signal and conditional render of `<app-settings>`.

## Files to Create/Modify

| File | Change |
|------|--------|
| `desktop/main.js` | Add `electron-store` + IPC handlers for settings |
| `desktop/preload.js` | Expose settings IPC methods |
| `desktop/package.json` | Add `electron-store` dependency |
| `backend/app/api/settings.py` | NEW: Workspace settings endpoints |
| [`backend/app/api/routes.py`](backend/app/api/routes.py) | Import and include settings router |
| `frontend/src/app/services/settings.service.ts` | NEW: Settings state management with browser fallback |
| `frontend/src/app/components/settings/settings.component.ts` | NEW: Settings UI |
| [`frontend/src/app/app.component.ts`](frontend/src/app/app.component.ts) | Add settings button + panel toggle + dev mode banner |
| `frontend/src/electron.d.ts` | NEW: TypeScript types for `window.electronAPI` |

## Runtime Environment Detection

The frontend needs to detect whether it's running in Electron or browser (for dev):

```typescript
// settings.service.ts
@Injectable({ providedIn: 'root' })
export class SettingsService {
  private readonly isElectron = !!(window as any).electronAPI;
  
  readonly globalSettings = signal<GlobalSettings | null>(null);
  readonly workspaceSettings = signal<WorkspaceSettings | null>(null);
  
  constructor(private http: HttpClient) {}
  
  async loadGlobalSettings(): Promise<GlobalSettings> {
    if (this.isElectron) {
      // Production: use Electron secure storage
      const settings = await window.electronAPI!.getGlobalSettings();
      this.globalSettings.set(settings);
      return settings;
    } else {
      // Dev mode: fall back to localStorage (NOT SECURE - dev only!)
      console.warn('Running outside Electron - using localStorage (insecure, dev only)');
      const stored = localStorage.getItem('seriem_dev_settings');
      const settings: GlobalSettings = stored 
        ? JSON.parse(stored) 
        : { anthropicApiKey: '', gitCredentials: null };
      this.globalSettings.set(settings);
      return settings;
    }
  }
  
  async saveGlobalSettings(settings: Partial<GlobalSettings>): Promise<boolean> {
    if (this.isElectron) {
      return window.electronAPI!.setGlobalSettings(settings);
    } else {
      // Dev mode fallback
      const current = this.globalSettings() || { anthropicApiKey: '', gitCredentials: null };
      const updated = { ...current, ...settings };
      localStorage.setItem('seriem_dev_settings', JSON.stringify(updated));
      this.globalSettings.set(updated);
      return true;
    }
  }
  
  // Workspace selection also needs fallback
  async selectFolder(): Promise<string | null> {
    if (this.isElectron) {
      return window.electronAPI!.selectFolder();
    } else {
      // Dev mode: prompt for path or use fixed ./storage
      const path = prompt('Enter workspace path (dev mode):', './storage');
      return path;
    }
  }
}
```

### Dev Mode Indicator

Show a warning banner when running outside Electron:

```typescript
// app.component.ts
@if (!isElectron) {
  <div class="dev-mode-banner">
    Running in browser dev mode. Settings stored in localStorage (not secure).
  </div>
}
```



## Validation Rules

- **API Key**: Required, must start with `sk-ant-` 
- **Git Token**: If provided, username is also required
- **Workspace settings file**: Backend validates JSON schema on write

## First-Run Integration

The settings page connects to the first-run wizard (see [local_proposal_layer](local_proposal_layer_bd7aa7a7.plan.md) Phase 5):

1. On app startup, check if API key is configured
2. If not, show first-run wizard before main UI
3. Wizard collects API key and initial workspace
4. After wizard completes, settings are persisted and main UI loads





````