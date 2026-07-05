# Chaos Monkey for VS Code

Chaos Monkey is a VS Code extension that scans Python projects for dependency issues, visualizes the dependency graph, simulates failures, analyzes risk, and generates a local AI-backed report.

## Features

- Scan a Python workspace for service modules and dependency relationships
- Build a Cytoscape dependency graph in a VS Code webview
- Simulate failure effects across the dependency graph
- Analyze structural issues such as cycles, hotspots, orphans, and leaf nodes
- Generate a written report from scan, analysis, and vulnerability findings
- Optional local AI report generation via `llama-cpp-python` and a local model file

## Architecture

This repository contains two main parts:

1. **VS Code extension frontend**
   - `src/extension.ts` starts the backend and registers commands
   - `src/graphPanel.ts` builds the webview panel and communicates with the backend
   - `src/sidebar.ts` provides a sidebar tree view for discovered services
   - `media/graph.js` renders Cytoscape graphs and handles panel controls

2. **Python backend**
   - `backend/app/main.py` starts a FastAPI server
   - `backend/app/routers/scan.py`, `analyze.py`, `simulate.py`, `recommend.py` expose REST endpoints
   - `backend/app/services/` contains scanning, analysis, simulation, and graph-building logic
   - `backend/config.env` stores backend configuration and local model path

## Prerequisites

- VS Code
- Python 3.11 or newer available on the system PATH
- `pip` installed
- Node.js / npm for building the extension
- Optional: a local llama-cpp-compatible model file for AI report generation

## Installation

1. Open the `extension` folder in VS Code.
2. Install Node dependencies if you want to build the extension locally:

```bash
npm install
```

3. Compile the extension and copy media files:

```bash
npm run compile
```

4. Install backend Python dependencies:

```bash
cd backend
pip install -r requirements.txt
```

5. Set up the local Llama model (one-time):

```bash
python setup_llama.py
```

This downloads and caches the default model in `backend/models/llama/`.

6. Optionally configure a specific local model path in `backend/config.env`:

```text
LLAMA_CPP_MODEL_PATH=
```

Set this only if you want the backend to use a pre-downloaded model file.

## Using the Extension

### Commands

- `Chaos: Scan Project` — scan the open workspace for Python dependency data
- `Chaos: Open Graph` — open the graph panel and interact with the scan results

### Webview Controls

- `Scan` — runs a scan from the panel using the current workspace path
- `Simulate` — simulates failure effects on the discovered graph
- `Analyze` — sends dependencies and services to the backend for structural analysis
- `Write Report` — requests the backend to generate a vulnerability report

## Local AI Report Support

The extension supports offline report generation using a local `llama-cpp` model via `llama-cpp-python`.

### How it works

- Backend dependencies are installed from `backend/requirements.txt`
- `setup_llama.py` downloads and caches a local model in `backend/models/llama/`
- `backend/app/services/analyzer.py` automatically loads the local model path
- The `/recommend` endpoint uses the local model to generate AI report text
- If no model is available, the backend falls back to a standard generated report

### Model file placement and configuration

By default, `setup_llama.py` downloads the model to:

```text
backend/models/llama/
```

If you prefer to use a pre-downloaded model, set the path in `backend/config.env`:

```text
LLAMA_CPP_MODEL_PATH=C:/Users/PRERAK PATEL/Desktop/ChaosMonkey/extension/backend/models/llama/7B/your-model.gguf
```

The model file must be compatible with `llama-cpp-python` (GGUF format). This is a local-only model, not a cloud service.

## Backend Endpoints

- `POST /scan/` — scans a Python project path and returns services, dependencies, vulnerabilities, and graph data
- `POST /analyze/` — analyzes dependency relationships and returns structural findings
- `POST /simulate/random` — simulates failure effects over discovered services and dependencies
- `POST /recommend/` — generates a written report and optionally writes `chaos-report.txt` to the project root

## Configuration

### `backend/config.env`

The project currently stores backend config values here. Example:

```text
MYSQL_USER=root
MYSQL_PASSWORD=passwd
MYSQL_HOST=host.docker.internal
MYSQL_PORT=3306
MYSQL_DB=mydb
LLAMA_CPP_MODEL_PATH=
```

Set `LLAMA_CPP_MODEL_PATH` only if you have a compatible local model and want to override the default cached download.

To change the backend port, set `BACKEND_PORT` in `backend/config.env` or in your environment. Example:

```text
BACKEND_PORT=8001
```

If not set, the backend will default to port `8000`.

## Build and Package

- `npm run compile` — compile TypeScript and copy media assets to `out/`
- `npm run watch` — run `tsc` in watch mode for development
- `npm run package` — package the extension with `vsce`
- `npm run publish` — publish using `vsce`

## Notes

- The extension activation installs backend dependencies automatically, but Python must still be present.
- If `LLAMA_CPP_MODEL_PATH` is not set or the model fails to load, the report feature still returns a fallback generated summary.
- The backend is based on FastAPI and runs locally at `http://127.0.0.1:8000`.

## Troubleshooting

- If the scan fails, verify the backend is running and Python is installed.
- If AI report generation fails, check `backend/config.env` and ensure `llama-cpp-python` can load the specified model.
- Use the VS Code debug console to inspect backend logs printed from `src/extension.ts`.

## License

MIT