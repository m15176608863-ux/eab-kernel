"""Positive admission policy, separate from the rounding-provenance analysis.

This is an auxiliary code check over a small first-order Python subset, NOT a
safety guarantee or Python numeric proof. Runtime differential tests against
independent rational references are the primary construction guard. Unsupported
nodes/calls/escapes identified by this finite model are issues, including future
AST nodes; zero diagnostics does not prove arbitrary Python safe. Reviewed departures are exact, context-pinned sites in the manifest;
they do not turn a callable spelling or an entire function into a safe API.
The old provenance checks still run at admitted and waived sites.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
_flow_spec = importlib.util.spec_from_file_location("exact_construction_flow", HERE / "exact_construction_flow.py")
_flow = importlib.util.module_from_spec(_flow_spec)
_flow_spec.loader.exec_module(_flow)
analyze = _flow.analyze


# No runtime introspection of builtins to enlarge the policy on a new Python.
DIRECT = frozenset("abs all any bool dict enumerate filter float frozenset int isinstance issubclass len list max min next range repr reversed round set sorted str sum tuple type zip AssertionError ArithmeticError IndexError KeyError NotImplementedError OverflowError RuntimeError StopIteration TypeError ValueError ZeroDivisionError object super property staticmethod classmethod AttributeError FloatingPointError".split())
CONSTRUCTORS = frozenset("Fraction scalar_rational vector_rational ratio_rational sqrt_rational norm_rational unit_rational scalar_exact vector_exact ratio_exact sqrt_exact norm_exact unit_exact normalized_difference_rational scalar_algebraic _float_vector".split())
INTRINSICS = DIRECT | CONSTRUCTORS | frozenset("from_float values items get copy __getitem__".split())
FORBIDDEN = frozenset("map filter iter eval exec compile getattr setattr delattr hasattr globals locals vars dir __import__ callable breakpoint memoryview partial reduce".split())
NODE_NAMES = frozenset("Module FunctionDef arguments arg ClassDef Return Delete Assign AugAssign AnnAssign For While If With withitem Raise Try ExceptHandler Assert Import ImportFrom alias Expr Pass Break Continue BoolOp BinOp UnaryOp IfExp Dict Set ListComp SetComp DictComp GeneratorExp comprehension Compare Call FormattedValue Constant Attribute Subscript Starred Name List Tuple Slice Load Store Del And Or Add Sub Mult MatMult Div Mod Pow LShift RShift BitOr BitXor BitAnd FloorDiv Invert Not UAdd USub Eq NotEq Lt LtE Gt GtE Is IsNot In NotIn keyword".split())


def _literal_integer_expression(node):
    """A small positive type proof; never infer types from variable names.

    int/int and negative integer powers create floats in Python, while mixed
    Fraction/float operations may silently round. This helper proves only the
    literal case; the source-flow analysis separately handles typed variables,
    exact Fraction operations and ordinary floats outside construction sinks.
    """
    if isinstance(node, ast.Constant):
        return type(node.value) is int
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub, ast.Invert)):
        return _literal_integer_expression(node.operand)
    if not isinstance(node, ast.BinOp):
        return False
    if isinstance(node.op, ast.Pow):
        return (_literal_integer_expression(node.left) and isinstance(node.right, ast.Constant)
                and type(node.right.value) is int and node.right.value >= 0)
    return (isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod,
                                ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd))
            and _literal_integer_expression(node.left) and _literal_integer_expression(node.right))


def _dump(node):
    return ast.dump(node, include_attributes=False)


def _hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        head = _dotted(node.value)
        return head + "." + node.attr if head else ""
    return ""


def _policy():
    file = HERE / "exact_construction_policy.json"
    stat = file.stat()
    return _read_policy(stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=2)
def _read_policy(mtime, size):
    return json.loads((HERE / "exact_construction_policy.json").read_text(encoding="utf-8"))


def closed_subset_issues(text, path="<injected>", *, apply_waivers=True, repository_root=None, analysis=None):
    """Reject unanalysed syntax by default; no path-existence-based admission.

    Tests' test_* driver bodies and module-level pytest/import scaffolding are
    explicitly outside this preflight's proof domain; standalone helper/oracle
    functions (even inside test_*.py) are not exempt. The legacy cast/rounding
    pass still inspects ALL src/tests bodies, including those drivers.
    """
    tree = ast.parse(text, filename=path)
    policy = _policy()
    analysis = analysis or analyze(text, path, repository_root)
    analysis.structural_calls = set()
    imports = set(policy["imports"])
    members = set(policy.get("members", []))
    waivers = {tuple(row[k] for k in ("path", "function", "rule", "node", "context"))
               for row in policy["waivers"] if row["reason"].strip()}
    scaffold = path.startswith("tests/test_")
    contexts = site_contexts(text)
    issues = stale_waiver_issues(text, path) if apply_waivers else []

    class Closed(ast.NodeVisitor):
        def __init__(self):
            self.stack = []
            self.scopes = [tree]
            self.bindings = [{}]
            self.assigned = [set()]
            self.parents = []
            self.in_annotation = False

        def issue(self, node, rule):
            fn = ".".join(self.stack) or "<module>"
            if scaffold and (not self.stack or self.stack[0].startswith("test_")):
                return
            # Admission is a proof about this source value/call, not a waiver
            # for the function or an allowlist of arithmetic spellings.
            if rule in {"closed-unproved-arithmetic", "closed-modulo", "closed-reduction"}:
                if not analysis.arithmetic_issue(node):
                    return
            if rule == "closed-syntax" and isinstance(node, (ast.JoinedStr, ast.FormattedValue)):
                if not analysis.reaches_sink(node):
                    return
            if rule in {"closed-unknown-call", "closed-import-call", "closed-unknown-member", "closed-method-call"}:
                if analysis.call_proved(node):
                    return
            if rule in {"closed-data-attribute", "closed-namespace-value"}:
                # Plain record data reads are permitted only off a construction
                # slice; reflection is independently refused above/below.
                if analysis.attribute_proved(node) or not analysis.reaches_sink(node):
                    return
            if rule == "closed-indirect-write" and not analysis.reaches_sink(node):
                # The provenance pass models local container/record mutation.
                # Callable escape and unknown invocation remain separate errors.
                return
            if rule == "closed-decorator" and self.structural_decorator(node):
                if isinstance(node, ast.Call):
                    analysis.structural_calls.add(_flow.key(node))
                return
            if rule == "closed-syntax" and isinstance(node, ast.Lambda) and self.data_key(node):
                return
            if rule == "closed-callback":
                keys = [item.value for item in node.keywords if item.arg == "key"]
                if keys and all(self.data_key(item) for item in keys):
                    return
            if rule == "closed-callable-value" and analysis.reference_proved(node):
                return
            if rule == "closed-shadowed-intrinsic" and (
                    path == "src/eab/construction.py" and node.name in _flow.CONSTRUCTION):
                return
            context = contexts[fn]
            key = (path, fn, rule, _dump(node), context)
            if not apply_waivers or key not in waivers:
                line = next((n.lineno for n in reversed([*self.parents, node]) if hasattr(n, "lineno")), 1)
                issues.append((path, line, fn, rule, ast.get_source_segment(text, node), _dump(node), context))

        def structural_decorator(self, node):
            fn = node.func if isinstance(node, ast.Call) else node
            target = self.resolve(fn.id) if isinstance(fn, ast.Name) else None
            return target in {
                "import:dataclasses:dataclass", "import:functools:lru_cache",
                "import:functools:cache", "builtin:property", "builtin:staticmethod",
                "builtin:classmethod",
            } and not any(isinstance(n, (ast.Lambda, ast.Starred)) for n in ast.walk(node))

        def data_key(self, node):
            # Only projection keys of the known ordering primitives are admitted.
            # A lambda capturing/invoking a numerical function is not a key proof.
            if not isinstance(node, ast.Lambda):
                return False
            parents = self.parents
            outer = next((p for p in reversed(parents) if isinstance(p, ast.Call)), None)
            if outer is None or _dotted(outer.func).split(".")[-1] not in {"sorted", "sort", "min", "max"}:
                return False
            for part in ast.walk(node.body):
                if isinstance(part, ast.Call):
                    if not isinstance(part.func, ast.Name) or self.resolve(part.func.id) not in {"builtin:abs", "builtin:min", "builtin:max"}:
                        return False
                elif isinstance(part, (ast.Lambda, ast.NamedExpr, ast.Yield, ast.YieldFrom)):
                    return False
                elif isinstance(part, ast.Name) and self.resolve(part.id) is not None:
                    if self.resolve(part.id) not in {"builtin:abs", "builtin:min", "builtin:max"}:
                        return False
            return True

        def visit(self, node):
            if type(node).__name__ not in NODE_NAMES:
                self.issue(node, "closed-syntax")
            self.parents.append(node)
            super().visit(node)
            self.parents.pop()

        def resolve(self, name):
            for symbols, assigned in zip(reversed(self.bindings), reversed(self.assigned)):
                if name in assigned:
                    return None
                if name in symbols:
                    return symbols[name]
            if name in DIRECT | CONSTRUCTORS:
                return "builtin:" + name
            return None

        def collect(self, body, parameters=()):
            symbols, assigned = {}, set(parameters)
            class Collect(ast.NodeVisitor):
                def visit_FunctionDef(inner, n):
                    symbols[n.name] = "defined:" + n.name
                visit_AsyncFunctionDef = visit_FunctionDef
                def visit_ClassDef(inner, n):
                    symbols[n.name] = "class:" + n.name
                def visit_Import(inner, n):
                    for a in n.names:
                        symbols[a.asname or a.name.split(".")[0]] = "module:" + (a.name if a.asname else a.name.split(".")[0])
                def visit_ImportFrom(inner, n):
                    for a in n.names:
                        symbols[a.asname or a.name] = "import:" + "."*n.level + (n.module or "") + ":" + a.name
                def visit_Name(inner, n):
                    if isinstance(n.ctx, (ast.Store, ast.Del)):
                        assigned.add(n.id)
            visitor = Collect()
            for n in body:
                visitor.visit(n)
            return symbols, assigned

        def visit_Module(self, n):
            self.bindings[0], self.assigned[0] = self.collect(n.body)
            self.generic_visit(n)

        def visit_FunctionDef(self, n):
            # Annotations specify types, not first-class numerical callables;
            # call expressions in annotations remain inspected by the old pass.
            annotations = [a.annotation for a in [*n.args.posonlyargs, *n.args.args, *n.args.kwonlyargs,
                                                  n.args.vararg, n.args.kwarg] if a is not None]
            for a in [*annotations, n.returns]:
                if a is not None:
                    self.annotation(a)
            self.stack.append(n.name)
            self.scopes.append(n)
            if n.name in INTRINSICS:
                self.issue(n, "closed-shadowed-intrinsic")
            if getattr(n, "type_params", ()):
                self.issue(n, "closed-type-parameters")
            for d in n.decorator_list:
                self.issue(d, "closed-decorator")
                self.visit(d)
            params = [a.arg for a in [*n.args.posonlyargs, *n.args.args, *n.args.kwonlyargs,
                                      n.args.vararg, n.args.kwarg] if a is not None]
            symbols, assigned = self.collect(n.body, params)
            self.bindings.append(symbols)
            self.assigned.append(assigned)
            for d in [*n.args.defaults, *(d for d in n.args.kw_defaults if d is not None)]:
                self.visit(d)
            for s in n.body:
                self.visit(s)
            self.assigned.pop()
            self.bindings.pop()
            self.scopes.pop()
            self.stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, n):
            for base in [*n.bases, *(k.value for k in n.keywords)]:
                self.annotation(base)
            self.stack.append(n.name)
            self.scopes.append(n)
            if n.name in INTRINSICS:
                self.issue(n, "closed-shadowed-intrinsic")
            if getattr(n, "type_params", ()):
                self.issue(n, "closed-type-parameters")
            for d in n.decorator_list:
                self.issue(d, "closed-decorator")
                self.visit(d)
            self.bindings.append(self.collect(n.body)[0])
            self.assigned.append(set())
            for s in n.body:
                self.visit(s)
            self.assigned.pop()
            self.bindings.pop()
            self.scopes.pop()
            self.stack.pop()

        def annotation(self, n):
            old = self.in_annotation
            self.in_annotation = True
            self.visit(n)
            self.in_annotation = old

        def visit_AnnAssign(self, n):
            self.annotation(n.annotation)
            self.visit(n.target)
            if n.value is not None:
                self.visit(n.value)

        def visit_Import(self, n):
            if analysis.import_proved(n):
                return
            for a in n.names:
                if a.name not in imports:
                    self.issue(n, "closed-import")

        def visit_ImportFrom(self, n):
            if analysis.import_proved(n):
                return
            for a in n.names:
                key = "."*n.level + (n.module or "") + ":" + a.name
                if a.name == "*" or key not in imports:
                    self.issue(n, "closed-import")

        def visit_Call(self, n):
            if analysis.sink_issue(n):
                self.issue(n, "closed-rounded-construction")
            if self.in_annotation:
                # Python annotations may execute constructors and retain their
                # results in a runtime dictionary outside local provenance.
                self.issue(n, "closed-annotation-call")
            if any(k.arg == "key" for k in n.keywords):
                self.issue(n, "closed-callback")
            if any(k.arg is None for k in n.keywords):
                self.issue(n, "closed-unpacked-call")
            func = n.func
            target = self.resolve(func.id) if isinstance(func, ast.Name) else None
            if (_dotted(func).split(".")[-1] == "sum"
                    or target and target.split(":")[-1] == "sum"):
                self.issue(n, "closed-reduction")
            if isinstance(func, ast.Name):
                target = self.resolve(func.id)
                if target and target.startswith("import:") and target[len("import:"):] not in imports:
                    self.issue(n, "closed-import-call")
                elif func.id in FORBIDDEN or (target and target.split(":")[-1] in FORBIDDEN):
                    self.issue(n, "closed-dynamic-call")
                elif target is None:
                    self.issue(n, "closed-unknown-call")
            elif isinstance(func, ast.Attribute):
                dotted = _dotted(func)
                root = self.resolve(dotted.split(".")[0]) if dotted else None
                # Only statically imported namespace dispatch is first-order.
                if func.attr in FORBIDDEN or func.attr.startswith("__"):
                    self.issue(n, "closed-dynamic-call")
                elif root and root.startswith(("module:", "import:")):
                    member = root + "." + ".".join(dotted.split(".")[1:])
                    if member not in members:
                        self.issue(n, "closed-unknown-member")
                else:
                    self.issue(n, "closed-method-call")
            else:
                self.issue(n, "closed-indirect-call")
            self.generic_visit(n)

        def visit_Name(self, n):
            if n.id == "__annotations__" and isinstance(n.ctx, ast.Load):
                self.issue(n, "closed-runtime-reflection")
            if self.in_annotation or not isinstance(n.ctx, ast.Load):
                return
            parent = self.parents[-2] if len(self.parents) > 1 else None
            target = self.resolve(n.id)
            if target is None:
                return
            if isinstance(parent, ast.Call) and parent.func is n:
                return
            if isinstance(parent, ast.Attribute) and parent.value is n:
                return
            if isinstance(parent, ast.Call) and _dotted(parent.func) in {"isinstance", "issubclass"}:
                return
            if isinstance(parent, ast.ExceptHandler) and parent.type is n:
                return
            if isinstance(parent, ast.Tuple) and len(self.parents) > 2:
                grandparent = self.parents[-3]
                if isinstance(grandparent, ast.ExceptHandler) and grandparent.type is parent:
                    return
                if isinstance(grandparent, ast.Call) and _dotted(grandparent.func) in {"isinstance", "issubclass"}:
                    return
            if not self.stack and (target.startswith("import:typing:") or target in {"builtin:int", "builtin:float", "builtin:bool", "builtin:str"}):
                if isinstance(parent, ast.Subscript) or any(isinstance(p, ast.Subscript) for p in self.parents[:-1]):
                    return
            if target.startswith("module:"):
                return
            if target in {"import:math:inf", "import:math:nan", "import:math:pi", "import:math:e", "import:math:tau"}:
                return
            if isinstance(parent, (ast.FunctionDef, ast.ClassDef)) and n in parent.decorator_list and self.structural_decorator(n):
                return
            if isinstance(parent, ast.keyword) and parent.arg == "default_factory" and target in {"builtin:list", "builtin:dict", "builtin:set", "builtin:tuple"}:
                outer = self.parents[-3] if len(self.parents) > 2 else None
                if isinstance(outer, ast.Call) and isinstance(outer.func, ast.Name) and self.resolve(outer.func.id) == "import:dataclasses:field":
                    return
            self.issue(n, "closed-callable-value")

        def visit_Attribute(self, n):
            # Runtime protocol/introspection attributes are not ordinary record
            # fields. New dunder spellings must not need a new bypass patch.
            if n.attr.startswith("__") and n.attr.endswith("__"):
                self.issue(n, "closed-runtime-reflection")
            if isinstance(n.ctx, (ast.Store, ast.Del)):
                self.issue(n, "closed-indirect-write")
            if not self.in_annotation and isinstance(n.ctx, ast.Load):
                parent = self.parents[-2] if len(self.parents) > 1 else None
                root = self.resolve(_dotted(n).split(".")[0])
                if (root and root.startswith(("module:", "import:"))
                        and not (isinstance(parent, ast.Call) and parent.func is n)
                        and not isinstance(parent, ast.Attribute)):
                    # Constants and type members require a reviewed site too;
                    # no guessing that an unknown attribute cannot be callable.
                    self.issue(n, "closed-namespace-value")
                elif (not root or not root.startswith(("module:", "import:"))) and not (
                        isinstance(parent, ast.Call) and parent.func is n):
                    # Even builtin generator frames / exception args can carry
                    # rounded values. Ordinary record fields need a site review;
                    # there is no globally safe attribute-name allowlist.
                    self.issue(n, "closed-data-attribute")
            self.generic_visit(n)

        def visit_BinOp(self, n):
            if not _literal_integer_expression(n):
                self.issue(n, "closed-modulo" if isinstance(n.op, ast.Mod) else "closed-unproved-arithmetic")
            self.generic_visit(n)

        def visit_With(self, n):
            if not analysis.context_proved(n):
                self.issue(n, "closed-context-protocol")
            self.generic_visit(n)

        def visit_AugAssign(self, n):
            self.issue(n, "closed-unproved-arithmetic")
            self.generic_visit(n)

        def visit_Subscript(self, n):
            if isinstance(n.ctx, (ast.Store, ast.Del)):
                self.issue(n, "closed-indirect-write")
            self.generic_visit(n)

    Closed().visit(tree)
    return list(dict.fromkeys(issues))


def site_contexts(text):
    """Hash the smallest lexical scope's source, never its sibling functions.

    Function pins include decorators, signatures, comments and the complete
    body. A nested function has its own pin rather than inheriting its outer
    scope's hash. Module/class pins cover their non-definition statements;
    separately pinned child definitions cannot invalidate unrelated sites.
    Branches may define the same qualified binding more than once. All source
    candidates for that binding are pinned together; never let the last one
    silently overwrite an earlier function's pin. Unrelated bindings remain
    independent. Newlines are normalized just like Python's source reader.
    This is a local review pin, not a transitive dependency/semantic proof.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    tree = ast.parse(text)
    definitions = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    lines = text.splitlines(keepends=True)

    def source(node):
        first = min([node.lineno, *(d.lineno for d in getattr(node, "decorator_list", ()))])
        end = node.end_lineno
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # AST.end_lineno omits trailing indented comments. They still belong
            # to the function's source review, unlike inter-function blank lines.
            for index in range(end, len(lines)):
                line = lines[index]
                stripped = line.lstrip()
                if not stripped.strip():
                    continue
                if stripped.startswith("#") and len(line) - len(stripped) > node.col_offset:
                    end = index + 1
                    continue
                break
        return "".join(lines[first - 1:end])

    def nondefinition_source(body):
        return "\n".join(source(node) for node in body if not isinstance(node, definitions))

    sources = {"<module>": [nondefinition_source(tree.body)]}

    def descend(node, names=()):
        if isinstance(node, definitions):
            names = (*names, node.name)
            if isinstance(node, ast.ClassDef):
                # The class header/decorators are part of the class contract,
                # while method implementations have independent source pins.
                first_body = min(node.body, key=lambda s: (s.lineno, s.col_offset))
                first = min([node.lineno, *(d.lineno for d in node.decorator_list)])
                header = ("".join(lines[first - 1:first_body.lineno - 1])
                          + lines[first_body.lineno - 1][:first_body.col_offset])
                context = header + nondefinition_source(node.body)
            else:
                context = source(node)
            sources.setdefault(".".join(names), []).append(context)
        for child in ast.iter_child_nodes(node):
            descend(child, names)
    descend(tree)
    return {name: _hash(parts[0] if len(parts) == 1 else json.dumps(parts, ensure_ascii=False))
            for name, parts in sources.items()}


