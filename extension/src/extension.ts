import * as vscode from "vscode";
import { ChaosGraphPanel } from "./graphPanel";
import { ChaosSidebarProvider } from "./sidebar";

export function activate(context: vscode.ExtensionContext) {
  const sidebarProvider = new ChaosSidebarProvider();
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("chaosSidebar", sidebarProvider)
  );

  const scanCommand = vscode.commands.registerCommand(
    "chaos.scanProject",
    async () => {
      const folder = vscode.workspace.workspaceFolders?.[0];
      if (!folder) {
        vscode.window.showErrorMessage("Open a workspace folder first.");
        return;
      }

      const path = folder.uri.fsPath;
      try {
        const res = await fetch("http://localhost:8000/scan/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path })
        });
        const data = await res.json();
        sidebarProvider.updateServices(data.services);
        vscode.window.showInformationMessage(
          `Chaos: scanned ${data.services.length} modules.`
        );
      } catch (err) {
        vscode.window.showErrorMessage("Chaos scan failed. Is backend running?");
      }
    }
  );

  const openGraphCommand = vscode.commands.registerCommand(
    "chaos.openGraph",
    async () => {
      const folder = vscode.workspace.workspaceFolders?.[0];
      if (!folder) {
        vscode.window.showErrorMessage("Open a workspace folder first.");
        return;
      }
      ChaosGraphPanel.createOrShow(context.extensionUri, folder.uri.fsPath);
    }
  );

  context.subscriptions.push(scanCommand, openGraphCommand);
}

export function deactivate() {}
