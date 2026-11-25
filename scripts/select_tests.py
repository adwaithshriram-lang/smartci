#!/usr/bin/env python3
"""Select pytest files affected by the latest source-code changes.

The selector uses Python's AST (no third-party dependency) to build an import
map, then follows reverse dependencies so changes to a module also select tests
for modules that depend on it. If diff detection is uncertain, it runs all tests.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TESTS = ROOT / "tests"


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def all_tests() -> list[str]:
    files = sorted(p.relative_to(ROOT).as_posix() for p in TESTS.glob("test_*.py"))
    return files or ["tests"]


def module_name(path: Path) -> str | None:
    try:
        relative = path.relative_to(ROOT).with_suffix("")
    except ValueError:
        return None
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts) if parts else None


def resolve_imports(path: Path) -> set[str]:
    """Return absolute module names imported by a Python file."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()

    current = module_name(path) or ""
    package = current.rpartition(".")[0]
    found: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                package_parts = package.split(".") if package else []
                keep = max(0, len(package_parts) - (node.level - 1))
                prefix = package_parts[:keep]
                base = ".".join(prefix + ([base] if base else []))
            if base:
                found.add(base)
                for alias in node.names:
                    if alias.name != "*":
                        found.add(f"{base}.{alias.name}")

    return found


def changed_files() -> list[str]:
    base = os.environ.get("BASE_SHA", "").strip()
    if not base and os.environ.get("GITHUB_BASE_REF"):
        base = f"origin/{os.environ['GITHUB_BASE_REF']}"

    if base and set(base) == {"0"}:
        raise RuntimeError("The push event has no previous commit to compare.")

    if base:
        return [p for p in git_output("diff", "--name-only", f"{base}..HEAD").splitlines() if p]
    # Local demonstration: compare the latest commit with its parent.
    return [p for p in git_output("diff", "--name-only", "HEAD~1", "HEAD").splitlines() if p]


def select_tests() -> list[str]:
    try:
        changed = changed_files()
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"[selector] Could not determine Git diff ({exc}); running all tests.", file=sys.stderr)
        return all_tests()

    changed_src = [
        p for p in changed
        if p.startswith("src/") and p.endswith(".py") and (ROOT / p).is_file()
    ]
    if not changed_src:
        print("[selector] No changed Python source files; running all tests.", file=sys.stderr)
        return all_tests()

    source_files = sorted(SRC.rglob("*.py"))
    source_imports = {
        module_name(path): resolve_imports(path)
        for path in source_files
        if module_name(path)
    }

    # Build reverse edges: if module A imports B, changing B can affect A.
    reverse_dependencies: dict[str, set[str]] = {}
    for module, imports in source_imports.items():
        for imported in imports:
            if imported in source_imports:
                reverse_dependencies.setdefault(imported, set()).add(module)

    impacted: set[str] = set()
    for path in changed_src:
        name = module_name(ROOT / path)
        if name:
            impacted.add(name)

    pending = list(impacted)
    while pending:
        current = pending.pop()
        for dependent in reverse_dependencies.get(current, set()):
            if dependent not in impacted:
                impacted.add(dependent)
                pending.append(dependent)

    selected: list[str] = []
    for test_file in sorted(TESTS.glob("test_*.py")):
        imports = resolve_imports(test_file)
        if any(
            imported == module or imported.startswith(module + ".")
            for imported in imports
            for module in impacted
        ):
            selected.append(test_file.relative_to(ROOT).as_posix())

    if not selected:
        print("[selector] No test mapping found; running all tests for safety.", file=sys.stderr)
        return all_tests()

    print(f"[selector] Changed source: {', '.join(changed_src)}", file=sys.stderr)
    print(f"[selector] Impacted modules: {', '.join(sorted(impacted))}", file=sys.stderr)
    print(f"[selector] Selected {len(selected)} of {len(all_tests())} test files.", file=sys.stderr)
    return selected


if __name__ == "__main__":
    print(" ".join(select_tests()))
