# backend/app/services/engines/level3_deep_static.py

from typing import List, Tuple, Dict, Any, Union
from collections import defaultdict, deque


Dependency = Union[Tuple[str, str], Dict[str, str]]


def _normalize_dependencies(dependencies: List[Dependency]) -> List[Tuple[str, str]]:
    """
    Normalize dependencies into a list of (source, target) tuples.

    Accepts:
      - {"source": "A", "target": "B"}
      - ("A", "B") or ["A", "B"]
    """
    normalized: List[Tuple[str, str]] = []

    for dep in dependencies:
        if isinstance(dep, dict):
            src = dep.get("source")
            dst = dep.get("target")
            if src and dst:
                normalized.append((src, dst))
        elif isinstance(dep, (list, tuple)) and len(dep) == 2:
            src, dst = dep
            if src and dst:
                normalized.append((str(src), str(dst)))

    return normalized


def run_level3(services: List[str], dependencies: List[Dependency]) -> Dict[str, Any]:
    """
    Deep static analysis of the dependency graph.

    Returns:
      - fan_in:  how many services depend on each service
      - fan_out: how many services each service depends on
      - depth:   approximate depth from roots
      - roots:   services with no incoming edges
      - leaves:  services with no outgoing edges
    """

    # 1) Normalize dependencies to (src, dst) tuples
    deps: List[Tuple[str, str]] = _normalize_dependencies(dependencies)

    # 2) Build adjacency + reverse adjacency
    outgoing: Dict[str, set] = defaultdict(set)
    incoming: Dict[str, set] = defaultdict(set)

    for src, dst in deps:
        outgoing[src].add(dst)
        incoming[dst].add(src)

    # Ensure all services appear in maps
    for s in services:
        outgoing.setdefault(s, set())
        incoming.setdefault(s, set())

    # 3) Fan-in / Fan-out
    fan_in = {s: len(incoming[s]) for s in services}
    fan_out = {s: len(outgoing[s]) for s in services}

    # 4) Roots (no incoming) and leaves (no outgoing)
    roots = [s for s in services if fan_in[s] == 0]
    leaves = [s for s in services if fan_out[s] == 0]

    # 5) Approximate depth from roots using BFS
    depth: Dict[str, int] = {s: 0 for s in services}
    queue = deque(roots)

    visited = set(roots)
    while queue:
        node = queue.popleft()
        for neighbor in outgoing[node]:
            if neighbor not in visited:
                depth[neighbor] = depth[node] + 1
                visited.add(neighbor)
                queue.append(neighbor)

    return {
        "fan_in": fan_in,
        "fan_out": fan_out,
        "depth": depth,
        "roots": roots,
        "leaves": leaves,
        "edge_count": len(deps),
    }
