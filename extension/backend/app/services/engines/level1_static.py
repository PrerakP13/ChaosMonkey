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
    
    # Skip directories and files
    skip_dirs = {".venv", "venv", "__pycache__", ".env", "tests", "test", ".git", "node_modules"}

    for r, dirs, files in os.walk(root):
        # Filter out directories to skip
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".env") and not d.startswith(".")]
        
        for f in files:
            if not f.endswith(".py"):
                continue
            
            # Skip test files and other files that shouldn't be scanned
            if f.startswith("test_") or f.endswith("_test.py") or f in ("setup.py", "conftest.py"):
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
