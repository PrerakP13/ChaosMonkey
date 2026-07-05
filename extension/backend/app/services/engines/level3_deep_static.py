from typing import List, Tuple, Dict, Any
from collections import defaultdict, deque
from app.helpers.helper import make_vuln


def run_level3(services: List[str], dependencies: List[Tuple[str, str]]) -> Dict[str, Any]:
    print(f"[Level3] Starting with {len(services)} services, {len(dependencies)} dependencies")
    
    clean_deps: List[Tuple[str, str]] = []
    for edge in dependencies:
        if (
            isinstance(edge, (list, tuple))
            and len(edge) == 2
            and isinstance(edge[0], str)
            and isinstance(edge[1], str)
            and edge[0]
            and edge[1]
        ):
            clean_deps.append((edge[0], edge[1]))
    
    print(f"[Level3] After cleaning: {len(clean_deps)} valid dependencies")
    
    outgoing: Dict[str, set] = defaultdict(set)
    incoming: Dict[str, set] = defaultdict(set)

    for src, dst in dependencies:
        outgoing[src].add(dst)
        incoming[dst].add(src)

    for s in services:
        outgoing.setdefault(s, set())
        incoming.setdefault(s, set())

    # fan-in / fan-out
    fan_in = {s: len(incoming[s]) for s in services}
    fan_out = {s: len(outgoing[s]) for s in services}

    # roots / leaves
    roots = [s for s in services if fan_in[s] == 0]
    leaves = [s for s in services if fan_out[s] == 0]

    # depth (BFS from roots)
    depth: Dict[str, int] = {s: 0 for s in services}
    q = deque(roots)
    visited = set(roots)
    while q:
        n = q.popleft()
        for nb in outgoing[n]:
            if nb not in visited:
                depth[nb] = depth[n] + 1
                visited.add(nb)
                q.append(nb)

    # cycle detection (simple DFS)
    def in_cycle(node, visited, stack):
        visited.add(node)
        stack.add(node)
        for nb in outgoing[node]:
            if nb not in visited:
                if in_cycle(nb, visited, stack):
                    return True
            elif nb in stack:
                return True
        stack.remove(node)
        return False

    cycle_nodes = set()
    for s in services:
        if in_cycle(s, set(), set()):
            cycle_nodes.add(s)

    # centrality approximation: number of paths through node
    centrality = {s: 0 for s in services}
    for src, dst in dependencies:
        centrality[src] += 1
        centrality[dst] += 1

    # improved risk score
    def compute_risk(s):
        score = (
            fan_in[s] * 3.0 +
            fan_out[s] * 2.0 +
            depth[s] * 1.0 +
            centrality[s] * 1.5
        )
        if s in cycle_nodes:
            score *= 1.8  # cycles are dangerous
        return score

    risk_scores = {s: compute_risk(s) for s in services}
    max_risk = max(risk_scores.values(), default=0.0)
    threshold = max_risk * 0.65 if max_risk > 0 else 0

    vulns: List[Dict[str, Any]] = []
    for s, score in risk_scores.items():
        if score >= threshold and score > 0:
            vulns.append(
                make_vuln(
                    file=s,
                    line=None,
                    engine="level3",
                    kind="ARCHITECTURAL_HOTSPOT",
                    message=f"High structural risk (fan_in={fan_in[s]}, fan_out={fan_out[s]}, depth={depth[s]}, centrality={centrality[s]}, cycle={s in cycle_nodes}).",
                    severity="MEDIUM",
                    meta={
                        "fan_in": fan_in[s],
                        "fan_out": fan_out[s],
                        "depth": depth[s],
                        "centrality": centrality[s],
                        "in_cycle": s in cycle_nodes,
                        "risk": score,
                    },
                )
            )

    print(f"[Level3] Returning: fan_in={len(fan_in)}, fan_out={len(fan_out)}, cycles={len(cycle_nodes)}, roots={len(roots)}, leaves={len(leaves)}")
    
    return {
        "fan_in": fan_in,
        "fan_out": fan_out,
        "depth": depth,
        "centrality": centrality,
        "cycle_nodes": list(cycle_nodes),
        "roots": roots,
        "leaves": leaves,
        "edge_count": len(dependencies),
        "risk_scores": risk_scores,
        "vulnerabilities": vulns,
    }
