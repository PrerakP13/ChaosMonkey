def node_severity_color(max_severity: str) -> str:
    mapping = {
        "CRITICAL": "#d32f2f",
        "HIGH": "#f57c00",
        "MEDIUM": "#fbc02d",
        "LOW": "#388e3c",
        "INFO": "#1976d2",
    }
    return mapping.get(max_severity or "INFO", "#1976d2")


def node_status_border(status: str) -> str:
    mapping = {
        "FAILED": "#d32f2f",
        "DEGRADED": "#f57c00",
        "OK": "#388e3c",
    }
    return mapping.get(status or "OK", "#388e3c")


def edge_chain_color(kind: str) -> str:
    mapping = {
        "CHAOS_CHAIN": "#d32f2f",
        "TAINT_CHAIN": "#7b1fa2",
        "HYBRID_CHAIN": "#c2185b",
    }
    return mapping.get(kind, "#9e9e9e")


# ---------------------------------------------------------
# SANITY CHECK
# ---------------------------------------------------------
def validate_graph(nodes, edges):
    print("\n[GRAPH VALIDATION] Running backend sanity check…")

    node_ids = set()

    # Validate nodes
    for i, n in enumerate(nodes):
        d = n.get("data", {})
        nid = d.get("id")
        label = d.get("label")

        if not nid:
            print(f"[GRAPH VALIDATION] ❌ BAD NODE #{i}: missing id → {d}")
        if not label:
            print(f"[GRAPH VALIDATION] ❌ BAD NODE #{i}: missing label → {d}")

        node_ids.add(nid)

    # Validate edges
    for i, e in enumerate(edges):
        d = e.get("data", {})
        eid = d.get("id")
        src = d.get("source")
        dst = d.get("target")

        if not eid:
            print(f"[GRAPH VALIDATION] ❌ BAD EDGE #{i}: missing id → {d}")
        if not src:
            print(f"[GRAPH VALIDATION] ❌ BAD EDGE #{i}: missing source → {d}")
        if not dst:
            print(f"[GRAPH VALIDATION] ❌ BAD EDGE #{i}: missing target → {d}")

        if src not in node_ids:
            print(f"[GRAPH VALIDATION] ⚠️ EDGE #{i} SOURCE NOT IN NODES: {src}")
        if dst not in node_ids:
            print(f"[GRAPH VALIDATION] ⚠️ EDGE #{i} TARGET NOT IN NODES: {dst}")

    print("[GRAPH VALIDATION] Done.\n")


# ---------------------------------------------------------
# MAIN GRAPH BUILDER
# ---------------------------------------------------------
def build_graph(services, dependencies, vuln_results):
    """
    Build Cytoscape graph with FULL metadata from Level 2–5.
    """

    # ---------------------------------------------------------
    # 1. Initialize node map
    # ---------------------------------------------------------
    node_map = {}

    for s in services:
        file = s if isinstance(s, str) else s["file"]

        # Skip __init__.py files entirely
        if file.endswith("/__init__.py") or file == "__init__.py":
            continue

        node_map[file] = {
            "id": file,
            "label": file,
            "severity": "INFO",
            "status": "OK",
            "color": "#1976d2",
            "borderColor": "#388e3c",
            "vulns": [],
            "risk_score": 0,
            "fan_in": 0,
            "fan_out": 0,
            "depth": 0,
            "centrality": 0,
            "in_cycle": False,
            "failure_depth": None,
            "failure_fanout": 0,
            "chains": []
        }

    # ---------------------------------------------------------
    # 2. LEVEL 2 — Vulnerabilities
    # ---------------------------------------------------------
    level2 = vuln_results.get("level2", {})
    for v in level2.get("vulnerabilities", []):
        file = v.get("file")
        if file not in node_map:
            continue

        sev = v.get("severity", "INFO")
        node_map[file]["vulns"].append(v)

        order = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if order.index(sev) > order.index(node_map[file]["severity"]):
            node_map[file]["severity"] = sev

    # ---------------------------------------------------------
    # 3. LEVEL 3 — Architectural Risk
    # ---------------------------------------------------------
    level3 = vuln_results.get("level3", {})

    fan_in = level3.get("fan_in", {})
    fan_out = level3.get("fan_out", {})
    depth = level3.get("depth", {})
    centrality = level3.get("centrality", {})
    cycle_nodes = set(level3.get("cycle_nodes", []))
    risk_scores = level3.get("risk_scores", {})

    for file, node in node_map.items():
        node["fan_in"] = fan_in.get(file, 0)
        node["fan_out"] = fan_out.get(file, 0)
        node["depth"] = depth.get(file, 0)
        node["centrality"] = centrality.get(file, 0)
        node["in_cycle"] = file in cycle_nodes
        node["risk_score"] = risk_scores.get(file, 0)

    # ---------------------------------------------------------
    # 4. LEVEL 4 — Runtime Failures
    # ---------------------------------------------------------
    level4 = vuln_results.get("level4", {})
    for eff in level4.get("effects", []):
        file = eff.get("service")
        if file not in node_map:
            continue

        node_map[file]["status"] = eff.get("status", "OK")
        node_map[file]["failure_depth"] = eff.get("depth")
        node_map[file]["failure_fanout"] = eff.get("fanout", 0)

    # ---------------------------------------------------------
    # 5. LEVEL 5 — Attack Chains
    # ---------------------------------------------------------
    level5 = vuln_results.get("level5", {})
    chain_edges = []

    for chain in level5.get("chains", []):
        path = chain["chain"]
        kind = chain["kind"]
        score = chain.get("score", 0)

        for node in path:
            if node in node_map:
                node_map[node]["chains"].append({
                    "kind": kind,
                    "score": score,
                    "path": path
                })

        for i in range(len(path) - 1):
            chain_edges.append((path[i], path[i+1], kind, score))

    # ---------------------------------------------------------
    # 6. Apply severity + status → colors
    # ---------------------------------------------------------
    for file, node in node_map.items():
        node["color"] = node_severity_color(node["severity"])
        node["borderColor"] = node_status_border(node["status"])

    # ---------------------------------------------------------
    # 7. Build Cytoscape nodes
    # ---------------------------------------------------------
    nodes = [{"data": node_map[file]} for file in node_map]

    # ---------------------------------------------------------
    # 8. Build Cytoscape edges
    # ---------------------------------------------------------
    edges = []
    for src, dst in dependencies:
        chain_kind = None
        chain_score = None

        for a, b, k, s in chain_edges:
            if a == src and b == dst:
                chain_kind = k
                chain_score = s
                break

        edges.append({
            "data": {
                "id": f"{src}_{dst}",
                "source": src,
                "target": dst,
                "is_chain": chain_kind is not None,
                "chain_kind": chain_kind,
                "chain_score": chain_score,
                "color": edge_chain_color(chain_kind)
            }
        })

    # ---------------------------------------------------------
    # 9. Run backend sanity check
    # ---------------------------------------------------------
    validate_graph(nodes, edges)

    return {"nodes": nodes, "edges": edges}
