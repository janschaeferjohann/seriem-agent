/**
 * Seriem Agent - Electron Main Process
 * 
 * Responsibilities:
 * - Launch Python FastAPI backend as child process
 * - Host Angular frontend in BrowserWindow
 * - Provide native dialogs (folder picker)
 * - Manage application lifecycle
 */

const { app, BrowserWindow, dialog, ipcMain, shell } = require('electron');
const { spawn, execSync } = require('child_process');
const path = require('path');
const net = require('net');
const Store = require('electron-store');

// Encrypted store for sensitive settings
const store = new Store({
  encryptionKey: 'seriem-agent-v1-key',
  defaults: {
    anthropicApiKey: '',
    gitCredentials: null,
    telemetryEnabled: true,
  }
});

// Global references
let mainWindow = null;
let backendProcess = null;
let backendPort = 8000;

// Check if running in development mode
const isDev = process.env.NODE_ENV === 'development';

// ============================================================================
// Python Detection
// ============================================================================

/**
 * Find a suitable Python executable (3.11+)
 * @returns {string|null} Path to Python executable or null if not found
 */
function findPython() {
  const candidates = [
    'python3',
    'python',
    // Windows common locations
    'C:\\Python311\\python.exe',
    'C:\\Python312\\python.exe',
    'C:\\Python313\\python.exe',
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python311', 'python.exe'),
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python312', 'python.exe'),
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python313', 'python.exe'),
    // macOS/Linux
    '/usr/bin/python3',
    '/usr/local/bin/python3',
  ];

  for (const candidate of candidates) {
    try {
      const result = execSync(`"${candidate}" --version`, { 
        stdio: 'pipe',
        timeout: 5000,
        windowsHide: true
      });
      const versionMatch = result.toString().match(/Python (\d+)\.(\d+)/);
      if (versionMatch) {
        const major = parseInt(versionMatch[1], 10);
        const minor = parseInt(versionMatch[2], 10);
        if (major >= 3 && minor >= 11) {
          console.log(`Found Python ${major}.${minor} at: ${candidate}`);
          return candidate;
        }
      }
    } catch (e) {
      // Continue to next candidate
    }
  }
  return null;
}

/**
 * Show error dialog when Python is not found
 */
function showPythonNotFoundError() {
  dialog.showErrorBox(
    'Python Not Found',
    'Seriem Agent requires Python 3.11 or later.\n\n' +
    'Please install Python from:\nhttps://www.python.org/downloads/\n\n' +
    'Make sure to check "Add Python to PATH" during installation.\n\n' +
    'After installing Python, restart Seriem Agent.'
  );
}

// ============================================================================
// Port Management
// ============================================================================

/**
 * Find an available port starting from the given port
 * @param {number} startPort - Port to start searching from
 * @param {number} maxAttempts - Maximum number of ports to try
 * @returns {Promise<number>} Available port number
 */
async function findAvailablePort(startPort = 8000, maxAttempts = 10) {
  for (let port = startPort; port < startPort + maxAttempts; port++) {
    const available = await isPortAvailable(port);
    if (available) {
      return port;
    }
  }
  throw new Error(`No available ports found between ${startPort} and ${startPort + maxAttempts - 1}`);
}

/**
 * Check if a port is available
 * @param {number} port - Port to check
 * @returns {Promise<boolean>} True if port is available
 */
function isPortAvailable(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', () => resolve(false));
    server.once('listening', () => {
      server.close();
      resolve(true);
    });
    server.listen(port, '127.0.0.1');
  });
}

// ============================================================================
// Backend Management
// ============================================================================

/**
 * Get the path to the backend directory
 * @returns {string} Path to backend directory
 */
function getBackendPath() {
  if (isDev) {
    return path.join(__dirname, '..', 'backend');
  }
  return path.join(process.resourcesPath, 'backend');
}

/**
 * Get the path to the frontend directory
 * @returns {string} Path to frontend directory
 */
function getFrontendPath() {
  if (isDev) {
    return path.join(__dirname, '..', 'frontend', 'dist', 'frontend', 'browser');
  }
  return path.join(process.resourcesPath, 'frontend');
}

/**
 * Start the Python backend server
 * @param {string} pythonPath - Path to Python executable
 * @param {number} port - Port to run the server on
 * @returns {ChildProcess} The spawned process
 */
function startBackend(pythonPath, port) {
  const backendPath = getBackendPath();
  const apiKey = store.get('anthropicApiKey', '');
  
  console.log(`Starting backend at ${backendPath} on port ${port}`);
  
  const env = {
    ...process.env,
    ANTHROPIC_API_KEY: apiKey,
    PYTHONUNBUFFERED: '1',
  };

  // Use venv Python if available
  let actualPython = pythonPath;
  const venvPython = process.platform === 'win32'
    ? path.join(backendPath, 'venv', 'Scripts', 'python.exe')
    : path.join(backendPath, 'venv', 'bin', 'python');
  
  try {
    require('fs').accessSync(venvPython);
    actualPython = venvPython;
    console.log('Using venv Python:', actualPython);
  } catch (e) {
    console.log('Venv not found, using system Python:', actualPython);
  }

  const proc = spawn(
    actualPython,
    ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(port)],
    {
      cwd: backendPath,
      env,
      windowsHide: true,
    }
  );

  proc.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  proc.stderr.on('data', (data) => {
    console.error(`[Backend] ${data.toString().trim()}`);
  });

  proc.on('error', (err) => {
    console.error('Failed to start backend:', err);
  });

  proc.on('exit', (code) => {
    console.log(`Backend exited with code ${code}`);
    backendProcess = null;
  });

  return proc;
}

