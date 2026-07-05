import os
import ast
from typing import Dict, List, Any, Tuple

from app.helpers.helper import compute_resilience
from app.services.engines.level1_static import run_level1
from app.services.engines.level2_attack import run_level2
from app.services.engines.level3_deep_static import run_level3
from app.services.engines.level4_dynamic import run_level4
from app.services.engines.level5_chaos import run_level5

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
) -> Dict[str, Any]:

    results: Dict[str, Any] = {}

    # Level 1
    results["level1"] = run_level1(root_path)

    # Level 2 (pattern + taint)
    level2 = run_level2(root_path, services, dependencies)
    results["level2"] = level2

    # Chaos failures (HIGH/CRITICAL)
    initial_failed = [
        v.get("file")
        for v in level2.get("vulnerabilities", [])
        if v.get("severity") in ("HIGH", "CRITICAL")
    ]

    # Taint vulns for Level 5
    taint_vulns = [
        v for v in level2.get("vulnerabilities", [])
        if v.get("engine") == "taint"
    ]

    # Level 3 — Architectural Risk
    level3 = run_level3(services, dependencies)
    results["level3"] = level3

    # Level 4 — Dynamic Simulation
    level4 = run_level4(
        services,
        dependencies,
        failed=initial_failed
    )
    results["level4"] = level4

    # Level 5 — Chaos + Taint Attack Chains (with risk-aware scoring)
    level5 = run_level5(
        services,
        dependencies,
        failed=initial_failed,
        taint_vulns=taint_vulns,
        risk_scores=level3.get("risk_scores", {}),
    )
    results["level5"] = level5

    # Resilience score
    results["resilience"] = compute_resilience(level3, level4, level5)

    return results
