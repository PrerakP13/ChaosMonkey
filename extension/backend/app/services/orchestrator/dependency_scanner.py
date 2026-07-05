import ast
import os
from collections import defaultdict
from typing import Dict, List, Tuple, Set


# ---------------------------------------------------------
# 1. Discover all Python files in the project and skip environment folders/files
# ---------------------------------------------------------
def discover_python_files(root_path: str) -> Set[str]:
    files = set()

    for dirpath, dirs, filenames in os.walk(root_path):

        # Skip unwanted directories
        skip_dirs = {
            ".venv",
            "venv",
            "__pycache__",
            ".env",
        }

        # Remove directories we don't want os.walk to enter
        dirs[:] = [
            d for d in dirs
            if d not in skip_dirs
            and not d.startswith(".env")   # .env.local, .env.dev, etc.
            and not d.startswith(".")      # ANY hidden folder
        ]

        # Collect Python files
        for name in filenames:
            if name.endswith(".py"):
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, root_path).replace("\\", "/")
                files.add(rel)

    return files



# ---------------------------------------------------------
# 2. Resolve an import to an actual file in the project
# ---------------------------------------------------------
def resolve_import_to_file(mod: str, project_files: Set[str]) -> str | None:
    """
    Resolve imports like:
      - app.services.graph_builder
      - backend.app.services.graph_builder
      - app.services
      - app.services.graph_builder.Engine
    """

    # Strip "backend." prefix
    if mod.startswith("backend."):
        mod = mod[len("backend."):]

    # Remove trailing attribute (e.g., ".Engine")
    parts = mod.split(".")
    while parts:
        candidate = "/".join(parts) + ".py"
        if candidate in project_files:
            return candidate

        candidate = "/".join(parts) + "/__init__.py"
        if candidate in project_files:
            return candidate

        parts.pop()  # Try parent module

    return None


# ---------------------------------------------------------
# 3. Resolve relative imports
# ---------------------------------------------------------
def resolve_relative_import(
    current_file: str, level: int, module: str | None, project_files: Set[str]
) -> str | None:
    """
    Handles:
      from . import x
      from ..services import y
      from ...engines.level1_static import Engine
    """

    # Convert current file to module path
    parts = current_file.split("/")[:-1]  # remove filename

    # Move up "level" directories
    if level > 0:
        parts = parts[: -level]

    # If module is provided, append it
    if module:
        parts += module.split(".")

    mod = ".".join(parts)
    return resolve_import_to_file(mod, project_files)


# ---------------------------------------------------------
# 4. Extract dependencies from Python files
# ---------------------------------------------------------
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

            # -----------------------------
            # import x, y as z
            # -----------------------------
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name
                    resolved = resolve_import_to_file(mod, project_files)
                    if resolved:
                        graph[file].append(resolved)

            # -----------------------------
            # from x import y
            # from x.y import z
            # from . import y
            # from ..services import z
            # from x import *
            # -----------------------------
            elif isinstance(node, ast.ImportFrom):

                # Handle relative imports
                if node.level > 0:
                    resolved = resolve_relative_import(
                        current_file=file,
                        level=node.level,
                        module=node.module,
                        project_files=project_files,
                    )
                    if resolved:
                        graph[file].append(resolved)
                    continue

                # Handle absolute imports
                if node.module:
                    mod = node.module
                    resolved = resolve_import_to_file(mod, project_files)
                    if resolved:
                        graph[file].append(resolved)

    return graph


# ---------------------------------------------------------
# 5. Normalize to edge list
# ---------------------------------------------------------
def normalize_dependency_graph(
    deps: Dict[str, List[str]]
) -> List[Tuple[str, str]]:
    edges: List[Tuple[str, str]] = []
    for src, targets in deps.items():
        for tgt in targets:
            edges.append((src, tgt))
    return edges
