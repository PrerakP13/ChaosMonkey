def build_graph(services, dependencies, vuln_results):
    # Build node map
    node_map = {s: {"id": s, "label": s, "vulns": []} for s in services}

    # Attach vulnerabilities from all levels
    for level, result in vuln_results.items():

        # Level 2 style: {"vulnerabilities": [...]}
        if isinstance(result, dict) and "vulnerabilities" in result:
            findings = result["vulnerabilities"]

        # Level 4 style: {"dynamic_effects": [...]}
        elif isinstance(result, dict) and "dynamic_effects" in result:
            findings = result["dynamic_effects"]

        # Level 1, 3, 5 have no per-file vulnerabilities
        else:
            continue

        # Process each vulnerability entry
        for f in findings:
            if not isinstance(f, dict):
                continue

            file = f.get("service") or f.get("file")
            if file in node_map:
                node_map[file]["vulns"].append(level.upper())

    # Convert to Cytoscape format
    nodes = list(node_map.values())
    edges = [{"source": a, "target": b} for a, b in dependencies]

    return {"nodes": nodes, "edges": edges}
