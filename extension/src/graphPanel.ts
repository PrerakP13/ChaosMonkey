import * as vscode from "vscode";
import * as path from "path";

let backendBaseUrl = "http://127.0.0.1:8000";

// ---------------------------------------------------------
// ChaosGraphPanel
// ---------------------------------------------------------
export class ChaosGraphPanel {
  public static currentPanel: ChaosGraphPanel | undefined;

  private readonly _panel: vscode.WebviewPanel;
  private readonly _extensionUri: vscode.Uri;
  private readonly _projectPath: string;
  private readonly _backendUrl: string;
  private readonly _onServicesUpdate?: (services: string[]) => void;

  public sendMessage(message: any) {
    this._panel.webview.postMessage(message);
  }

  public static createOrShow(
    extensionUri: vscode.Uri,
    projectPath: string,
    backendUrl: string,
    onServicesUpdate?: (services: string[]) => void
  ) {
    const column = vscode.ViewColumn.Beside;

    if (ChaosGraphPanel.currentPanel) {
      ChaosGraphPanel.currentPanel._panel.reveal(column);
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      "chaosGraph",
      "Chaos Dependency Graph",
      column,
      {
        enableScripts: true,
        retainContextWhenHidden: true
      }
    );

    ChaosGraphPanel.currentPanel = new ChaosGraphPanel(
      panel,
      extensionUri,
      projectPath,
      backendUrl,
      onServicesUpdate
    );
  }

  private constructor(
    panel: vscode.WebviewPanel,
    extensionUri: vscode.Uri,
    projectPath: string,
    backendUrl: string,
    onServicesUpdate?: (services: string[]) => void
  ) {
    this._panel = panel;
    this._extensionUri = extensionUri;
    this._projectPath = projectPath;
    this._backendUrl = backendUrl;
    backendBaseUrl = backendUrl;
    this._onServicesUpdate = onServicesUpdate;

    this._panel.webview.html = this._getHtmlForWebview(this._panel.webview);

    // ---------------------------------------------------------
    // MESSAGE HANDLER (scan + simulate + analyze + report)
    // ---------------------------------------------------------
    this._panel.webview.onDidReceiveMessage(async (message) => {
      console.log("[ChaosGraphPanel] received message from webview:", message?.type);


      // -------------------------
      // SCAN (NEW)
      // -------------------------
      if (message.type === "scan") {
        const result = await callBackend("/scan", message.payload);
        const services = result.results?.services || result.services || [];

        this._panel.webview.postMessage({
          type: "scanResult",
          payload: {
            graph: result.graph,   // full metadata graph
            results: result        // full Level 1–5 results
          }
        });

        if (this._onServicesUpdate && Array.isArray(services)) {
          this._onServicesUpdate(services);
        }
      }

      // -------------------------
      // SIMULATE
      // -------------------------
      if (message.type === "simulate") {
        try {
          console.log("[ChaosGraphPanel] invoking backend simulate with payload:", message.payload);
          const result = await callBackend("/simulate/random", message.payload);

          this._panel.webview.postMessage({
            type: "simulateResult",
            payload: result
          });

          if (this._onServicesUpdate && Array.isArray(message.payload.services)) {
            this._onServicesUpdate(message.payload.services);
          }
        } catch (err) {
          console.error("[ChaosGraphPanel] simulate failed:", err);
          this._panel.webview.postMessage({
            type: "simulateResult",
            payload: { error: String(err), failed: [], detailed: [], effects: [], chains: [], resilience: 0 }
          });
        }
      }

      // -------------------------
      // ANALYZE
      // -------------------------
      if (message.type === "analyze") {
        const result = await callBackend("/analyze", message.payload);

        this._panel.webview.postMessage({
          type: "analysisResult",
          payload: result
        });

        if (this._onServicesUpdate && Array.isArray(message.payload.services)) {
          this._onServicesUpdate(message.payload.services);
        }
      }

      // -------------------------
      // REPORT
      // -------------------------
      if (message.type === "generateReport") {
        const result = await callBackend("/recommend", message.payload);

        this._panel.webview.postMessage({
          type: "reportResult",
          payload: result
        });
      }
    });

    this._panel.onDidDispose(() => {
      ChaosGraphPanel.currentPanel = undefined;
    });

    // HTML Loader
    // ---------------------------------------------------------
  }

