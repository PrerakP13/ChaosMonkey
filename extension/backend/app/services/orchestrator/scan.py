import os
from typing import Dict, List, Tuple, Any

from app.services.orchestrator.dependency_scanner import (
    extract_dependencies,
    normalize_dependency_graph,
    discover_python_files
)

from app.services.scanner import run_all_scanners


def scan(path: str) -> Tuple[List[str], List[Tuple[str, str]], Dict[str, Any]]:
    """
    Returns:
        services
        dependencies
        vuln_results
    """

    if not os.path.exists(path):
        raise ValueError(f"Path does not exist: {path}")

    # 1. Discover all Python files
    services = discover_python_files(path)

    # 2. Extract dependency edges
    dep_graph = extract_dependencies(path)
    dependencies = normalize_dependency_graph(dep_graph)

    # 3. Run vulnerability scanners WITH dependencies
    vuln_results = run_all_scanners(path, services, dependencies)

    return services, dependencies, vuln_results


def enrich_services_with_vulns(
    services: List[str],
    vuln_results: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Turn raw service strings into node objects with attached vulnerability metadata.
    Currently only Level 2 produces per-service vulnerabilities.
    """

    service_map: Dict[str, Dict[str, Any]] = {
        svc: {"id": svc, "file": svc, "vulns": []}
        for svc in services
    }

    # Handle Level 2: {"vulnerabilities": [...], "no_imports": [...], "safe_services": [...]}
    level2 = vuln_results.get("level2")
    if isinstance(level2, dict):
        findings = level2.get("vulnerabilities", [])
        for f in findings:
            if not isinstance(f, dict):
                continue
            file = f.get("service") or f.get("file")
            if file in service_map:
                service_map[file]["vulns"].append(
                    f.get("issue", "LEVEL2_FINDING")
                )

    return list(service_map.values())
