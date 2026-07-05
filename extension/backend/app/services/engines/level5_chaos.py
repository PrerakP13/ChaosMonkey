def run_level5(services, dependencies, failed):
    """
    Level 5 — Chaos Engine
    Builds failure/attack chains from each failed module.
    """
    graph = {s: [] for s in services}
    for src, dst in dependencies:
        graph[src].append(dst)

    results = []
    chaos_failed = set()

    for entry in failed:
        queue = [(entry, [entry])]
        visited = set()

        while queue:
            node, path = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)

            for nxt in graph.get(node, []):
                if nxt in path:
                    continue
                new_path = path + [nxt]
                queue.append((nxt, new_path))

                results.append({
                    "entry": entry,
                    "chain": new_path,
                    "length": len(new_path),
                    "detail": f"Potential failure chain: {' → '.join(new_path)}"
                })

                chaos_failed.add(nxt)

    effects = [
        {
            "service": f,
            "status": "FAILED",
            "reason": "Chaos engine propagated failure."
        }
        for f in chaos_failed
    ]

    return {
        "failed": list(chaos_failed),
        "chains": results,
        "effects": effects
    }
