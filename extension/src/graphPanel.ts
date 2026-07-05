import * as vscode from "vscode";

export class ChaosGraphPanel {
  public static currentPanel: ChaosGraphPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private readonly extensionUri: vscode.Uri;

  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, workspacePath: string) {
    this.panel = panel;
    this.extensionUri = extensionUri;

    this.panel.webview.html = this.getHtml(this.panel.webview, workspacePath);
  }

  public static createOrShow(extensionUri: vscode.Uri, workspacePath: string) {
    const column = vscode.ViewColumn.Beside;

    if (ChaosGraphPanel.currentPanel) {
      ChaosGraphPanel.currentPanel.panel.reveal(column);
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      "chaosGraph",
      "Chaos Dependency Graph",
      column,
      {
        enableScripts: true
      }
    );

    ChaosGraphPanel.currentPanel = new ChaosGraphPanel(panel, extensionUri, workspacePath);

    panel.onDidDispose(() => {
      ChaosGraphPanel.currentPanel = undefined;
    });
  }

  private getHtml(webview: vscode.Webview, workspacePath: string): string {
    const scriptUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "media", "graph.js")
    );
    const styleUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "media", "graph.css")
    );

    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>Chaos Graph</title>
  <link rel="stylesheet" href="${styleUri}">
  <script src="https://unpkg.com/cytoscape@3.28.0/dist/cytoscape.min.js"></script>
</head>
<body>
  <div id="toolbar">
    <button id="scanBtn">Scan</button>
    <button id="simulateBtn">Simulate Random Failure</button>
  </div>
  <div id="cy"></div>
  <script>
    const WORKSPACE_PATH = ${JSON.stringify(workspacePath)};
  </script>
  <script src="${scriptUri}"></script>
</body>
</html>`;
  }
}
