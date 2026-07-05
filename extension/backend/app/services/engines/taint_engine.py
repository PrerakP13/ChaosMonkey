import ast, os
from typing import Dict, Set, List, Any
from app.helpers.helper import make_vuln


TAINT_SOURCES = {"input"}
TAINT_SINKS = {
    ("os", "system"): "COMMAND_INJECTION",
    ("subprocess", "Popen"): "COMMAND_INJECTION",
    ("cursor", "execute"): "SQL_INJECTION",  # heuristic
}


class TaintTracker(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.tainted_vars: Set[str] = set()
        self.findings: List[Dict[str, Any]] = []

    def taint(self, name: str):
        self.tainted_vars.add(name)

    def is_tainted(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id in self.tainted_vars
        if isinstance(node, ast.BinOp):
            return self.is_tainted(node.left) or self.is_tainted(node.right)
        if isinstance(node, ast.Call):
            return any(self.is_tainted(a) for a in node.args)
        if isinstance(node, ast.Attribute):
            return self.is_tainted(node.value)
        return False

    def visit_Assign(self, node: ast.Assign):
        # x = input()
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            if node.value.func.id in TAINT_SOURCES:
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        self.taint(t.id)
        # simple propagation: x = y
        if isinstance(node.value, ast.Name) and node.value.id in self.tainted_vars:
            for t in node.targets:
                if isinstance(t, ast.Name):
                    self.taint(t.id)

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # sink detection
        if isinstance(node.func, ast.Attribute):
            base = getattr(node.func.value, "id", None)
            attr = node.func.attr
            if base and (base, attr) in TAINT_SINKS:
                if any(self.is_tainted(a) for a in node.args):
                    kind = TAINT_SINKS[(base, attr)]
                    self.findings.append(
                        make_vuln(
                            file=self.filename,
                            line=getattr(node, "lineno", None),
                            engine="taint",
                            kind=f"TAINTED_{kind}",
                            severity="CRITICAL",
                            message=f"Tainted data flows into {base}.{attr} ({kind}).",
                        )
                    )
        self.generic_visit(node)


def run_taint_engine(root_path: str, services: List[str]) -> Dict[str, Any]:
    all_findings: List[Dict[str, Any]] = []

    for rel in services:
        full = os.path.join(root_path, rel)
        try:
            source = open(full, "r", encoding="utf-8").read()
            tree = ast.parse(source, filename=rel)
        except Exception:
            continue

        tracker = TaintTracker(rel)
        tracker.visit(tree)
        all_findings.extend(tracker.findings)

    return {"vulnerabilities": all_findings}
