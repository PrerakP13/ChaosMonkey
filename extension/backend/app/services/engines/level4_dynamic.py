from typing import List, Tuple, Dict, Any, Set
from collections import defaultdict, deque
from app.helpers.helper import make_vuln


def run_level4(
    services: List[str],
    dependencies: List[Tuple[str, str]],
    failed: List[str],
) -> Dict[str, Any]:
    print(f"[Level4] Starting with {len(services)} services, {len(dependencies)} dependencies, {len(failed)} failed")
    print(f"[Level4] Failed services: {failed}")

    # Build dependency map
    deps: Dict[str, List[str]] = defaultdict(list)
    rev: Dict[str, List[str]] = defaultdict(list)

    for src, dst in dependencies:
        deps[src].append(dst)
        rev[dst].append(src)
    
    print(f"[Level4] Built deps map: {dict(deps)}")

    failed_set: Set[str] = set(failed)
    degraded: Set[str] = set()

    # Track failure depth (how many hops from initial failure)
    failure_depth: Dict[str, int] = {s: (0 if s in failed_set else None) for s in services}

    # Propagate failures
    q = deque([(s, 0) for s in failed_set])
    visited = set(failed_set)

    while q:
        node, depth = q.popleft()
        for nxt in deps.get(node, []):
            if nxt not in visited:
                # fail only if ALL dependencies are failed
                if deps[nxt] and all(d in failed_set for d in deps[nxt]):
                    failed_set.add(nxt)
                    visited.add(nxt)
                    failure_depth[nxt] = depth + 1
                    q.append((nxt, depth + 1))

    # Mark degraded modules
    for s in services:
        if s not in failed_set:
            if any(d in failed_set for d in deps.get(s, [])):
                degraded.add(s)
                if failure_depth[s] is None:
                    # Get the max depth from dependencies, filtering out None values
                    dep_depths = []
                    for d in deps.get(s, []):
                        if d in failure_depth and failure_depth[d] is not None:
                            dep_depths.append(failure_depth[d])
                    max_depth = max(dep_depths) if dep_depths else 0
                    failure_depth[s] = max_depth + 1

    # Compute failure fan-out (how many modules each failure affects)
    fanout = {s: 0 for s in services}
    for src, dst in dependencies:
        if src in failed_set:
            fanout[src] += 1

    # Build effects list
    effects: List[Dict[str, Any]] = []
    for s in sorted(failed_set):
        effects.append({
            "service": s,
            "status": "FAILED",
            "reason": "Dependency collapse failure.",
            "depth": failure_depth.get(s, 0),
            "fanout": fanout.get(s, 0),
        })

    for s in sorted(degraded):
        effects.append({
            "service": s,
            "status": "DEGRADED",
            "reason": "Depends on a failed module.",
            "depth": failure_depth.get(s, 0),
            "fanout": fanout.get(s, 0),
        })

    # Convert to vulnerabilities
    vulns: List[Dict[str, Any]] = []
    for eff in effects:
        kind = "RUNTIME_FAILED" if eff["status"] == "FAILED" else "RUNTIME_DEGRADED"
        vulns.append(
            make_vuln(
                file=eff["service"],
                line=None,
                engine="level4",
                kind=kind,
                message=eff["reason"],
                detail=f"depth={eff['depth']}, fanout={eff['fanout']}",
                severity="HIGH",
                meta={
                    "source": eff["service"],
                    "depth": eff["depth"],
                    "fanout": eff["fanout"],
                    "status": eff["status"],
                },
            )
        )

    print(f"[Level4] Returning: failed={list(failed_set)}, degraded={list(degraded)}, effects={len(effects)}")
    
    return {
        "failed": list(failed_set),
        "degraded": list(degraded),
        "effects": effects,
        "failure_depth": failure_depth,
        "failure_fanout": fanout,
        "vulnerabilities": vulns,
    }