/**
 * Wait for the backend to be ready
 * @param {number} port - Port the backend is running on
 * @param {number} timeout - Maximum time to wait in ms
 * @returns {Promise<boolean>} True if backend is ready
 */
async function waitForBackend(port, timeout = 30000) {
  const startTime = Date.now();
  const url = `http://127.0.0.1:${port}/health`;
  
  while (Date.now() - startTime < timeout) {
    try {
      const http = require('http');
      const ready = await new Promise((resolve) => {
        const req = http.get(url, (res) => {
          resolve(res.statusCode === 200);
        });
        req.on('error', () => resolve(false));
        req.setTimeout(1000, () => {
          req.destroy();
          resolve(false);
        });
      });
      
      if (ready) {
        console.log('Backend is ready!');
        return true;
      }
    } catch (e) {
      // Continue waiting
    }
    
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  return false;
}

/**
 * Stop the backend server
 */
function stopBackend() {
  if (backendProcess) {
    console.log('Stopping backend...');
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(backendProcess.pid), '/f', '/t'], { windowsHide: true });
    } else {
      backendProcess.kill('SIGTERM');
    }
    backendProcess = null;
  }
}

// ============================================================================
// Window Management
// ============================================================================

/**
 * Create the main application window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    title: 'Seriem Agent',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    show: false, // Show when ready
  });

  // Load frontend
  if (isDev) {
    // In dev mode, load from Angular dev server
    mainWindow.loadURL('http://localhost:4200');
    mainWindow.webContents.openDevTools();
  } else {
    // In production, load from built files
    const frontendPath = getFrontendPath();
    mainWindow.loadFile(path.join(frontendPath, 'index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ============================================================================
// IPC Handlers
// ============================================================================

function setupIpcHandlers() {
  // Dialog: Select folder
  ipcMain.handle('dialog:selectFolder', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory'],
      title: 'Select Workspace Folder',
    });
    return result.canceled ? null : result.filePaths[0];
  });

  // Config: Get/Set API Key
  ipcMain.handle('config:getApiKey', () => {
    return store.get('anthropicApiKey', '');
  });

  ipcMain.handle('config:setApiKey', (_, key) => {
    store.set('anthropicApiKey', key);
    // Update backend environment if running
    if (backendProcess) {
      // Backend needs restart to pick up new key
      console.log('API key updated. Backend restart may be required.');
    }
    return true;
  });

  // Config: Get backend port
  ipcMain.handle('config:getBackendPort', () => {
    return backendPort;
  });

  // Settings: Get global settings
  ipcMain.handle('settings:getGlobal', () => {
    return {
      anthropicApiKey: store.get('anthropicApiKey', ''),
      gitCredentials: store.get('gitCredentials', null),
      telemetryEnabled: store.get('telemetryEnabled', true),
    };
  });

  // Settings: Set global settings
  ipcMain.handle('settings:setGlobal', (_, settings) => {
    if (settings.anthropicApiKey !== undefined) {
      store.set('anthropicApiKey', settings.anthropicApiKey);
    }
    if (settings.gitCredentials !== undefined) {
      store.set('gitCredentials', settings.gitCredentials);
    }
    if (settings.telemetryEnabled !== undefined) {
      store.set('telemetryEnabled', settings.telemetryEnabled);
    }
    return true;
  });

  // Settings: Set API key (convenience)
  ipcMain.handle('settings:setApiKey', (_, key) => {
    store.set('anthropicApiKey', key);
    return true;
  });

  // Settings: Set Git credentials
  ipcMain.handle('settings:setGitCredentials', (_, creds) => {
    store.set('gitCredentials', creds);
    return true;
  });

  // Shell: Open external link
  ipcMain.handle('shell:openExternal', (_, url) => {
    shell.openExternal(url);
  });

  // App: Check if first run (no API key)
  ipcMain.handle('app:isFirstRun', () => {
    const apiKey = store.get('anthropicApiKey', '');
    return !apiKey || apiKey.trim() === '';
  });

  // App: Restart backend
  ipcMain.handle('app:restartBackend', async () => {
    stopBackend();
    const pythonPath = findPython();
    if (pythonPath) {
      backendProcess = startBackend(pythonPath, backendPort);
      return waitForBackend(backendPort);
    }
    return false;
  });
}

// ============================================================================
// Application Lifecycle
// ============================================================================

app.whenReady().then(async () => {
  console.log('Seriem Agent starting...');
  
  // Find Python
  const pythonPath = findPython();
  if (!pythonPath) {
    showPythonNotFoundError();
    app.quit();
    return;
  }
  
  // Find available port
  try {
    backendPort = await findAvailablePort(8000);
    console.log(`Using port ${backendPort}`);
  } catch (e) {
    dialog.showErrorBox(
      'Port Error',
      'Could not find an available port for the backend server.\n\n' +
      'Please close any applications using ports 8000-8009 and try again.'
    );
    app.quit();
    return;
  }
  
  // Setup IPC handlers
  setupIpcHandlers();
  
  // Start backend (unless in dev mode where it might be running separately)
  if (!isDev) {
    backendProcess = startBackend(pythonPath, backendPort);
    const ready = await waitForBackend(backendPort);
    if (!ready) {
      dialog.showErrorBox(
        'Backend Error',
        'Failed to start the backend server.\n\n' +
        'Please check that all Python dependencies are installed.'
      );
      app.quit();
      return;
    }
  }
  
  // Create main window
  createWindow();
  
  // macOS: Re-create window when clicking dock icon
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed (except on macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Clean up before quitting
app.on('before-quit', () => {
  stopBackend();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  stopBackend();
});

