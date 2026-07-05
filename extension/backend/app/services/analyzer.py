import json
import os
from pathlib import Path

from dotenv import load_dotenv
from app.services.engines.level3_deep_static import run_level3
from app.services.model_manager import get_model_path, get_cached_models

BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_ROOT / "config.env")


def get_report_generation_settings():
    max_tokens = int(os.environ.get("CHAOS_REPORT_MAX_TOKENS", "2200"))
    n_ctx = int(os.environ.get("CHAOS_REPORT_N_CTX", "4096"))
    return max_tokens, n_ctx


def analyze_project(services, dependencies):
    # Level 3 deep static analysis only
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
        "deep_static": deep_results
    }


def get_local_model_path():
    """
    Get local model path. If not found, attempt to auto-download.
    Priority: environment variable > auto-download > None
    """
    # Check environment variable first
    env_path = os.environ.get("LLAMA_CPP_MODEL_PATH") or os.environ.get("LOCAL_AI_MODEL_PATH")
    if env_path and Path(env_path).exists():
        print(f"[get_local_model_path] Found model at env path: {env_path}")
        return env_path
    
    # Try to auto-download model
    try:
        model_path = get_model_path("mistral-7b")
        if model_path:
            print(f"[get_local_model_path] Found/downloaded model at: {model_path}")
            return str(model_path)
    except Exception as e:
        print(f"[get_local_model_path] Warning: Could not auto-download model: {e}")
    
    print(f"[get_local_model_path] No model path found")
    return None


def build_report_prompt(
    services,
    dependencies,
    vulnerabilities,
    chains,
    analysis,
):
    # Build vulnerability breakdown
    vuln_breakdown = {}
    severity_breakdown = {}
    if vulnerabilities:
        for v in vulnerabilities:
            if isinstance(v, dict):
                kind = v.get('kind', v.get('engine', 'unknown'))
                severity = v.get('severity', 'UNKNOWN')
                vuln_breakdown[kind] = vuln_breakdown.get(kind, 0) + 1
                severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1
    
    vuln_types_str = ", ".join(f"{k}({c})" for k, c in sorted(vuln_breakdown.items()))
    severity_str = ", ".join(f"{s}({c})" for s, c in sorted(severity_breakdown.items()))
    
    # Build attack chains info
    chains_info = f"{len(chains)} attack chains detected" if chains else "No attack chains detected"
    
    prompt = (
        "You are a senior security architect reviewing a codebase. Provide a detailed technical analysis report covering:\n"
        "1. System Architecture Overview\n"
        "2. Vulnerability Assessment (breakdown by type and severity)\n"
        "3. Risk Analysis (immediate concerns and blast radius)\n"
        "4. Remediation Priorities (what to fix first)\n"
        "5. Long-term Security Roadmap\n\n"
        "Use technical language appropriate for engineering leadership. Reference specific patterns and OWASP principles.\n\n"
        f"SCAN RESULTS:\n"
        f"- System Composition: {len(services)} modules with {len(dependencies)} dependencies\n"
        f"- Total Vulnerabilities: {len(vulnerabilities)}\n"
        f"- Vulnerability Types: {vuln_types_str if vuln_types_str else 'None'}\n"
        f"- Severity Distribution: {severity_str if severity_str else 'None'}\n"
        f"- Attack Chains: {chains_info}\n"
        f"- Hotspots: {len(analysis.get('hotspots', []))} high-dependency modules\n"
        f"- Circular Dependencies: {len(analysis.get('cycles', []))} detected\n\n"
        "Provide a comprehensive security assessment:"
    )
    return prompt


