import os
import ast

def run_level1(path: str):
    """
    Level 1 — Static Recon
    Scans the project and extracts:
      - all Python modules
      - all import relationships
    """
    services = []
    dependencies = []

    root = os.path.abspath(path)

    for r, _, files in os.walk(root):
        for f in files:
            if not f.endswith(".py"):
                continue

            full = os.path.join(r, f)
            rel = os.path.relpath(full, root).replace("\\", "/")
            services.append(rel)

            try:
                tree = ast.parse(open(full, "r", encoding="utf-8").read())
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        dependencies.append((rel, n.name))

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append((rel, node.module))

    return {
        "services": sorted(set(services)),
        "dependencies": sorted(set(dependencies)),
    }
