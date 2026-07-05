from typing import List, Tuple, Dict, Any, Set
from collections import deque, defaultdict
from app.helpers.helper import make_vuln


def run_level5(
    services: List[str],
    dependencies: List[Tuple[str, str]],
    failed: List[str],
    taint_vulns: List[Dict[str, Any]] | None = None,
    risk_scores: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    print(f"[Level5] Starting with {len(services)} services, {len(dependencies)} dependencies, {len(failed)} failed")
    print(f"[Level5] Failed services: {failed}")
    
    graph: Dict[str, List[str]] = {s: [] for s in services}
    for src, dst in dependencies:
        graph.setdefault(src, []).append(dst)

    risk_scores = risk_scores or {}

    chaos_entries: Set[str] = set(failed)
    taint_entries: Set[str] = set()

    if taint_vulns:
        for v in taint_vulns:
            f = v.get("file")
            if f:
                taint_entries.add(f)

    chains: List[Dict[str, Any]] = []
    chaos_failed: Set[str] = set(chaos_entries)
    taint_reach: Set[str] = set(taint_entries)

    def explore(entry: str, kind: str):
        queue = deque([(entry, [entry])])
        visited: Set[str] = set()

        while queue:
            node, path = queue.popleft()
            if node in visited:
                continue
            visited.add(node)

            for nxt in graph.get(node, []):
                if nxt in path:
                    continue
                new_path = path + [nxt]
                queue.append((nxt, new_path))

                if kind == "chaos":
                    chaos_failed.add(nxt)
                else:
                    taint_reach.add(nxt)

                # chain score: length + average risk along path
                length = len(new_path)
                avg_risk = sum(risk_scores.get(s, 0.0) for s in new_path) / length
                score = length * 2.0 + avg_risk * 1.5

                chains.append(
                    {
                        "entry": entry,
                        "kind": kind,  # "chaos" or "taint"
                        "chain": new_path,
                        "length": length,
                        "detail": " → ".join(new_path),
                        "score": score,
                    }
                )

    for entry in chaos_entries:
        explore(entry, "chaos")

    for entry in taint_entries:
        explore(entry, "taint")

    # dedupe chains by (entry, last, kind)
    seen_keys = set()
    deduped_chains = []
    for c in sorted(chains, key=lambda x: -x["score"]):
        key = (c["entry"], c["chain"][-1], c["kind"])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped_chains.append(c)

    effects = [
        {
            "service": s,
            "status": "FAILED",
            "reason": "Chaos engine propagated failure along attack chain.",
        }
        for s in sorted(chaos_failed)
        if s not in chaos_entries
    ]

    fanout: Dict[str, int] = defaultdict(int)
    for c in deduped_chains:
        if len(c["chain"]) >= 2:
            fanout[c["entry"]] += 1

    vulns: List[Dict[str, Any]] = []
    for c in deduped_chains:
        last = c["chain"][-1]
        chain_type = "CHAOS_CHAIN" if c["kind"] == "chaos" else "TAINT_CHAIN"
        vulns.append(
            make_vuln(
                file=last,
                line=None,
                engine="level5",
                kind="ATTACK_CHAIN",
                message=f"{chain_type}: {c['entry']} → {last}",
                detail=f"{c['detail']} (score={round(c['score'], 2)})",
                severity="HIGH" if c["kind"] == "chaos" else "MEDIUM",
                meta={
                    "chain": c["chain"],
                    "length": c["length"],
                    "entry_kind": c["kind"],
                    "fanout_from_entry": fanout.get(c["entry"], 0),
                    "chain_score": c["score"],
                },
            )
        )

    print(f"[Level5] Returning: failed={list(chaos_failed)}, chains={len(deduped_chains)}, effects={len(effects)}")
    
    return {
        "failed": list(chaos_failed),
        "taint_reach": list(taint_reach),
        "chains": deduped_chains,
        "effects": effects,
        "vulnerabilities": vulns,
    }
