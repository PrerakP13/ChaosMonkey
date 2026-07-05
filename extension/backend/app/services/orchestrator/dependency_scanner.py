import ast
import os
from collections import defaultdict
from typing import Dict, List, Tuple, Set


def discover_python_files(root_path: str) -> Set[str]:
    files = set()

    for dirpath, dirs, filenames in os.walk(root_path):
        skip_dirs = {".venv", "venv", "__pycache__", ".env", "tests", "test", ".git", "node_modules"}

        dirs[:] = [
            d for d in dirs
            if d not in skip_dirs
            and not d.startswith(".env")
            and not d.startswith(".")
        ]

        for name in filenames:
            # Skip test files, __init__.py, and setup files
            if name.endswith(".py") and name != "__init__.py":
                # Filter out test files
                if name.startswith("test_") or name.endswith("_test.py") or name in ("setup.py", "conftest.py"):
                    continue
                    
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, root_path).replace("\\", "/")
                files.add(rel)

    return files


def resolve_import_to_file(mod: str, project_files: Set[str]) -> str | None:


    parts = mod.split(".")
    while parts:
        candidate = "/".join(parts) + ".py"
        if candidate in project_files:
            return candidate

        candidate = "/".join(parts) + "/__init__.py"
        if candidate in project_files:
            return candidate

        parts.pop()

    return None


def resolve_relative_import(
    current_file: str, level: int, module: str | None, project_files: Set[str]
) -> str | None:
    """
    Resolve relative imports like:
        from . import x
        from .module import y
        from ..subpkg import z
    """

    # Split current file path into parts
    parts = current_file.split("/")[:-1]  # directory of current file

    # Move up directories based on "level"
    if level > 0:
        parts = parts[: -level] if level <= len(parts) else []

    # Case 1: from .module import x
    if module:
        mod = ".".join(parts + module.split("."))
        return resolve_import_to_file(mod, project_files)

    # Case 2: from . import x   (module=None)
    # node.names contains the imported names
    return None



def extract_dependencies(root_path: str) -> Dict[str, List[str]]:
    project_files = discover_python_files(root_path)
    graph: Dict[str, List[str]] = defaultdict(list)

    for file in project_files:
        full_path = os.path.join(root_path, file)

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=file)
        except Exception:
            continue

        for node in ast.walk(tree):

            # -------------------------------
            # import x, import x.y
            # -------------------------------
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name
                    resolved = resolve_import_to_file(mod, project_files)
                    if resolved and resolved not in graph[file]:
                        graph[file].append(resolved)

            # -------------------------------
            # from ... import ...
            # -------------------------------
            elif isinstance(node, ast.ImportFrom):

                # -------- relative imports --------
                if node.level > 0:

                    # Case 1: from .module import x
                    if node.module is not None:
                        resolved = resolve_relative_import(
                            current_file=file,
                            level=node.level,
                            module=node.module,
                            project_files=project_files,
                        )
                        if (
                            resolved
                            and isinstance(resolved, str)
                            and resolved in project_files
                            and resolved != file
                            and resolved not in graph[file]
                        ):
                            graph[file].append(resolved)


                    # Case 2: from . import x
                    else:
                        for alias in node.names:
                            mod = alias.name
                            resolved = resolve_relative_import(
                                current_file=file,
                                level=node.level,
                                module=mod,
                                project_files=project_files,
                            )
                            if resolved and resolved not in graph[file]:
                                graph[file].append(resolved)

                    continue

                # -------- absolute imports --------
                if node.module:
                    mod = node.module
                    resolved = resolve_import_to_file(mod, project_files)
                    if resolved and resolved not in graph[file]:
                        graph[file].append(resolved)

    return graph



def normalize_dependency_graph(
    deps: Dict[str, List[str]]
) -> List[Tuple[str, str]]:
    edges: List[Tuple[str, str]] = []
    for src, targets in deps.items():
        for tgt in targets:
            if (
                isinstance(src, str)
                and isinstance(tgt, str)
                and src
                and tgt
                and src != tgt
            ):
                edges.append((src, tgt))
    return edges