  private _getHtmlForWebview(webview: vscode.Webview): string {
    const graphJsUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this._extensionUri, "out", "media", "graph.js")
    );

    const styleUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this._extensionUri, "out", "media", "graph.css")
    );

    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <link rel="stylesheet" href="${styleUri}">
        <style>
          html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
            background: #1e1e1e;
            font-family: sans-serif;
          }
          #controls {
            position: absolute;
            top: 10px;
            left: 10px;
            z-index: 999;
          }
          button {
            margin-right: 8px;
            padding: 6px 12px;
            background: #007acc;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
          }
          #legend {
            position: absolute;
            top: 60px;
            left: 10px;
            width: 280px;
            padding: 25px;
            background: rgba(30, 30, 30, 0.98);
            border: 1px solid #444;
            border-radius: 8px;
            color: #ddd;
            font-size: 11px;
            overflow: hidden;
            z-index: 998;
          }
          #legend.collapsed {
            max-height: 40px;
          }
          #legend.collapsed #legendBody {
            display: none;
          }
          #legend-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
          }
          #legend-header span {
            font-size: 12px;
            font-weight: 700;
            color: #fff;
          }
          #legendToggleBtn {
            border: 1px solid #555;
            border-radius: 4px;
            background: transparent;
            color: #ddd;
            padding: 3px 8px;
            cursor: pointer;
            font-size: 11px;
          }
          #legend .legend-title {
            margin-top: 10px;
            margin-bottom: 6px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            color: #aaa;
          }
          #container {
            display: flex;
            height: 100%;
          }
          #legend .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 6px;
          }
          #legend .legend-item:last-child {
            margin-bottom: 0;
          }
          #legend .legend-swatch {
            width: 14px;
            height: 14px;
            border-radius: 3px;
            margin-right: 8px;
            flex-shrink: 0;
            border: 1px solid #555;
          }
          #container {
            display: flex;
            height: 100%;
          }
          #cy {
            flex: 3;
            background: #1e1e1e;
          }
          #analysis-panel {
            flex: 1;
            padding: 10px;
            overflow-y: auto;
            background: #252526;
            color: #ddd;
            border-left: 1px solid #333;
            font-size: 12px;
          }
          #report-status {
            position: fixed;
            left: 10px;
            bottom: 10px;
            z-index: 1000;
            display: none;
            align-items: center;
            gap: 6px;
            padding: 8px 10px;
            border-radius: 6px;
            background: rgba(37, 37, 38, 0.96);
            color: #ddd;
            border: 1px solid #444;
            font-size: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
          }
          #report-status.loading {
            display: flex;
          }
          #report-status .spinner {
            width: 12px;
            height: 12px;
            border: 2px solid #8ab4f8;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            flex-shrink: 0;
          }
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        </style>
      </head>

      <body>

        <div id="controls">
          <button id="scanBtn">Scan</button>
          <button id="simulateBtn">Simulate</button>
          <button id="analyzeBtn">Analyze</button>
          <button id="recommendBtn">Write Report</button>
        </div>

        <div id="legend" class="collapsed">
          <div id="legend-header">
            <span>Legend</span>
            <button id="legendToggleBtn" title="Show legend">Show</button>
          </div>
          <div id="legendBody">
            <div class="legend-title">Node severity</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#1976d2"></span>Info</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#388e3c"></span>Low</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#fbc02d"></span>Medium</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#f57c00"></span>High</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#d32f2f"></span>Critical</div>
            <div class="legend-title">Failure status</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#1e1e1e; border: 2px solid #388e3c"></span>OK border</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#1e1e1e; border: 2px solid #f57c00"></span>Degraded border</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#1e1e1e; border: 2px solid #d32f2f"></span>Failed border</div>
            <div class="legend-title">Chain edges</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#7b1fa2"></span>Taint chain</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#d32f2f"></span>Chaos chain</div>
          </div>
        </div>

        <div id="container">
          <div id="cy"></div>
          <div id="analysis-panel"></div>
        </div>

        <div id="report-status" role="status" aria-live="polite" style="display:none"></div>

        <script>
          window.projectPath = ${JSON.stringify(this._projectPath)};
        </script>
        <script>
          const legend = document.getElementById("legend");
          const toggleBtn = document.getElementById("legendToggleBtn");
          if (legend && toggleBtn) {
            toggleBtn.addEventListener("click", () => {
              const collapsed = legend.classList.toggle("collapsed");
              toggleBtn.textContent = collapsed ? "Show" : "Hide";
              toggleBtn.title = collapsed ? "Show legend" : "Hide legend";
            });
          }
        </script>
        <script src="https://unpkg.com/cytoscape/dist/cytoscape.min.js"></script>
        <script src="${graphJsUri}"></script>

      </body>
      </html>
    `;
  }
}

// ---------------------------------------------------------
// Backend Caller
// ---------------------------------------------------------
async function callBackend(endpoint: string, body: any): Promise<any> {
  const fullUrl = `${backendBaseUrl}${endpoint}`;
  console.log(`[callBackend] POST ${fullUrl}`);
  console.log(`[callBackend] Body:`, body);
  
  try {
    const res = await fetch(fullUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });

    console.log(`[callBackend] Response status: ${res.status} ${res.statusText}`);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error(`[callBackend] HTTP ${res.status}: ${errorText}`);
      throw new Error(`HTTP ${res.status}: ${errorText}`);
    }
    
    const data = await res.json();
    console.log(`[callBackend] Response data:`, data);
    return data;
  } catch (err) {
    console.error(`[callBackend] Error calling ${fullUrl}:`, err);
    throw err;
  }
}
