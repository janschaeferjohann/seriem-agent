# App Update Mechanism

## Problem Statement

Users have Seriem Agent installed as an Electron .exe. When you release new versions:

- How do they know an update is available?
- How do they get it with minimal friction?
- How do you avoid 100MB downloads for small bug fixes?

## Key Insight: Separate Shell from App Code

The Electron shell (main.js, preload.js) changes **rarely**. The actual app (Python backend + Angular frontend) changes **frequently**.**Two-tier update strategy:**| Layer | Contents | Update Frequency | Update Method ||-------|----------|------------------|---------------|| Shell | Electron main/preload, Python launcher | Rarely (breaking changes only) | Full installer download || App Code | Backend Python, Frontend Angular | Frequently | In-place zip extraction |

## Architecture

````mermaid
flowchart TD
  subgraph electron_shell [Electron Shell - Stable]
    main[main.js]
    preload[preload.js]
    launcher[Python_Launcher]
  end
  
  subgraph app_code [App Code - Updatable]
    backend[backend/]
    frontend[frontend/dist/]
  end
  
  subgraph update_flow [Update Flow]
    startup[App_Startup] --> check[Check_Version_Endpoint]
    check -->|newer_available| notify[Show_Update_Banner]
    notify -->|user_clicks_update| download[Download_app-code.zip]
    download --> extract[Extract_to_app-code/]
    extract --> restart[Restart_Backend]
  end
  
  electron_shell --> app_code
  launcher --> backend
```

## File Structure After Install

```
C:\Users\{user}\AppData\Local\SeriemAgent\
  app-1.0.0-win.exe          # Electron shell (from installer)
  resources/
    app-code/                 # UPDATABLE - extracted here
      backend/
        app/
        requirements.txt
        venv/                 # Created on first run
      frontend/
        index.html
        main.js
        ...
    version.json              # Current app-code version
```

## Version Endpoint

**Backend** `GET /api/version`:

```json
{
  "app_version": "1.2.3",
  "backend_version": "1.2.3",
  "frontend_version": "1.2.3",
  "min_shell_version": "1.0.0",
  "released_at": "2025-01-15T10:00:00Z"
}
```

**Update server** (can be same backend or separate):

`GET https://updates.yourcompany.com/seriem-agent/latest.json`:

```json
{
  "app_version": "1.2.4",
  "download_url": "https://updates.yourcompany.com/seriem-agent/app-code-1.2.4.zip",
  "shell_version": "1.0.0",
  "shell_download_url": "https://updates.yourcompany.com/seriem-agent/SeriemAgent-Setup-1.0.0.exe",
  "release_notes": "Bug fixes and performance improvements",
  "sha256": "abc123..."
}
```

## Update Flow (Detailed)

### On Electron Startup

```javascript
// main.js
async function checkForUpdates() {
  const currentVersion = require('./resources/version.json').app_version;
  
  try {
    const latest = await fetch('https://updates.yourcompany.com/seriem-agent/latest.json');
    const data = await latest.json();
    
    if (semver.gt(data.app_version, currentVersion)) {
      // Notify renderer to show update banner
      mainWindow.webContents.send('update-available', {
        version: data.app_version,
        releaseNotes: data.release_notes,
        requiresShellUpdate: semver.gt(data.shell_version, SHELL_VERSION)
      });
    }
  } catch (e) {
    // Offline or server down - silently continue
    console.log('Update check failed:', e.message);
  }
}
```

### User Clicks "Update"

