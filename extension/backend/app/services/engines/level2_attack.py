import ast
import os
from typing import List, Dict, Any
from app.helpers.helper import make_vuln
from app.services.engines.taint_engine import run_taint_engine

class BaseDetector(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.findings: List[Dict[str, Any]] = []

    # Default severity mapping
    SEVERITY_MAP = {
        "SQL_INJECTION": "HIGH",
        "COMMAND_INJECTION": "CRITICAL",
        "PATH_TRAVERSAL": "MEDIUM",
        "WEAK_CRYPTO": "LOW",
        "INSECURE_RANDOM": "LOW",
        "INSECURE_DESERIALIZATION": "HIGH",
        "HARDCODED_SECRET": "HIGH",
        "DANGEROUS_FUNCTION": "HIGH",
        "INSECURE_HTTP": "MEDIUM",
        "XSS": "HIGH",
    }

    def add(self, node: ast.AST, kind: str, message: str, detail: str = "", meta=None):
        severity = self.SEVERITY_MAP.get(kind, "MEDIUM")

        self.findings.append(
            make_vuln(
                file=self.filename,
                line=getattr(node, "lineno", None),
                engine="level2",
                kind=kind,
                message=message,
                detail=detail,
                severity=severity,      # REQUIRED
                meta=meta or {},
            )
        )




class SQLInjectionDetector(BaseDetector):
    SQL_FUNCS = {"execute", "executemany", "raw"}

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute) and node.func.attr in self.SQL_FUNCS:
            if not node.args:
                return
            q = node.args[0]
            if isinstance(q, ast.BinOp) and isinstance(q.op, ast.Add):
                self.add(node, "SQL_INJECTION", "SQL via string concatenation.")
            elif isinstance(q, ast.JoinedStr):
                self.add(node, "SQL_INJECTION", "SQL via f-string.")
            elif isinstance(q, ast.BinOp) and isinstance(q.op, ast.Mod):
                self.add(node, "SQL_INJECTION", "SQL via %-formatting.")
            elif isinstance(q, ast.Call) and isinstance(q.func, ast.Attribute) and q.func.attr == "format":
                self.add(node, "SQL_INJECTION", "SQL via .format().")
        self.generic_visit(node)


class CommandInjectionDetector(BaseDetector):
    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("system", "popen"):
            self.add(node, "COMMAND_INJECTION", "os.system/os.popen call.")
        if isinstance(node.func, ast.Attribute) and getattr(node.func.value, "id", "") == "subprocess":
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.add(node, "COMMAND_INJECTION", "subprocess with shell=True.")
        self.generic_visit(node)


class PathTraversalDetector(BaseDetector):
    FILE_FUNCS = {"open", "unlink", "remove", "rmdir"}

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in self.FILE_FUNCS:
            if node.args:
                self.add(node, "PATH_TRAVERSAL", "File operation on dynamic path.", meta={"func": node.func.id})
        if isinstance(node.func, ast.Attribute) and node.func.attr == "join":
            if getattr(node.func.value, "attr", None) == "path":
                self.add(node, "PATH_TRAVERSAL", "Path built via os.path.join; validate input.")
        self.generic_visit(node)


class WeakCryptoDetector(BaseDetector):
    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute) and getattr(node.func.value, "id", "") == "hashlib":
            if node.func.attr in ("md5", "sha1"):
                self.add(node, "WEAK_CRYPTO", f"Weak hash {node.func.attr} used.")
        self.generic_visit(node)


class InsecureRandomDetector(BaseDetector):
    def visit_Attribute(self, node: ast.Attribute):
        if getattr(node.value, "id", "") == "random":
            self.add(node, "INSECURE_RANDOM", "random module used; not crypto secure.")
        self.generic_visit(node)


class InsecureDeserializationDetector(BaseDetector):
    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute) and getattr(node.func.value, "id", "") == "pickle":
            if node.func.attr in ("load", "loads"):
                self.add(node, "INSECURE_DESERIALIZATION", "pickle.load/loads used.")
        if isinstance(node.func, ast.Attribute) and getattr(node.func.value, "id", "") == "yaml":
            if node.func.attr == "load":
                self.add(node, "INSECURE_DESERIALIZATION", "yaml.load used; prefer safe_load.")
        self.generic_visit(node)


class HardcodedSecretsDetector(BaseDetector):
    SECRET_KEYS = ("API_KEY", "SECRET", "TOKEN", "PASSWORD", "KEY")

    def visit_Assign(self, node: ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                name = t.id.upper()
                if any(k in name for k in self.SECRET_KEYS):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        self.add(node, "HARDCODED_SECRET", f"Hardcoded secret in {t.id}.")
        self.generic_visit(node)


class DangerousFunctionsDetector(BaseDetector):
    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
            self.add(node, "DANGEROUS_FUNCTION", f"Use of {node.func.id}.")
        self.generic_visit(node)


class InsecureHTTPDetector(BaseDetector):
    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute) and getattr(node.func.value, "id", "") == "requests":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                url = node.args[0].value
                if url.startswith("http://"):
                    self.add(node, "INSECURE_HTTP", "HTTP used instead of HTTPS.", meta={"url": url})
        self.generic_visit(node)


