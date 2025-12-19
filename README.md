# Seriem Agent

A prototype coding agent application built with LangChain and Anthropic models. Features an Angular frontend with file explorer and chat interface, backed by a FastAPI Python backend.

## Architecture

```
seriem-agent/
├── backend/          # Python FastAPI + LangChain
├── frontend/         # Angular 20 app
├── desktop/          # Electron shell for desktop app
├── storage/          # Agent workspace (local files)
├── README.md
└── agents.md         # Agent architecture docs
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- npm 10+
- Anthropic API key

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
cp env.example .env
# Edit .env with your ANTHROPIC_API_KEY (never commit .env)

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

Open http://localhost:4200

### Desktop App (Electron)

#### Building the .exe Installer

1. **Build the Angular frontend first:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Install desktop dependencies:**
   ```bash
   cd desktop
   npm install
   ```

3. **Build the Electron app:**
   ```bash
   cd desktop
   npm run build:win    # Windows
   npm run build:mac    # macOS
   npm run build:linux  # Linux
   ```

The installer will be created in `desktop/dist/`:
- Windows: `Seriem Agent Setup x.x.x.exe`
- Unpacked version: `desktop/dist/win-unpacked/` (can run directly without installing)

#### Development Testing (Without Full Build)

For faster iteration during development:

```bash
# Terminal 1: Run the backend
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Run the frontend dev server
cd frontend
npm start

# Terminal 3: Run Electron in dev mode
cd desktop
npm run start:dev
```

In dev mode, Electron will:
- Load frontend from `http://localhost:4200` (hot reload)
- Skip spawning the backend (assumes you're running it separately)
- Open DevTools automatically

**Note:** The packaged Electron app requires users to have Python 3.11+ installed on their system.

## Features

- **File Explorer**: Browse and view files in the agent's workspace
- **Chat Interface**: Interact with the AI agent via chat
- **Filesystem Tools**: Agent can list, read, write, and edit files
- **Streaming Responses**: Real-time message streaming via WebSocket
- **Proposal Layer**: Agent file changes require user approval before being applied
- **Diff Review UI**: Review proposed changes with side-by-side diff view
- **Workspace Selection**: Choose any folder as your workspace
- **Desktop App**: Electron-based desktop application with native folder picker

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message to agent |
| `/api/files` | GET | List files in workspace |
| `/api/files/{path}` | GET | Read file content |
| `/api/workspace/select` | POST | Set active workspace folder |
| `/api/workspace/current` | GET | Get current workspace info |
| `/api/proposals/pending` | GET | List pending change proposals |
| `/api/proposals/{id}` | GET | Get proposal details with diff |
| `/api/proposals/{id}/approve` | POST | Approve and apply changes |
| `/api/proposals/{id}/reject` | POST | Reject and discard changes |
| `/ws/chat` | WebSocket | Streaming chat |

## Tech Stack

- **Backend**: Python, FastAPI, LangChain, Anthropic Claude
- **Frontend**: Angular 20, Angular Material, Monaco Editor
- **Desktop**: Electron with electron-builder
- **Storage**: Local filesystem

## Future Plans

- Specialized subagents (code generation, review, testing)
- Git integration for commits on approval
- Telemetry and usage analytics
- Auto-update mechanism

## License

MIT

