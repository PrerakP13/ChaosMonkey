import os
from typing import Dict, List, Tuple, Any

from backend.app.services.orchestrator.dependency_scanner import (
    extract_dependencies,
    normalize_dependency_graph,
    discover_python_files
)

from backend.app.services.scanner import run_all_scanners

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




def enrich_services_with_vulns(services: List[str], vuln_results: Dict[str, List[Dict[str, Any]]]):
    """
    Attach vulnerability metadata to each service/file.
    Output format matches what graph_builder expects.
    """

    service_map = {svc: {"file": svc, "vulns": []} for svc in services}

    for vuln_type, findings in vuln_results.items():
        for f in findings:
            file = f.get("file")
            if file in service_map:
                service_map[file]["vulns"].append(vuln_type.upper())

    # graph_builder expects a list of strings or objects depending on your version
    # If your graph_builder expects plain strings, return services unchanged
    # If it expects metadata, return enriched objects
    # For now, return plain strings (your current graph_builder uses strings)
    return services