```javascript
// main.js - IPC handler
ipcMain.handle('app:update', async () => {
  const latest = await fetchLatestInfo();
  
  if (semver.gt(latest.shell_version, SHELL_VERSION)) {
    // Shell update required - open download page
    shell.openExternal(latest.shell_download_url);
    return { action: 'shell_update_required' };
  }
  
  // Download app-code zip
  const zipPath = path.join(app.getPath('temp'), 'app-code-update.zip');
  await downloadFile(latest.download_url, zipPath);
  
  // Verify hash
  const hash = await computeSha256(zipPath);
  if (hash !== latest.sha256) {
    throw new Error('Download verification failed');
  }
  
  // Stop backend
  await stopBackend();
  
  // Extract to app-code folder (overwrites)
  const appCodePath = path.join(app.getPath('userData'), 'resources', 'app-code');
  await extractZip(zipPath, appCodePath);
  
  // Update version.json
  await fs.writeFile(
    path.join(appCodePath, '..', 'version.json'),
    JSON.stringify({ app_version: latest.app_version })
  );
  
  // Restart backend
  await startBackend();
  
  // Reload frontend
  mainWindow.reload();
  
  return { action: 'updated', version: latest.app_version };
});
```

## Update Options (Choose Your Complexity)

### Option A: Manual Download (Simplest)

- App shows "Update available" notification with link
- User downloads new installer manually
- Zero server infrastructure needed

**Pros**: No backend required, works with file share

**Cons**: High friction, users may ignore

### Option B: In-Place App Code Update (Recommended)

- Shell checks update endpoint on startup
- Downloads and extracts app-code.zip
- Restarts backend, reloads frontend
- Shell itself only updates for breaking changes

**Pros**: Small downloads (just changed code), seamless UX

**Cons**: Need to host zip files somewhere

### Option C: Full electron-updater (Most Polished)

- Uses electron-updater with GitHub Releases or S3
- Downloads full installer in background
- "Restart to update" button
- Differential updates possible (NSIS)

**Pros**: Industry standard, handles edge cases

**Cons**: Large downloads, more complex setup

## Recommended: Option B Implementation

### Release Process (for maintainers)

```bash
# 1. Build frontend
cd frontend && npm run build

# 2. Create app-code.zip
zip -r app-code-1.2.4.zip backend/ frontend/dist/ -x "backend/venv/*" -x "backend/__pycache__/*"

# 3. Compute hash
sha256sum app-code-1.2.4.zip

# 4. Update latest.json on update server
# 5. Upload zip to update server
```

### Update Server Options

1. **GitHub Releases** - Free, works well for public/internal repos
2. **Internal file share** - `\\server\updates\seriem-agent\`
3. **S3/Azure Blob** - Scalable, pay-per-use
4. **Simple HTTP server** - Nginx serving static files

### Handling Python Dependency Changes

If `requirements.txt` changes:

```javascript
// After extracting update
const newReqs = await fs.readFile(path.join(appCodePath, 'backend', 'requirements.txt'));
const oldReqs = await fs.readFile(path.join(appCodePath, 'backend', 'venv', 'requirements.txt'));

if (newReqs !== oldReqs) {
  // Re-run pip install
  await execAsync(`${venvPython} -m pip install -r requirements.txt`, {
    cwd: path.join(appCodePath, 'backend')
  });
}
```

## Files to Create/Modify

| File | Change |

|------|--------|

| `desktop/main.js` | Add version check + update download logic |

| `desktop/preload.js` | Expose update IPC methods |

| `backend/app/api/routes.py` | Add `/api/version` endpoint |

| `frontend/src/app/components/update-banner/` | NEW: Update notification UI |

| `scripts/release.sh` | NEW: Script to build app-code.zip and update latest.json |

## Migration Path

1. **v1.0**: Ship without auto-update (manual download only)
2. **v1.1**: Add version check + notification (shows "Update available" with link)
3. **v1.2**: Add in-place app-code updater (seamless updates)
4. **Future**: Consider electron-updater for shell updates if needed

## Risks and Mitigations

| Risk | Mitigation |

|------|------------|

| Update fails mid-extraction | Keep backup of previous app-code, rollback on error |

| User offline | Cache version check, skip silently |

| Corrupted download | SHA256 verification before extraction |

| Breaking shell changes | min_shell_version field forces full reinstall when needed |

| pip install fails | Show error, offer "Try Again" or "Skip Update" |

## Non-Goals (for MVP)

- Delta updates (only download changed files)
- Automatic silent updates (always prompt user)
- Rollback UI (manual reinstall for now)




````