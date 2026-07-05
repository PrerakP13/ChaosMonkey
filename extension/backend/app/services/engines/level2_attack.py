RISKY = {
    "subprocess": "Potential command injection risk.",
    "os": "os.system / os.popen can be unsafe.",
    "pickle": "pickle is unsafe with untrusted input.",
    "hashlib": "Check for weak hashes (MD5/SHA1).",
    "random": "random is not cryptographically secure.",
}

def run_level2(services, dependencies):
    """
    Level 2 — Static Attack Surface
    Flags modules that import risky libraries.
    Also identifies services with no imports and services with only safe imports.
    """
    vulns = []
    risky_services = set()
    imported_any = set()

    for src, target in dependencies:
        imported_any.add(src)

        if not isinstance(target, str):
            continue

        base = target.split(".")[0]

        if base in RISKY:
            risky_services.add(src)
            vulns.append({
                "service": src,
                "issue": f"Risky import detected: {base}",
                "detail": RISKY[base],
            })

    # Services that import nothing
    no_imports = [s for s in services if s not in imported_any]

    # Services that import only safe modules
    safe_services = [s for s in services if s not in risky_services]

    return {
        "vulnerabilities": vulns,
        "no_imports": no_imports,
        "safe_services": safe_services,
    }

