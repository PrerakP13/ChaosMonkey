from backend.app.services.engines.level2_attack import run_level2
from backend.app.services.engines.level3_deep_static import run_level3

def analyze_project(services, dependencies):
    # Level 2 attack analysis
    attack_results = run_level2(services, dependencies)

    # Level 3 deep static analysis
    deep_results = run_level3(services, dependencies)

    # Existing structural analysis
    cycles = []
    for a, b in dependencies:
        if (b, a) in dependencies:
            cycles.append((a, b))

    incoming = {}
    for a, b in dependencies:
        incoming[b] = incoming.get(b, 0) + 1

    hotspots = [s for s, count in incoming.items() if count >= 3]

    connected = set([a for a, _ in dependencies] + [b for _, b in dependencies])
    orphans = [s for s in services if s not in connected]

    outgoing = set([a for a, _ in dependencies])
    leaf_nodes = [s for s in outgoing if s not in incoming]

    return {
        "cycles": cycles,
        "hotspots": hotspots,
        "orphans": orphans,
        "leaf_nodes": leaf_nodes,
        "dependency_count": incoming,
        "attack_surface": attack_results,
        "deep_static": deep_results
    }


def generate_recommendations(analysis):
    recs = []

    if analysis["cycles"]:
        recs.append("Break circular dependencies.")

    if analysis["hotspots"]:
        recs.append("High-risk modules detected. Add isolation or retries.")

    return recs
