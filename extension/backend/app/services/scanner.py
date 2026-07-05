import os
import ast
from typing import Dict, List, Any, Tuple

from backend.app.services.engines.level1_static import run_level1
from backend.app.services.engines.level2_attack import run_level2
from backend.app.services.engines.level3_deep_static import run_level3

def scan_project(path: str):
    services = []
    dependencies = []

    for root, _, files in os.walk(path):
        if ".venv" in root or "venv" in root or "__pycache__" in root:
            continue

        for f in files:
            if f.endswith(".py"):
                full = os.path.join(root, f)
                module = full.replace(path, "").replace("\\", "/")
                services.append(module)

                with open(full, "r", encoding="utf-8") as src:
                    tree = ast.parse(src.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for n in node.names:
                            dependencies.append((module, n.name))

                    if isinstance(node, ast.ImportFrom):
                        if node.module:
                            dependencies.append((module, node.module))

    return services, dependencies




def run_all_scanners(
    root_path: str,
    services: List[str],
    dependencies: List[Tuple[str, str]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Unified entry point for all vulnerability scanners.
    """

    return {
        "level1": run_level1(root_path),
        "level2": run_level2(services, dependencies),
        "level3": run_level3(services, dependencies),
         }
