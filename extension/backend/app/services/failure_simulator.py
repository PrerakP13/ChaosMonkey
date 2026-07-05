from backend.app.services.engines.level4_dynamic import run_level4
from backend.app.services.engines.level5_chaos import run_level5


def simulate_failures(services, dependencies, failed):
    # Normalize dependencies: convert dicts → tuples
    clean_deps = []
    for dep in dependencies:
        if isinstance(dep, dict):
            src = dep.get("source")
            dst = dep.get("target")
            if src and dst:
                clean_deps.append((src, dst))
        elif isinstance(dep, (list, tuple)) and len(dep) == 2:
            clean_deps.append((dep[0], dep[1]))

    # Run Level 4 (dynamic propagation)
    level4 = run_level4(services, clean_deps, failed)

    # Run Level 5 (chaos propagation)
    level5 = run_level5(services, clean_deps, level4["failed"])

    # Merge failed nodes
    final_failed = set(level4["failed"]) | set(level5["failed"])

    # Merge effects
    final_effects = level4["effects"] + level5["effects"]

    return {
        "failed": list(final_failed),
        "effects": final_effects,
        "dynamic_effects": level4,
        "chaos_results": level5,
        "graph": {
            "nodes": [{"id": s, "failed": s in final_failed} for s in services],
            "edges": [{"source": a, "target": b} for a, b in clean_deps]
        }
    }