class XSSDetector(BaseDetector):
    # function/attribute names that typically render HTML
    HTML_FUNCS = {"HTMLResponse", "render_template", "render", "Response", "make_response"}

    def visit_Call(self, node: ast.Call):
        # 1) Simple name calls: render_template(...), render(...), HTMLResponse(...)
        if isinstance(node.func, ast.Name):
            name = node.func.id

            # Flask / generic: render_template("tpl.html", user=user_input)
            if name == "render_template":
                self._handle_flask_render_template(node)

            # Django: render(request, "tpl.html", context={...})
            elif name == "render":
                self._handle_django_render(node)

            # FastAPI / Starlette / generic: HTMLResponse(...), Response(...)
            elif name in ("HTMLResponse", "Response", "make_response"):
                self._handle_html_response(node)

        # 2) Attribute calls: fastapi.responses.HTMLResponse(...), flask.make_response(...)
        elif isinstance(node.func, ast.Attribute):
            attr = node.func.attr

            if attr in ("HTMLResponse", "Response"):
                self._handle_html_response(node)

            if attr in ("render_template", "make_response"):
                self._handle_flask_like(node)

        self.generic_visit(node)

    # ---------- helpers ----------

    def _looks_dynamic(self, node: ast.AST) -> bool:
        # heuristic: anything non-constant is "dynamic"
        if isinstance(node, ast.Constant):
            return False
        if isinstance(node, (ast.JoinedStr, ast.Name, ast.BinOp, ast.Call, ast.Dict, ast.List, ast.Tuple)):
            return True
        return False

    def _handle_html_response(self, node: ast.Call):
        # FastAPI / Starlette / generic HTMLResponse(content=...)
        for kw in node.keywords:
            if kw.arg in ("content", "body", "html") and self._looks_dynamic(kw.value):
                self.add(
                    node,
                    "XSS",
                    "Dynamic content rendered into HTML response.",
                    detail=f"Argument '{kw.arg}' appears dynamic.",
                )

        # positional first arg as body/content
        if node.args:
            if self._looks_dynamic(node.args[0]):
                self.add(
                    node,
                    "XSS",
                    "Dynamic content rendered into HTML response (positional arg).",
                )

    def _handle_flask_render_template(self, node: ast.Call):
        # render_template("tpl.html", user=user_input)
        for kw in node.keywords:
            if self._looks_dynamic(kw.value):
                self.add(
                    node,
                    "XSS",
                    f"Potential XSS via template variable '{kw.arg}' in render_template.",
                )

    def _handle_flask_like(self, node: ast.Call):
        # flask.make_response(html), flask.Response(html)
        if node.args and self._looks_dynamic(node.args[0]):
            self.add(
                node,
                "XSS",
                "Dynamic HTML passed to response constructor.",
            )

    def _handle_django_render(self, node: ast.Call):
        # render(request, template_name, context={...})
        # context may be 3rd positional or 'context=' kw
        # positional context
        if len(node.args) >= 3 and self._looks_dynamic(node.args[2]):
            self.add(
                node,
                "XSS",
                "Dynamic context passed to Django render().",
            )

        # keyword context
        for kw in node.keywords:
            if kw.arg == "context" and self._looks_dynamic(kw.value):
                self.add(
                    node,
                    "XSS",
                    "Dynamic context passed to Django render(context=...).",
                )

# -----------------------------------------
# DETECTOR REGISTRY (put this AFTER classes)
# -----------------------------------------

DETECTORS = [
    SQLInjectionDetector,
    CommandInjectionDetector,
    PathTraversalDetector,
    WeakCryptoDetector,
    InsecureRandomDetector,
    InsecureDeserializationDetector,
    HardcodedSecretsDetector,
    DangerousFunctionsDetector,
    InsecureHTTPDetector,
    XSSDetector,
    # RiskyImportDetector  ← add here when ready
]

# -----------------------------------------
# LEVEL 2 ORCHESTRATOR
# -----------------------------------------

def run_level2(root_path: str, services: List[str], dependencies) -> Dict[str, Any]:
    all_findings: List[Dict[str, Any]] = []

    # run all pattern-based detectors
    for rel in services:
        full = os.path.join(root_path, rel)
        try:
            src = open(full, "r", encoding="utf-8").read()
            tree = ast.parse(src, filename=rel)
        except Exception:
            continue

        for Detector in DETECTORS:
            d = Detector(rel)
            d.visit(tree)
            all_findings.extend(d.findings)

    # run taint engine (imported from taint_engine.py)
    taint_results = run_taint_engine(root_path, services)
    all_findings.extend(taint_results.get("vulnerabilities", []))

    return {"vulnerabilities": all_findings}
