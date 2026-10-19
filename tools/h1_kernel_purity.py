"""AST-only domain-purity and transitive import boundary audit.

The starting vocabulary is a permanent floor, not a source-code allowlist.
Only real module/class/function docstrings are exempt from string scanning.
"""
from __future__ import annotations

import ast
from collections import deque
from pathlib import Path
import re


KERNEL_ROOTS = frozenset("predicates construction numeric_domain rational3 dual lp margin limit limit_multi oracle_construction kernel2d kernel3d".split())
DOMAIN_WORDS = frozenset("dda bdda tia tf rock joint mtype df04 df05 df06 df07 legacy zsto lock_second bolt m4 m6 csv slot tuple7 岩石 节理 岩体 围岩 断层 岩爆".split())
FORBIDDEN_PACKAGES = ("eab.adapters", "eab.readers")
SHARED_MODULES = frozenset(("eab", "eab.contact_record", "eab.numeric_decode"))
DOMAIN_ACRONYMS = frozenset("dda bdda tia csv zsto df04 df05 df06 df07".split())
# These ordinary mathematical words contain the acronym 'tia' accidentally.
# Whole components only: appending a domain acronym is never exempted.
ORDINARY_COMPONENTS = frozenset("initial partial potential spatial tangential exponential differential differentiability".split())
LEXICAL_ALLOWLIST = {
    ("eab.contact_record", "joint_material"): "Existing serialized material identity field, not an engine code or table slot.",
    ("*", "slots"): "Only the dataclass(slots=...) language keyword; never a variable or string.",
}


def words(value):
    """Retain alphanumerics; detect plurals, split spellings and acronyms."""
    unsplit = set(re.findall(r"[a-z][a-z0-9]*", value.lower()))
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    result = unsplit | set(re.findall(r"[a-z][a-z0-9]*", value.lower()))
    for component in tuple(result):
        if component.endswith("s"):
            result.add(component[:-1])
        if component.endswith("ies"):
            result.add(component[:-3] + "y")
        if component not in ORDINARY_COMPONENTS:
            result.update(word for word in DOMAIN_ACRONYMS if word in component)
        if component.startswith("tf"):
            result.add("tf")
    compact = value.lower().replace("_", "")
    if "mtype" in compact:
        result.add("mtype")
    if "locksecond" in compact:
        result.add("lock_second")
    return result | {word for word in DOMAIN_WORDS if not word.isascii() and word in value}


def _docstrings(tree):
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr):
                value = node.body[0].value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    found.add(id(value))
    return found


def _identifiers(node):
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        return (node.attr,)
    if isinstance(node, ast.arg):
        return (node.arg,)
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return (node.name,)
    if isinstance(node, ast.alias):
        return (node.name, node.asname or "")
    if isinstance(node, ast.ImportFrom):
        return (node.module or "",)
    if isinstance(node, ast.keyword):
        return (node.arg or "",)
    if isinstance(node, (ast.Global, ast.Nonlocal)):
        return node.names
    if isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)):
        return (node.name or "",)
    if isinstance(node, ast.MatchMapping):
        return (node.rest or "",)
    if isinstance(node, ast.MatchClass):
        return node.kwd_attrs
    return ()


