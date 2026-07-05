import * as vscode from "vscode";
import * as cp from "child_process";
import * as fs from "fs";
import * as path from "path";
import { ChaosGraphPanel } from "./graphPanel";
import { ChaosSidebarProvider } from "./sidebar";

function getBackendPort(backendDir: string): string {
  const envPath = path.join(backendDir, "config.env");
  try {
    const config = fs.readFileSync(envPath, "utf8");
    const match = config.match(/^\s*BACKEND_PORT\s*=\s*(\d+)\s*$/m);
    return match ? match[1] : "8000";
  } catch {
    return "8000";
  }
}

async function ensureBackendDependencies(backendDir: string): Promise<void> {
  return new Promise((resolve) => {
    const installer = cp.spawn("python", ["-m", "pip", "install", "-r", "requirements.txt"], {
      cwd: backendDir
    });

    installer.stdout?.on("data", (data) => {
      console.log("[Backend pip]", data.toString());
    });

    installer.stderr?.on("data", (data) => {
      console.error("[Backend pip]", data.toString());
    });

    installer.on("error", (err) => {
      console.error("[Backend pip] install failed:", err);
      resolve();
    });

    installer.on("close", (code) => {
      if (code !== 0) {
        console.error(`Backend pip install exited with code ${code}`);
      }
      resolve();
    });
  });
}

interface ScanResponse {
  services: string[];
  dependencies: any[];
  graph: any;
}

let backendProcess: cp.ChildProcess | null = null;

export async function activate(context: vscode.ExtensionContext) {
  // -------------------------------
  // 1. INSTALL BACKEND DEPENDENCIES
  // -------------------------------
  const backendDir = path.join(context.extensionPath, "backend");
  const backendPath = path.join(backendDir, "app", "main.py");
  const backendPort = getBackendPort(backendDir);
  const backendBaseUrl = `http://127.0.0.1:${backendPort}`;

  await vscode.window.withProgress({
    location: vscode.ProgressLocation.Notification,
    title: "Installing Chaos backend dependencies...",
    cancellable: false,
  }, async () => {
    await ensureBackendDependencies(backendDir);
  });

  // -------------------------------
  // 2. START BACKEND AUTOMATICALLY
  // -------------------------------
  console.log("Starting backend at:", backendPath);
  console.log("Backend CWD:", backendDir);

  // IMPORTANT: no shell:true, no quoting issues
  backendProcess = cp.spawn("python", [backendPath], {
    cwd: backendDir,
    env: {
      ...process.env,
      BACKEND_PORT: backendPort
    }
  });

  // Logging
  backendProcess.stdout?.on("data", (data) => {
    console.log("[Backend STDOUT]", data.toString());
  });

backendProcess.stderr?.on("data", (data) => {
  console.error("[Backend STDERR]", data.toString());
});

backendProcess.on("error", (err) => {
  console.error("[Backend ERROR] Failed to start:", err);
});

backendProcess.on("exit", (code) => {
  console.error("[Backend EXIT] Code:", code);
});

  // -------------------------------
  // 2. SIDEBAR PROVIDER
  // -------------------------------
  const sidebarProvider = new ChaosSidebarProvider();
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("chaosSidebar", sidebarProvider)
  );

  // -------------------------------
  // 3. SCAN COMMAND
  // -------------------------------
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
        const res = await fetch(`${backendBaseUrl}/scan/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path })
        });

        const data = (await res.json()) as ScanResponse;

        sidebarProvider.updateServices(data.services);

        vscode.window.showInformationMessage(
          `Chaos: scanned ${data.services.length} modules.`
        );

        // Send scan result to graph panel if open
        if (ChaosGraphPanel.currentPanel) {
          ChaosGraphPanel.currentPanel.sendMessage({
            type: "scanResult",
            payload: {
              graph: data.graph,
              results: data
            }
          });
        }

      } catch (err) {
        vscode.window.showErrorMessage(
          "Chaos scan failed. Backend may not be ready yet."
        );
      }
    }
  );

  // -------------------------------
  // 4. OPEN GRAPH COMMAND
  // -------------------------------
  const openGraphCommand = vscode.commands.registerCommand(
    "chaos.openGraph",
    async () => {
      const folder = vscode.workspace.workspaceFolders?.[0];
      if (!folder) {
        vscode.window.showErrorMessage("Open a workspace folder first.");
        return;
      }

      ChaosGraphPanel.createOrShow(
        context.extensionUri,
        folder.uri.fsPath,
        backendBaseUrl,
        (services: string[]) => sidebarProvider.updateServices(services)
      );
    }
  );

  context.subscriptions.push(scanCommand, openGraphCommand);
}

export function deactivate() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}
