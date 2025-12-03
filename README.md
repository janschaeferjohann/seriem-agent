# Seriem Agent

A prototype coding agent application built with LangChain and Anthropic models. Features an Angular frontend with file explorer and chat interface, backed by a FastAPI Python backend.

## Architecture

```
seriem-agent/
├── backend/          # Python FastAPI + LangChain
├── frontend/         # Angular 20 app
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
# Edit .env with your ANTHROPIC_API_KEY

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

Open http://localhost:4200

## Features

- **File Explorer**: Browse and view files in the agent's workspace
- **Chat Interface**: Interact with the AI agent via chat
- **Filesystem Tools**: Agent can list, read, write, and edit files
- **Streaming Responses**: Real-time message streaming via WebSocket

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message to agent |
| `/api/files` | GET | List files in storage |
| `/api/files/{path}` | GET | Read file content |
| `/ws/chat` | WebSocket | Streaming chat |

## Tech Stack

- **Backend**: Python, FastAPI, LangChain, Anthropic Claude
- **Frontend**: Angular 20, Angular Material
- **Storage**: Local filesystem

## Future Plans

- Electron desktop app packaging
- Specialized subagents (code generation, review, testing)
- Enhanced file operations

## License

MIT

