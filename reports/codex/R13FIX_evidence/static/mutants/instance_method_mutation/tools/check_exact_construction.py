"""Auxiliary AST code check for the exact-to-binary64 boundary.

This tool and its closed-subset admission are NOT a safety guarantee. Runtime
per-value differential tests against independent rational references, including
subnormal/ordinary/overflow-edge scales, are the primary construction guard.
No static analysis here claims complete reliable data flow for arbitrary Python.
Positive subset admission plus default rejection is a maintenance aid only. exact_construction_subset.py rejects unknown syntax,
dispatch, imports and callable flow. The JSON policy records individually
reviewed sites pinned to their AST node and enclosing function source. No automatic waiver generation occurs during a scan.
The original local may-analysis still rejects premature sqrt/norm/unit and
subtract-after-rounding idioms; opaque call boundaries are rejected,
not silently assumed to have safe return or side-effect summaries. Test driver/scaffolding exemptions and the unchanged
legacy input/filter exceptions are documented in docs/r12fix_design_sync.md.
Run from any working directory.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
_subset_spec = importlib.util.spec_from_file_location("exact_construction_subset", ROOT / "tools/exact_construction_subset.py")
_subset = importlib.util.module_from_spec(_subset_spec)
_subset_spec.loader.exec_module(_subset)
closed_subset_issues = _subset.closed_subset_issues

def _name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _name(node.value) + "." + node.attr
    return ""


def scan_text(text, path="<injected>", *, repository_root=None):
    """Finite, conservative intraprocedural may-analysis, not Python proof.

    Values snapshot rounding/callable provenance at assignment, plus abstract
    object identities for local mutation. All identities are source nodes or
    lexically scoped input names; callable labels are source names or imported
    namespace members. Joins are set union over that finite domain, so loops
    reach a fixed point without a depth/iteration cap or growing synthetic AST.
    Unknown call boundaries are rejected unless context-pinned review applies;
    known argument rounding is preserved, without inventing a clean summary. This is not a proof for arbitrary Python object protocols.
    """
    tree = ast.parse(text, filename=path)
    converters = {"_float_vector", "_display_fraction", "_construction_float",
                  "scalar_rational", "vector_rational", "scalar_exact", "vector_exact",
                  "ratio_rational", "ratio_exact", "sqrt_rational", "sqrt_exact",
                  "norm_rational", "norm_exact", "unit_rational", "unit_exact",
                  "normalized_difference_rational"}
    passthrough = {"tuple", "list", "dict", "set", "sum", "min", "max", "abs",
                   "Fraction", "from_float", "zip", "enumerate", "reversed", "sorted",
                   "values", "items", "get", "copy", "__getitem__"}
    roots = {"sqrt", "sqrt_rational", "sqrt_exact"}
    vectors = {"hypot", "norm", "unit", "norm_rational", "unit_rational", "norm_exact", "unit_exact"}
    mutators = {"append", "extend", "insert", "update", "setdefault", "add", "__setitem__"}
    namespaces = {"math", "builtins", "functools"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for item in node.names:
                name = ((node.module or "") + "." + item.name
                        if isinstance(node, ast.ImportFrom) else item.name)
                parts = name.split(".")
                namespaces.update(".".join(parts[:i]) for i in range(1, len(parts) + 1))

    # A value is (rounding bits: 1 explicit boundary / 2 implicit arithmetic, callable labels, object references). These
    # immutable snapshots never retain a live AST Name to resolve after rebinding.
    empty = (False, frozenset(), frozenset())

    def value(rounded=False, names=(), refs=()):
        return int(rounded), frozenset(names), frozenset(refs)

    def combine(*values):
        flags = 0
        for v in values:
            flags |= v[0]
        return (flags,
                frozenset().union(*(v[1] for v in values)),
                frozenset().union(*(v[2] for v in values)))

    def arguments(node):
        """Every Python call argument, including *args and **kwargs."""
        return [*node.args, *(item.value for item in node.keywords)]

    def joined(*states):
        """Join bindings AND heap; callable, rounded and alias facts stay paired."""
        states = [state for state in states if state is not None]
        return tuple({key: combine(*(part[key] for part in parts if key in part))
                      for key in set().union(*(set(part) for part in parts))}
                     for parts in zip(*states)) if states else None

    analysis = _subset.analyze(text, path, repository_root)
    closed_rows = (closed_subset_issues(text, path, analysis=analysis) if repository_root is None else
                   _subset.closed_subset_issues(text, path, repository_root=repository_root, analysis=analysis))
    issues = [row[:5] for row in closed_rows]
    approved_sites = _subset.approved_sites(text, path, repository_root)

    class Check:
        def __init__(self):
            self.stack = []
            self.bindings, self.heap = {}, {}
            self.exceptions = []
            self.generator_iterators = {}
            self.lazy_inputs = {}
            self.consuming = set()

        def state(self):
            return dict(self.bindings), dict(self.heap)

        def restore(self, state):
            self.bindings, self.heap = (dict(part) for part in state)

        def checkpoint(self):
            for prefixes in self.exceptions:
                prefixes.append(self.state())

        def read(self, v):
            # Transitive references allow a list inside a list, mutable aliases,
            # and cyclic containers without recursively expanding source AST.
            refs = v[2]
            while True:
                expanded = combine(v, *(self.heap.get(ref, empty) for ref in v[2]))
                if expanded == v:
                    return value(v[0], v[1], refs)
                v = expanded

        def elements(self, v):
            parts = [self.heap[ref] for ref in v[2] if ref in self.heap]
            return self.read(combine(*parts)) if parts else v

        def container(self, node, contents):
            # Allocation sites summarize all instances; weak updates retain an
            # earlier iteration's object while an alias can still reference it.
            self.heap[node] = combine(self.heap.get(node, empty), contents)
            return self.read(value(refs={node}))

        def lookup(self, name):
            return self.read(self.bindings.get(name, value(names={name}, refs={(tuple(self.stack), name)})))

        def issue(self, node, rule):
            function = ".".join(self.stack) or "<module>"
            driver = path.startswith("tests/test_") and (not self.stack or self.stack[0].startswith("test_"))
            if driver and rule.startswith("closed-"):
                return
            if rule == "closed-unproved-call" and (analysis.call_proved(node) or
                    _subset._flow.key(node) in getattr(analysis, "structural_calls", ())):
                return
            if rule == "closed-rounded-call" and analysis.call_proved(node) and not analysis.reaches_sink(node):
                return
            if (function, rule, ast.dump(node, include_attributes=False)) not in approved_sites:
                issues.append((path, node.lineno, function, rule, ast.get_source_segment(text, node)))

        def bind(self, target, v, evaluated_owner=None):
            if isinstance(target, ast.Name):
                self.bindings[target.id] = self.read(v)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for item in target.elts:
                    self.bind(item, v)
            elif isinstance(target, ast.Starred):
                self.bind(target.value, v)
            elif isinstance(target, (ast.Attribute, ast.Subscript)):
                owner = self.evaluate(target.value) if evaluated_owner is None else evaluated_owner
                if isinstance(target, ast.Subscript) and evaluated_owner is None:
                    self.evaluate(target.slice)
                for ref in owner[2]:
                    self.heap[ref] = combine(self.heap.get(ref, empty), v)

        def assignment(self, targets, expression, v):
            # Preserve element-wise unpacking, including each element's already
            # evaluated snapshot (RHS evaluation precedes every target write).
            for target in targets:
                if (isinstance(target, (ast.Tuple, ast.List))
                        and isinstance(expression, (ast.Tuple, ast.List))
                        and len(target.elts) == len(expression.elts)
                        and not any(isinstance(item, ast.Starred) for item in target.elts)):
                    for left, right in zip(target.elts, expression.elts):
                        self.bind(left, self.expression_values.get(right, v))
                else:
                    self.bind(target, v)

        def evaluate(self, node):
            if node is None:
                return empty
            self.checkpoint()
            v = self.expression(node)
            self.expression_values[node] = v
            self.checkpoint()
            return v

        def expression(self, node):
            if isinstance(node, ast.Name):
                return self.lookup(node.id)
            if isinstance(node, ast.Constant):
                return empty
            if isinstance(node, ast.Attribute):
                base = self.evaluate(node.value)
                if node.attr == "__call__":
                    return base
                names = {name + "." + node.attr for name in base[1] if name in namespaces}
                names.add(_name(node))
                # An attribute can be supplied by a local object mutation; the
                # object summary is deliberately field-insensitive (may, not must).
                contents = combine(*(self.heap.get(ref, empty) for ref in base[2]))
                if node.attr not in mutators | passthrough:
                    names.update(self.read(contents)[1])
                return value(base[0], names, base[2])
            if isinstance(node, ast.Subscript):
                base = self.evaluate(node.value)
                self.evaluate(node.slice)
                return self.elements(base)
            if isinstance(node, ast.Dict):
                # Python interleaves each key/value pair; ast.iter_child_nodes
                # groups all keys first and would reorder walrus side effects.
                contents = []
                for key, item in zip(node.keys, node.values):
                    contents.append(self.evaluate(key))
                    contents.append(self.evaluate(item))
                return self.container(node, combine(*contents))
            if isinstance(node, ast.NamedExpr):
                v = self.evaluate(node.value)
                self.bind(node.target, v)
                return v
            if isinstance(node, ast.IfExp):
                self.evaluate(node.test)
                before = self.state()
                left = self.evaluate(node.body)
                body_state = self.state()
                self.restore(before)
                right = self.evaluate(node.orelse)
                self.restore(joined(body_state, self.state()))
                return combine(left, right)
            if isinstance(node, ast.BoolOp):
                result = self.evaluate(node.values[0])
                for item in node.values[1:]:
                    skipped = self.state()
                    result = combine(result, self.evaluate(item))
                    self.restore(joined(skipped, self.state()))
                return result
            if isinstance(node, ast.Compare):
                self.evaluate(node.left)
                for i, item in enumerate(node.comparators):
                    skipped = self.state()
                    self.consume(self.evaluate(item))
                    if i:
                        self.restore(joined(skipped, self.state()))
                return empty
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                return self.comprehension(node)
            if isinstance(node, ast.Lambda):
                defaults = [self.evaluate(item) for item in node.args.defaults]
                kw_defaults = [self.evaluate(item) if item is not None else None for item in node.args.kw_defaults]
                outer = self.state()
                positional = [*node.args.posonlyargs, *node.args.args]
                for arg in [*positional, *node.args.kwonlyargs, node.args.vararg, node.args.kwarg]:
                    if arg is not None:
                        self.bindings[arg.arg] = value(refs={arg})
                for arg, v in zip(positional[-len(defaults):], defaults):
                    self.bindings[arg.arg] = v
                for arg, v in zip(node.args.kwonlyargs, kw_defaults):
                    if v is not None:
                        self.bindings[arg.arg] = v
                # Preserve the existing narrowly declared lambda-call summary.
                if isinstance(node.body, ast.Call):
                    callable_value = self.evaluate(node.body.func)
                    self.evaluate(node.body)
                else:
                    self.evaluate(node.body)
                    callable_value = empty
                self.restore(outer)
                return value(names=callable_value[1], refs={node})
            if isinstance(node, ast.Call):
                function = self.evaluate(node.func)  # capture before argument walruses
                evaluated = {arg: self.evaluate(arg) for arg in [*node.args, *(k.value for k in node.keywords)]}
                args = [evaluated[arg] for arg in arguments(node)]
                names = {name.split(".")[-1] for name in function[1]}
                raw_args = args
                args = [self.consume(arg) for arg in args]
                sentinel = (len(node.args) == 1 and isinstance(node.args[0], ast.Constant)
                            and isinstance(node.args[0].value, str)
                            and node.args[0].value.lower().lstrip("+-") in {"inf", "infinity", "nan"})
                if function[1] & {"math.sqrt", "math.hypot"} and not path.startswith("tests/"):
                    self.issue(node, "implicit-root")
                if function[1] & {"float", "builtins.float"} and not sentinel:
                    self.issue(node, "direct-float")
                if names & {"map"} and args and args[0][1] & {"float", "builtins.float"}:
                    self.issue(node, "direct-float")
                rounding = combine(*(self.read(arg) for arg in args))[0]
                if analysis.power_sink(node) and args and self.read(args[0])[0]:
                    self.issue(node, "closed-rounded-construction")
                if rounding & 1:
                    if names & roots:
                        self.issue(node, "rounded-root")
                    if names & vectors:
                        self.issue(node, "rounded-vector")
                if rounding & 2 and names & (roots | vectors):
                    self.issue(node, "closed-rounded-construction")
                if isinstance(node.func, ast.Attribute) and node.func.attr in mutators:
                    for ref in function[2]:
                        self.heap[ref] = combine(self.heap.get(ref, empty), *args)
                if function[1] & {"functools.partial", "partial"}:
                    bound_names = {name.split(".")[-1] for name in args[0][1]} if args else set()
                    if any(arg[0] for arg in args[1:]):
                        if bound_names & roots:
                            self.issue(node, "rounded-root")
                        if bound_names & vectors:
                            self.issue(node, "rounded-vector")
                    return combine(value(refs={node}), *args[:1])
                if names & (converters | {"float"}):
                    return value(True, refs={node})
                if names & {"map", "zip", "enumerate", "reversed", "filter"}:
                    self.lazy_inputs[node] = combine(self.lazy_inputs.get(node, empty), *raw_args)
                if names & {"map"} and args:
                    mapped = {name.split(".")[-1] for name in args[0][1]}
                    return self.container(node, combine(value(bool(mapped & (converters | {"float"}))), *args))
                if isinstance(node.func, ast.Attribute) and node.func.attr in {"__next__", "send", "throw"}:
                    return self.consume(value(refs=function[2]))
                if names & (passthrough | {"next", "filter"}):
                    contents = combine(*args, value(function[0]),
                                       self.elements(value(refs=function[2])))
                    if names & {"sum"} and analysis.return_kind(node) != "exact":
                        contents = combine(contents, value(2))
                    return self.container(node, contents)
                # Exact discrete metadata is not a floating construction.
                if function[1] & {"len", "range", "isinstance", "issubclass", "type", "bool"}:
                    return value(refs={node})
                if function[1] & {"AssertionError", "ArithmeticError", "IndexError", "KeyError", "NotImplementedError", "OverflowError", "RuntimeError", "StopIteration", "TypeError", "ValueError", "ZeroDivisionError"}:
                    return value(refs={node})
                if function[1] & {"int", "builtins.int"}:
                    return value(combine(*args)[0], refs={node})
                driver = path.startswith("tests/test_") and (not self.stack or self.stack[0].startswith("test_"))
                if not driver:
                    self.issue(node, "closed-unproved-call")
                    sink_inputs = analysis.sink_arguments(node)
                    selected = [arg for i, arg in enumerate(args) if i in sink_inputs]
                    selected += [evaluated[k.value] for k in node.keywords if k.arg in sink_inputs]
                    if any(arg[0] for arg in (selected if analysis.call_proved(node) else args)):
                        self.issue(node, "closed-rounded-call")
                return value(0 if driver else combine(*args, value(2) if analysis.call_may_round(node) else empty)[0], refs={node})
            if isinstance(node, ast.Starred):
                return self.consume(self.evaluate(node.value))
            children = [self.evaluate(child) for child in ast.iter_child_nodes(node)
                        if isinstance(child, ast.expr)]
            if isinstance(node, ast.BinOp):
                if analysis.power_sink(node) and children and self.read(children[0])[0]:
                    self.issue(node, "closed-rounded-construction")
                if isinstance(node.op, ast.Sub) and all(v[0] & 1 for v in children):
                    self.issue(node, "subtract-rounded")
                if (isinstance(node.op, ast.Pow) and isinstance(node.right, ast.Constant)
                        and node.right.value == 0.5 and not path.startswith("tests/")):
                    self.issue(node, "implicit-root")
            if isinstance(node, (ast.Tuple, ast.List, ast.Set, ast.Dict)):
                return self.container(node, combine(*children))
            if isinstance(node, ast.BinOp) and analysis.may_round(node):
                return combine(*children, value(2))
            return combine(*children)

        def consume(self, v):
            # Consume only this iterable, not generators stored as data inside
            # an already-built container. Eager consumers detach the exhausted
            # generator identity from their results (late replay would be wrong).
            lazy = {ref for ref in v[2] if isinstance(ref, ast.GeneratorExp) or ref in self.lazy_inputs}
            result = value(v[0], v[1], v[2] - lazy)
            for ref in lazy:
                if ref in self.consuming:
                    continue
                self.consuming.add(ref)
                if isinstance(ref, ast.GeneratorExp):
                    yielded = self.elements(self.comprehension(ref, replay=True))
                else:
                    yielded = self.consume(self.lazy_inputs[ref])
                result = combine(result, yielded)
                self.consuming.remove(ref)
            return self.read(result)

        def comprehension(self, node, replay=False):
            if replay:
                outer_iter = self.generator_iterators[node]
            else:
                outer_iter = self.evaluate(node.generators[0].iter)
                if isinstance(node, ast.GeneratorExp):
                    self.generator_iterators[node] = combine(self.generator_iterators.get(node, empty), outer_iter)
            outer_iter = self.consume(outer_iter)
            outer = self.state()
            results = []

            def generator(index):
                item = node.generators[index]
                iterable = outer_iter if index == 0 else self.consume(self.evaluate(item.iter))
                entry = self.state()
                head = entry
                while True:
                    self.restore(head)
                    self.bind(item.target, self.elements(iterable))
                    filtered = []
                    for condition in item.ifs:
                        self.evaluate(condition)
                        filtered.append(self.state())
                    if index + 1 < len(node.generators):
                        generator(index + 1)
                    elif isinstance(node, ast.DictComp):
                        results.append(combine(self.evaluate(node.key), self.evaluate(node.value)))
                    else:
                        results.append(self.evaluate(node.elt))
                    new_head = joined(entry, head, self.state(), *filtered)
                    if new_head == head:
                        break
                    head = new_head
                self.restore(new_head)

            generator(0)
            after = self.state()
            # Comprehension targets are private; PEP 572 walruses escape, but
            # zero iterations / failed filters / unconsumed generators preserve
            # pre-comprehension bindings too. Heap side effects likewise may join.
            exported = set()

            def collect(item):
                if isinstance(item, ast.Lambda):
                    return
                if isinstance(item, ast.NamedExpr):
                    exported.add(item.target.id)
                for child in ast.iter_child_nodes(item):
                    collect(child)

            collect(node)
            self.restore(outer)
            for name in exported:
                if name in after[0]:
                    self.bindings[name] = combine(outer[0].get(name, empty), after[0][name])
            self.heap = joined(outer, after)[1]
            return self.container(node, combine(*results))

        def flow_join(self, *flows):
            keys = set().union(*(set(flow) for flow in flows))
            return {key: joined(*(flow.get(key) for flow in flows)) for key in keys}

        def block(self, statements, entry=None):
            flow = {"normal": self.state() if entry is None else entry}
            for statement in statements:
                current = flow.pop("normal", None)
                if current is None:
                    break
                self.restore(current)
                self.checkpoint()
                flow = self.flow_join(flow, self.statement(statement))
                self.checkpoint()
            return flow

        def branch(self, statements, entry):
            self.restore(entry)
            return self.block(statements)

        def loop(self, node):
            is_for = isinstance(node, (ast.For, ast.AsyncFor))
            iterable = self.consume(self.evaluate(node.iter)) if is_for else empty
            entry = self.state()
            head = entry
            accumulated = {}
            while True:
                self.restore(head)
                if is_for:
                    condition_state = self.state()
                    self.bind(node.target, self.elements(iterable))
                else:
                    self.evaluate(node.test)
                    condition_state = self.state()
                body = self.block(node.body)
                accumulated = self.flow_join(accumulated, body)
                backedge = joined(body.get("normal"), body.get("continue"))
                new_head = joined(entry, head, backedge)
                if new_head == head:
                    break
                head = new_head
            # Only condition/exhaustion exits enter else; a break bypasses it.
            finished = self.branch(node.orelse, condition_state)
            outgoing = {key: state for key, state in accumulated.items()
                        if key not in {"normal", "break", "continue"}}
            if "break" in accumulated:
                outgoing["normal"] = accumulated["break"]
            return self.flow_join(outgoing, finished)

        def try_statement(self, node):
            prefix_states = [self.state()]
            self.exceptions.append(prefix_states)
            body = self.block(node.body)
            self.exceptions.pop()
            raised = joined(*prefix_states, body.get("raise"))
            handlers = []
            for handler in node.handlers:
                self.restore(raised)
                self.evaluate(handler.type)
                if handler.name:
                    self.bindings[handler.name] = value(refs={handler})
                handled = self.block(handler.body)
                handlers.append(handled)
                # except* handlers can both run; conservatively retain any
                # preceding handler state as well as independent exception entry.
                if isinstance(node, ast.TryStar):
                    raised = joined(raised, *handled.values())
            normal = self.branch(node.orelse, body["normal"]) if "normal" in body else {}
            exits = self.flow_join({k: v for k, v in body.items() if k != "normal"},
                                   {"raise": raised}, normal, *handlers)
            if node.finalbody:
                final = self.branch(node.finalbody, joined(*exits.values()))
                exits = self.flow_join({k: v for k, v in final.items() if k != "normal"},
                                       {k: final["normal"] for k in exits} if "normal" in final else {})
            return exits

        def annotations(self, expressions):
            # Annotation execution depends on scope/future flags. Keep the old
            # gate's expression inspection without asserting eager evaluation:
            # both unevaluated and evaluated local effects remain possible.
            before = self.state()
            for expression in expressions:
                self.evaluate(expression)
            self.restore(joined(before, self.state()))

        def statement(self, node):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    self.evaluate(decorator)
                defaults = [self.evaluate(item) for item in node.args.defaults]
                kw_defaults = [self.evaluate(item) if item is not None else None for item in node.args.kw_defaults]
                self.annotations([arg.annotation for arg in
                                  [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
                                   node.args.vararg, node.args.kwarg] if arg is not None] + [node.returns])
                outer = self.state()
                self.stack.append(node.name)
                positional = [*node.args.posonlyargs, *node.args.args]
                for arg in [*positional, *node.args.kwonlyargs, node.args.vararg, node.args.kwarg]:
                    if arg is not None:
                        self.bindings.pop(arg.arg, None)
                for arg, v in zip(positional[-len(defaults):], defaults):
                    self.bindings[arg.arg] = v
                for arg, v in zip(node.args.kwonlyargs, kw_defaults):
                    if v is not None:
                        self.bindings[arg.arg] = v
                saved_exceptions, self.exceptions = self.exceptions, []
                self.block(node.body)
                self.exceptions = saved_exceptions
                self.stack.pop()
                self.restore(outer)
            elif isinstance(node, ast.ClassDef):
                for expression in [*node.decorator_list, *node.bases, *(k.value for k in node.keywords)]:
                    self.evaluate(expression)
                outer = self.state()
                self.stack.append(node.name)
                self.block(node.body)
                self.stack.pop()
                self.restore(outer)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for item in node.names:
                    if isinstance(node, ast.Import):
                        bound = item.asname or item.name.split(".")[0]
                        name = item.name if item.asname else bound
                    else:
                        bound = item.asname or item.name
                        name = (node.module or "") + "." + item.name
                    self.bindings[bound] = value(names={name}, refs={node})
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                if node.value is not None:
                    v = self.evaluate(node.value)
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    self.assignment(targets, node.value, v)
                if isinstance(node, ast.AnnAssign):
                    self.annotations([node.annotation])
            elif isinstance(node, ast.AugAssign):
                left = self.evaluate(node.target)
                owner = (self.expression_values[node.target.value]
                         if isinstance(node.target, (ast.Attribute, ast.Subscript)) else None)
                right = self.evaluate(node.value)
                if analysis.power_sink(node) and self.read(left)[0]:
                    self.issue(node, "closed-rounded-construction")
                if isinstance(node.op, ast.Sub) and left[0] & 1 and right[0] & 1:
                    self.issue(node, "subtract-rounded")
                # Augmented assignment evaluates its lvalue exactly once,
                # before the RHS; writing back must not replay an index walrus.
                self.bind(node.target, combine(left, right, value(2) if analysis.may_round(node) else empty), evaluated_owner=owner)
            elif isinstance(node, ast.Assert):
                self.evaluate(node.test)
                success = self.state()
                self.evaluate(node.msg)
                return {"normal": success, "raise": self.state()}
            elif isinstance(node, ast.If):
                self.evaluate(node.test)
                entry = self.state()
                return self.flow_join(self.branch(node.body, entry), self.branch(node.orelse, entry))
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                return self.loop(node)
            elif isinstance(node, (ast.Try, ast.TryStar)):
                return self.try_statement(node)
            elif isinstance(node, ast.Match):
                subject = self.evaluate(node.subject)
                entry = self.state()
                paths = [{"normal": entry}]
                for case in node.cases:
                    self.restore(entry)
                    for item in ast.walk(case.pattern):
                        name = (item.name if isinstance(item, (ast.MatchAs, ast.MatchStar))
                                else item.rest if isinstance(item, ast.MatchMapping) else None)
                        if name:
                            self.bindings[name] = subject
                    if case.guard:
                        self.evaluate(case.guard)
                        entry = joined(entry, self.state())
                    paths.append(self.block(case.body))
                return self.flow_join(*paths, {"normal": entry})
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    v = self.evaluate(item.context_expr)
                    if isinstance(item.context_expr, ast.Call):
                        v = combine(v, *(self.expression_values.get(arg, empty) for arg in arguments(item.context_expr)))
                    if item.optional_vars is not None:
                        self.bind(item.optional_vars, v)
                prefixes = [self.state()]
                self.exceptions.append(prefixes)
                body = self.block(node.body)
                self.exceptions.pop()
                # __exit__/__aexit__ may suppress an exception, never a return,
                # break or continue. Every possible raising prefix can resume.
                return self.flow_join(body, {"normal": joined(*prefixes, body.get("raise"))})
            elif isinstance(node, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.expr):
                        self.evaluate(child)
                return {type(node).__name__.lower(): self.state()}
            elif isinstance(node, ast.Delete):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.bindings.pop(target.id, None)
                    else:
                        self.evaluate(target)
            else:
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.expr):
                        self.evaluate(child)
            return {"normal": self.state()}

        expression_values = None

    checker = Check()
    checker.expression_values = {}
    checker.block(tree.body)
    return list(dict.fromkeys(issues))


def scan_repository(root=ROOT):
    return [issue for folder in ("src", "tests")
            for path in sorted((root / folder).rglob("*.py"))
            for issue in scan_text(path.read_text(encoding="utf-8-sig"), path.relative_to(root).as_posix(), repository_root=root)]


if __name__ == "__main__":
    found = scan_repository()
    for path, line, function, rule, code in found:
        print(f"{path}:{line} {function}: {rule}: {code}")
    print(f"exact construction AST gate: {len(found)} violation(s)")
    sys.exit(bool(found))
