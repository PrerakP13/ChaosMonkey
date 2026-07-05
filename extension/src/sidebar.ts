import * as vscode from "vscode";

class ChaosNode extends vscode.TreeItem {
  constructor(label: string) {
    super(label, vscode.TreeItemCollapsibleState.None);
    this.contextValue = "chaosService";
  }
}

export class ChaosSidebarProvider implements vscode.TreeDataProvider<ChaosNode> {
  private _onDidChangeTreeData: vscode.EventEmitter<ChaosNode | undefined | void> =
    new vscode.EventEmitter<ChaosNode | undefined | void>();
  readonly onDidChangeTreeData: vscode.Event<ChaosNode | undefined | void> =
    this._onDidChangeTreeData.event;

  private services: string[] = [];

  updateServices(services: string[]) {
    this.services = services;
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: ChaosNode): vscode.TreeItem {
    return element;
  }

  getChildren(): Thenable<ChaosNode[]> {
    return Promise.resolve(this.services.map((s) => new ChaosNode(s)));
  }
}
