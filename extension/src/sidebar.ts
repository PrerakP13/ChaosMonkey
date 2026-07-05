import * as vscode from "vscode";

export class ChaosSidebarProvider
  implements vscode.TreeDataProvider<ServiceItem>
{
  private _onDidChangeTreeData: vscode.EventEmitter<
    ServiceItem | undefined | null | void
  > = new vscode.EventEmitter<ServiceItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<
    ServiceItem | undefined | null | void
  > = this._onDidChangeTreeData.event;

  private services: string[] = [];

  updateServices(services: string[]) {
    this.services = services;
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: ServiceItem): vscode.TreeItem {
    return element;
  }

  getChildren(): Thenable<ServiceItem[]> {
    return Promise.resolve(
      this.services.map((svc) => new ServiceItem(svc))
    );
  }
}

class ServiceItem extends vscode.TreeItem {
  constructor(label: string) {
    super(label, vscode.TreeItemCollapsibleState.None);
    this.tooltip = `Service: ${label}`;
    this.description = "";
  }
}
