import hashlib
from typing import Dict, Any, Optional

SEVERITY_MAP = {
    "SQL_INJECTION": "CRITICAL",
    "TAINTED_SQL_INJECTION": "CRITICAL",
    "COMMAND_INJECTION": "CRITICAL",
    "TAINTED_COMMAND_INJECTION": "CRITICAL",
    "PATH_TRAVERSAL": "HIGH",
    "INSECURE_DESERIALIZATION": "HIGH",
    "HARDCODED_SECRET": "HIGH",
    "WEAK_CRYPTO": "MEDIUM",
    "INSECURE_RANDOM": "LOW",
    "DANGEROUS_FUNCTION": "HIGH",
    "INSECURE_HTTP": "MEDIUM",
    "XSS": "HIGH",
    "ARCHITECTURAL_HOTSPOT": "MEDIUM",
    "RUNTIME_FAILED": "HIGH",
    "RUNTIME_DEGRADED": "MEDIUM",
    "ATTACK_CHAIN": "CRITICAL",
}

def severity_for(kind: str, default: str = "MEDIUM") -> str:
    return SEVERITY_MAP.get(kind, default)


def make_vuln(
    *,
    file: str,
    line: Optional[int],
    engine: str,
    kind: str,
    severity: str,
    message: str,
    detail: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base = f"{file}:{line}:{engine}:{kind}:{message}"
    vid = hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]
    return {
        "id": vid,
        "file": file,
        "line": line,
        "engine": engine,
        "kind": kind,
        "severity": severity,
        "message": message,
        "detail": detail,
        "meta": meta or {},
    }



def compute_resilience(level3: Dict[str, Any],
                       level4: Dict[str, Any],
                       level5: Dict[str, Any]) -> Dict[str, Any]:
    # Level 3: architectural risk (higher risk → lower resilience)
    risk_scores = level3.get("risk_scores", {})
    max_risk = max(risk_scores.values(), default=0.0)
    avg_risk = sum(risk_scores.values()) / len(risk_scores) if risk_scores else 0.0

    # Level 4: runtime impact
    failed = set(level4.get("failed", []))
    degraded = set(level4.get("degraded", []))
    total = max(len(risk_scores), 1)

    failed_ratio = len(failed) / total
    degraded_ratio = len(degraded) / total

    # Level 5: attack chains
    chains = level5.get("chains", [])
    max_chain_len = max((c.get("length", 0) for c in chains), default=0)
    chain_count = len(chains)

    # Normalize components into 0–100 penalties
    risk_penalty = min(avg_risk / (max_risk or 1.0) * 40.0, 40.0) if max_risk > 0 else 0.0
    failure_penalty = min(failed_ratio * 35.0 + degraded_ratio * 15.0, 50.0)
    chain_penalty = min(chain_count * 2.0 + max_chain_len * 3.0, 40.0)

    raw_score = 100.0 - (risk_penalty + failure_penalty + chain_penalty)
    score = max(0.0, min(100.0, raw_score))

    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    return {
        "score": round(score, 2),
        "grade": grade,
        "components": {
            "risk_penalty": risk_penalty,
            "failure_penalty": failure_penalty,
            "chain_penalty": chain_penalty,
            "failed_ratio": failed_ratio,
            "degraded_ratio": degraded_ratio,
            "max_chain_len": max_chain_len,
            "chain_count": chain_count,
        },
    }