def _literal_text(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _literal_text(node.left), _literal_text(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _allowed(module, node, value, parents):
    if module == "eab.contact_record" and value == "joint_material":
        parent = parents.get(node)
        if isinstance(node, ast.Name) and isinstance(parent, ast.AnnAssign) and parent.target is node:
            owner = parents.get(parent)
            return isinstance(owner, ast.ClassDef) and owner.name == "ContactRecord"
        if isinstance(node, ast.Constant) and isinstance(parent, ast.Set):
            owner = parents.get(parent)
            return isinstance(owner, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_INTEGER_FIELDS" for t in owner.targets)
    if isinstance(node, ast.keyword) and value == "slots":
        parent = parents.get(node)
        return isinstance(parent, ast.Call) and isinstance(parent.func, ast.Name) and parent.func.id == "dataclass"
    return False


def _imports(tree, module, is_package, modules):
    result = set()
    package = module if is_package else module.rpartition(".")[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")[:len(package.split("."))-node.level+1]
                absolute = ".".join(base + ([node.module] if node.module else []))
            else:
                absolute = node.module or ""
            result.add(absolute)
            for alias in node.names:
                child = absolute + "." + alias.name
                if child in modules or any(child == p or child.startswith(p+".") for p in FORBIDDEN_PACKAGES):
                    result.add(child)
        elif isinstance(node, ast.Call):
            # Literal dynamic imports are also part of the AST import graph.
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if name in ("__import__", "import_module") and node.args:
                first = _literal_text(node.args[0])
                if first is not None:
                    result.add(first)
        elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute):
            if isinstance(node.value.value, ast.Name) and node.value.value.id == "sys" and node.value.attr == "modules":
                name = _literal_text(node.slice)
                if name is not None:
                    result.add(name)
    # Importing a submodule executes each parent package's __init__ as well.
    for name in tuple(result):
        parts = name.split(".")
        result.update(".".join(parts[:i]) for i in range(1, len(parts)))
    return {name for name in result if name == "eab" or name.startswith("eab.")}


def audit_kernel(source_root):
    """Return deterministic violations; source_root contains the eab package."""
    source_root = Path(source_root)
    paths = sorted((source_root / "eab").rglob("*.py"))
    modules = {}
    for path in paths:
        module = ".".join(path.relative_to(source_root).with_suffix("").parts)
        is_package = path.name == "__init__.py"
        if is_package:
            module = module.removesuffix(".__init__")
        modules[module] = (path, ast.parse(path.read_text(encoding="utf-8-sig")), is_package)
    graph = {name: _imports(tree, name, package, modules)
             for name, (_, tree, package) in modules.items()}
    violations = []
    for module, (path, tree, _) in sorted(modules.items()):
        is_kernel = bool(module.split(".")[1:2] and module.split(".")[1] in KERNEL_ROOTS)
        if is_kernel or module in SHARED_MODULES:
            relative = path.relative_to(source_root).as_posix()
            docstrings = _docstrings(tree)
            parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
            forbidden = sorted(DOMAIN_WORDS & words(module))
            if forbidden:
                violations.append(f"{relative}:0: domain module token {','.join(forbidden)}")
            for node in ast.walk(tree):
                values = list(_identifiers(node))
                if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)) and id(node) not in docstrings:
                    values.append(node.value.decode("utf-8", errors="replace") if isinstance(node.value, bytes) else node.value)
                for value in values:
                    forbidden = sorted(DOMAIN_WORDS & words(value))
                    if forbidden and not _allowed(module, node, value, parents):
                        violations.append(f"{relative}:{node.lineno}: domain token {','.join(forbidden)}")
        if is_kernel:
            # Even an import-free leaf executes its own package parents.
            parts = module.split(".")
            pending = deque([(module, (module,))] +
                            [(".".join(parts[:i]), (module, ".".join(parts[:i]))) for i in range(1, len(parts))])
            visited = set()
            while pending:
                current, trail = pending.popleft()
                if current in visited:
                    continue
                visited.add(current)
                for target in sorted(graph.get(current, ())):
                    chain = (*trail, target)
                    if any(target == p or target.startswith(p+".") for p in FORBIDDEN_PACKAGES):
                        violations.append(f"{relative}: forbidden import path {' -> '.join(chain)}")
                    elif target not in visited:
                        pending.append((target, chain))
    return sorted(set(violations))


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1] / "src")
    args = parser.parse_args()
    violations = audit_kernel(args.source_root)
    for line in violations:
        print(line)
    print(f"kernel purity: {len(violations)} violations")
    return bool(violations)


if __name__ == "__main__":
    raise SystemExit(main())