def stale_waiver_issues(text, path):
    """Expired local reviews are explicit failures, even after a safe rewrite.

    A removed function must have its obsolete review removed by a human too.
    Files absent from the scan cannot be checked here; repository inventory
    validation is separate from this source-local contract.
    """
    rows = [row for row in _policy()["waivers"] if row["path"] == path]
    if not rows:
        return []
    contexts = site_contexts(text)
    lines = {"<module>": 1}
    nodes = set()
    node_kinds = {row["node"].split("(", 1)[0] for row in rows}

    def descend(node, names=()):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names = (*names, node.name)
            lines[".".join(names)] = node.lineno
        if type(node).__name__ in node_kinds:
            nodes.add(_dump(node))
        for child in ast.iter_child_nodes(node):
            descend(child, names)

    descend(ast.parse(text))
    issues = []
    for row in rows:
        fn = row["function"]
        if contexts.get(fn) != row["context"] or row["node"] not in nodes:
            issues.append((path, lines.get(fn, 1), fn, "closed-stale-waiver",
                           "Local review expired: " + row["rule"], row["node"],
                           contexts.get(fn, "<deleted-scope>")))
    return list(dict.fromkeys(issues))


def approved_sites(text, path, repository_root=None):
    """Return only exact site fingerprints with their local source pin intact."""
    contexts = site_contexts(text)
    policy = _policy()
    return {(r["function"], r["rule"], r["node"]) for r in policy["waivers"]
            if r["path"] == path and r["reason"].strip() and contexts.get(r["function"]) == r["context"]}