def generate_report_with_local_model(prompt, model_path, max_tokens=None):
    try:
        from llama_cpp import Llama
    except ImportError:
        print(f"[generate_report_with_local_model] llama_cpp not installed")
        return None

    if not model_path:
        print(f"[generate_report_with_local_model] No model path provided")
        return None

    if max_tokens is None:
        max_tokens, n_ctx = get_report_generation_settings()
    else:
        n_ctx = int(os.environ.get("CHAOS_REPORT_N_CTX", "4096"))

    try:
        print(f"[generate_report_with_local_model] Loading model from: {model_path}")
        llm = Llama(
            model_path=model_path,
            n_threads=os.cpu_count() or 4,
            temperature=0.3,
            n_ctx=n_ctx,
            verbose=False
        )
        print(f"[generate_report_with_local_model] Model loaded, generating detailed response (max_tokens={max_tokens}, n_ctx={n_ctx})...")
        result = llm(prompt, max_tokens=max_tokens, top_p=0.95)
        text = result["choices"][0]["text"].strip()
        print(f"[generate_report_with_local_model] Response generated (length={len(text)})")
        return text
    except Exception as e:
        print(f"[generate_report_with_local_model] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_recommendations(analysis):
    recs = []

    if analysis.get("cycles"):
        recs.append("Break circular dependencies.")

    if analysis.get("hotspots"):
        recs.append("High-risk modules detected. Add isolation or retries.")

    return recs


def generate_recommendation_report(
    analysis: dict,
    services=None,
    dependencies=None,
    graph=None,
    vulnerabilities=None,
    chains=None,
):
    print(f"[generate_recommendation_report] Starting report generation")
    print(f"[generate_recommendation_report] Analysis: {analysis}")
    
    services = services or []
    dependencies = dependencies or []
    graph = graph or {}
    vulnerabilities = vulnerabilities or []
    chains = chains or []

    # Flatten vulnerabilities if they come as a dict organized by level
    if isinstance(vulnerabilities, dict):
        flat_vulns = []
        for level_key, level_data in vulnerabilities.items():
            if isinstance(level_data, dict):
                # Extract vulnerabilities from nested structure
                level_vulns = level_data.get("vulnerabilities", [])
                if level_vulns:
                    flat_vulns.extend(level_vulns)
        vulnerabilities = flat_vulns

    graph_nodes = graph.get("nodes", [])
    if not vulnerabilities:
        for node in graph_nodes:
            data = None
            if isinstance(node, dict):
                data = node.get("data")
            if isinstance(data, dict):
                vulns = data.get("vulns", [])
                if vulns:
                    vulnerabilities.extend(vulns)

    if not chains:
        for node in graph_nodes:
            data = node.get("data") if isinstance(node, dict) else node
            if data:
                chains.extend(data.get("chains", []))

    severity_counts = {}
    for vuln in vulnerabilities:
        if not isinstance(vuln, dict):
            continue
        severity = vuln.get("severity", "UNKNOWN")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    lines = []
    lines.append("Chaos Monkey Vulnerability Report")
    lines.append("=")
    lines.append("")
    lines.append(f"Modules scanned: {len(services)}")
    lines.append(f"Dependencies analyzed: {len(dependencies)}")
    lines.append(f"Detected vulnerabilities: {len(vulnerabilities)}")
    lines.append(f"Attack chains found: {len(chains)}")
    lines.append("")

    lines.append("Summary")
    lines.append("-------")
    if severity_counts:
        lines.append(
            "Severity breakdown: " + ", ".join(
                f"{severity}={count}" for severity, count in severity_counts.items()
            )
        )
    else:
        lines.append("No engine-level vulnerabilities were detected.")

    if analysis.get("cycles"):
        lines.append(f"Found circular dependency pairs: {len(analysis.get('cycles', []))}")
    if analysis.get("hotspots"):
        lines.append(f"High-risk hotspots: {len(analysis.get('hotspots', []))}")
    if not severity_counts and not chains:
        lines.append("The codebase appears to have low detectable risk from the current scanners.")
    lines.append("")

    lines.append("Causes")
    lines.append("------")
    if vulnerabilities:
        kinds = {}
        for vuln in vulnerabilities:
            if not isinstance(vuln, dict):
                continue
            kind = vuln.get("kind") or vuln.get("engine") or "UNKNOWN"
            kinds.setdefault(kind, 0)
            kinds[kind] += 1

        for kind, count in sorted(kinds.items(), key=lambda x: -x[1]):
            if "PATH_TRAVERSAL" in kind or "path" in kind.lower():
                lines.append(
                    f"- {count} findings indicate unsafe file path handling or concatenation, which can allow an attacker to traverse directories or access unintended files."
                )
            elif "WEAK_CRYPTO" in kind or "crypto" in kind.lower():
                lines.append(
                    f"- {count} findings indicate weak cryptography, which can cause compromised integrity or authentication failures."
                )
            elif "ATTACK_CHAIN" in kind or "chain" in kind.lower():
                lines.append(
                    f"- {count} findings describe propagated attack chains where a failure in one component can impact downstream services."
                )
            else:
                lines.append(f"- {count} findings of type {kind} require code review for root cause and remediation.")
    else:
        lines.append("- No direct vulnerability causes were identified by the current scanners.")
    lines.append("")

    lines.append("Effects")
    lines.append("-------")
    if vulnerabilities:
        high_vulns = [v for v in vulnerabilities if v.get("severity") in ("HIGH", "CRITICAL")]
        if high_vulns:
            lines.append(
                f"- {len(high_vulns)} high-severity issues can lead to direct exploitation, data loss, or unauthorized access."
            )
        if chains:
            lines.append(
                "- Attack chains may allow an initial compromise to cascade across multiple modules, increasing blast radius."
            )
        else:
            lines.append(
                "- Without chain propagation, most findings are localized to individual modules, but still deserve prompt remediation."
            )
    else:
        lines.append("- No exploitable effects were identified based on current vulnerability data.")
    lines.append("")

    lines.append("Safeguards")
    lines.append("----------")
    if vulnerabilities:
        if any("PATH_TRAVERSAL" in (v.get("kind") or "") or "path" in (v.get("kind") or "").lower() for v in vulnerabilities):
            lines.append("- Validate and normalize all file system inputs. Use safe root directories and reject unexpected path separators.")
        if any("WEAK_CRYPTO" in (v.get("kind") or "") or "crypto" in (v.get("kind") or "").lower() for v in vulnerabilities):
            lines.append("- Replace weak hashing and encryption primitives with modern alternatives, e.g. SHA-256, AES-GCM, or built-in secure frameworks.")
        if any("ATTACK_CHAIN" in (v.get("kind") or "") or "chain" in (v.get("kind") or "").lower() for v in vulnerabilities):
            lines.append("- Add isolation barriers, input validation, and failure handling between chained services to prevent propagation.")
        if any(v.get("severity") == "MEDIUM" for v in vulnerabilities):
            lines.append("- Review medium-severity findings for secure defaults and validate assumptions around inputs and dependencies.")
        if any(v.get("severity") == "LOW" for v in vulnerabilities):
            lines.append("- Track low-severity issues as technical debt and remediate them during regular maintenance cycles.")
    else:
        lines.append("- Keep current secure coding practices and rerun analysis after new changes.")

    if analysis.get("cycles"):
        lines.append("- Resolve circular dependencies by refactoring shared responsibilities into stable abstractions.")
    if analysis.get("hotspots"):
        lines.append("- Limit the number of modules depending on a single hotspot to reduce risk concentration.")

    lines.append("")
    lines.append("Detailed Findings")
    lines.append("----------------")
    for vuln in vulnerabilities[:20]:
        file = vuln.get("file") or vuln.get("id") or "unknown"
        message = vuln.get("message") or vuln.get("detail") or "No description available."
        severity = vuln.get("severity") or "UNKNOWN"
        lines.append(f"- {file} [{severity}] - {message}")

    if chains:
        lines.append("")
        lines.append("Attack Chains")
        lines.append("-------------")
        for chain in chains[:10]:
            kind = chain.get("kind") or chain.get("engine") or "unknown"
            detail = chain.get("detail") or ", ".join(chain.get("chain", []))
            score = chain.get("score")
            lines.append(f"- {kind} chain: {detail} (score={score})")

    final_report = "\n".join(lines)
    model_path = get_local_model_path()
    print(f"[generate_recommendation_report] Model path: {model_path}")
    
    if model_path:
        max_tokens, _ = get_report_generation_settings()
        print(f"[generate_recommendation_report] Attempting to generate agentic report with LLM using max_tokens={max_tokens}")
        prompt = build_report_prompt(services, dependencies, vulnerabilities, chains, analysis)
        ai_text = generate_report_with_local_model(prompt, model_path, max_tokens=max_tokens)
        if ai_text:
            print(f"[generate_recommendation_report] LLM report generated successfully (length={len(ai_text)})")
            return ai_text
        else:
            print(f"[generate_recommendation_report] LLM report generation failed, falling back to template")
    else:
        print(f"[generate_recommendation_report] No model path found, using template report")

    return final_report
