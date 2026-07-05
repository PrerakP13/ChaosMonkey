def run_level4(services, dependencies, failed):
    """
    Level 4 — Dynamic Simulation
    Propagates failures through dependency graph.
    """
    failed = set(failed)
    degraded = set()

    # Build dependency map
    deps = {s: [] for s in services}
    for src, dst in dependencies:
        deps[src].append(dst)

    # Cascading failures
    changed = True
    while changed:
        changed = False
        for s in services:
            if s in failed:
                continue
            if deps[s] and all(d in failed for d in deps[s]):
                failed.add(s)
                changed = True

    # Degraded modules
    for s in services:
        if s in failed:
            continue
        if any(d in failed for d in deps[s]):
            degraded.add(s)

    effects = []

    for s in sorted(failed):
        effects.append({
            "service": s,
            "status": "FAILED",
            "reason": "Transitively failed due to dependency collapse."
        })

    for s in sorted(degraded):
        effects.append({
            "service": s,
            "status": "DEGRADED",
            "reason": "Depends on a failed module."
        })

    return {
        "failed": list(failed),
        "degraded": list(degraded),
        "effects": effects
    }
