from app.services.engines.level4_dynamic import run_level4
from app.services.engines.level5_chaos import run_level5
from app.services.engines.level3_deep_static import run_level3  # if you have it
import json


def simulate_failures(services, dependencies, failed):
    print("[simulate_failures] Starting simulation")
    print(f"[simulate_failures] Input services ({len(services)}): {services[:3]}...")
    print(f"[simulate_failures] Input failed: {failed}")
    print(f"[simulate_failures] Input dependencies ({len(dependencies)}): {dependencies[:2] if dependencies else 'none'}...")
    
    # Normalize dependencies
    clean_deps = []
    for dep in dependencies:
        if isinstance(dep, dict):
            src = dep.get("source")
            dst = dep.get("target")
            if src and dst:
                clean_deps.append((src, dst))
        elif isinstance(dep, (list, tuple)) and len(dep) == 2:
            clean_deps.append((dep[0], dep[1]))

    print(f"[simulate_failures] After normalization: {len(clean_deps)} dependencies")

    # LEVEL 3 — Deep static analysis
    level3 = run_level3(services, clean_deps)
    print(f"[simulate_failures] Level3 complete: fan_in keys={list(level3.get('fan_in', {}).keys())[:2]}...")

    # LEVEL 4 — Runtime propagation
    level4 = run_level4(services, clean_deps, failed)
    print(f"[simulate_failures] Level4 complete: failed={level4['failed']}, effects={len(level4['effects'])}")

    # LEVEL 5 — Attack chains
    level5 = run_level5(services, clean_deps, level4["failed"])
    print(f"[simulate_failures] Level5 complete: failed={level5['failed']}, chains={len(level5['chains'])}")

    # Merge failures
    final_failed = set(level4["failed"]) | set(level5["failed"])
    final_effects = level4["effects"] + level5["effects"]
    
    print(f"[simulate_failures] Merged: final_failed={final_failed}, final_effects={len(final_effects)}")

    # Build detailed per-node report
    detailed = []
    for svc in final_failed:
        arch = {
            "fan_in": level3["fan_in"].get(svc, 0),
            "fan_out": level3["fan_out"].get(svc, 0),
            "depth": level3["depth"].get(svc, 0),
            "centrality": level3["centrality"].get(svc, 0),
            "risk_score": level3["risk_scores"].get(svc, 0),
            "in_cycle": svc in level3.get("cycle_nodes", [])
        }

        runtime = next((e for e in final_effects if e["service"] == svc), {})
        chains = [c for c in level5.get("chains", []) if svc in c["chain"]]

        detailed.append({
            "service": svc,
            "status": runtime.get("status", "FAILED"),
            "architecture": arch,
            "runtime": {
                "failure_depth": runtime.get("depth"),
                "failure_fanout": runtime.get("fanout")
            },
            "chains": chains
        })

    # Compute resilience
    failed_count = len(final_failed)
    degraded_count = len([e for e in final_effects if e.get("status") == "DEGRADED"])
    resilience = max(0, 100 - (failed_count * 5 + degraded_count * 2))

    result = {
        "failed": list(final_failed),
        "detailed": detailed,
        "effects": final_effects,
        "chains": level5.get("chains", []),
        "resilience": resilience
    }
    
    print(f"[simulate_failures] Final result: failed={len(result['failed'])}, detailed={len(result['detailed'])}, effects={len(result['effects'])}, chains={len(result['chains'])}, resilience={result['resilience']}")
    
    return result
