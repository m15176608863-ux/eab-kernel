"""Source-derived, sink-directed facts for the construction preflight.

This is an auxiliary abstract interpreter for ordinary first-order Python, not
execution, a safety guarantee, or complete data flow for arbitrary Python.
Runtime differential tests with independent rational references are primary.
Known source instance methods, a single-inheritance initializer chain, generated
dataclass post-initialization, and explicit property setters replay effects.
Unresolved/multiple-inheritance MRO and dynamic object protocols are rejected
where recognized, not modeled as safe. Metaclasses, dynamically installed
methods/descriptors, monkeypatching, extension calls, general aliasing and
re-entrant protocol execution are outside any completeness claim.  It distinguishes supplied float
data from arithmetic-derived floats.  Only the latter is forbidden on a path
to a root, norm, unit vector or geometric difference construction.  Converting
an already-derived float back to Fraction does not erase that history.

Function bodies and dataclass annotations are read from source.  No repository
hash, function-name exemption, runtime import or policy waiver is used here.
Unknown dispatch remains unknown, even when its result is not a construction.
"""
from __future__ import annotations

import ast
from collections import namedtuple
from functools import lru_cache
from pathlib import Path


I, Q, F, INPUT, B, S, N, UNKNOWN = range(8)
Value = namedtuple("Value", "types origins bad objects refs")
EMPTY = Value(frozenset(), frozenset(), frozenset(), frozenset(), frozenset())


def value(*types, origins=(), bad=(), objects=(), refs=()):
    return Value(frozenset(types), frozenset(origins), frozenset(bad), frozenset(objects), frozenset(refs))


def join(*values):
    return Value(*(frozenset().union(*(v[i] for v in values)) for i in range(5)))


def key(node):
    return (getattr(node, "lineno", 0), getattr(node, "col_offset", 0),
            ast.dump(node, include_attributes=False))


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted(node.value)
        return prefix + "." + node.attr if prefix else ""
    return ""


CONSTRUCTION = frozenset("scalar_rational vector_rational ratio_rational sqrt_rational norm_rational unit_rational normalized_difference_rational".split())
SINKS = frozenset("sqrt_rational norm_rational unit_rational normalized_difference_rational".split())
DYNAMIC = frozenset("eval exec compile getattr setattr delattr hasattr globals locals vars dir __import__ callable partial reduce map filter iter".split())
SCALAR_PURE = frozenset("abs min max sum round".split())
CONTAINERS = frozenset("tuple list set frozenset dict zip enumerate reversed sorted range".split())
DISCRETE = frozenset("all any bool len isinstance issubclass hash id ord".split())
EXCEPTIONS = frozenset("AssertionError ArithmeticError IndexError KeyError NotImplementedError OverflowError RuntimeError StopIteration TypeError ValueError ZeroDivisionError Exception".split())
MATH_INT = frozenset("isqrt gcd lcm comb perm factorial floor ceil trunc".split())
MATH_BOOL = frozenset("isfinite isnan isinf isclose".split())
MATH_FLOAT = frozenset("sqrt hypot sin cos tan asin acos atan atan2 sinh cosh tanh exp exp2 expm1 log log2 log10 log1p pow ldexp frexp modf fsum prod remainder fmod copysign fabs nextafter ulp degrees radians dist".split())
CONTAINER_METHODS = frozenset("append extend insert add update setdefault pop clear remove discard sort reverse copy get items keys values count index".split())
TEXT_METHODS = frozenset("strip lstrip rstrip split rsplit splitlines join lower upper replace startswith endswith format encode isdigit isdecimal".split())
MODELED_MODULES = frozenset("math fractions dataclasses functools itertools pathlib json csv collections random pytest struct".split())


def _struct_format(node):
    """Finite literal-format transfer; never executes the struct protocol."""
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return None
    fmt = node.value
    if fmt[:1] in {"<", ">", "!", "="}:
        fmt = fmt[1:]
    elif fmt.startswith("@"):
        return None  # Native alignment/width is intentionally outside the model.
    arguments, types, floating, narrow = 0, set(), set(), set()
    count = ""
    for code in fmt:
        if code.isspace():
            if count:
                return None
            continue
        if code.isascii() and code.isdigit():
            count += code
            if len(count) > 6:
                return None
            continue
        repeat = int(count) if count else 1
        count = ""
        if code not in "xcbB?hHiIlLqQefdsp":
            return None
        arity = 0 if code == "x" else 1 if code in "sp" else repeat
        if arguments + arity > 4096:
            return None
        if code in "efd":
            floating.update(range(arguments, arguments + arity))
            if code in "ef":
                narrow.update(range(arguments, arguments + arity))
        arguments += arity
        if arity:
            types.add(S if code in "csp" else F if code in "efd" else B if code == "?" else I)
    return None if count else (arguments, types, floating, narrow)


@lru_cache(maxsize=512)
def _read_module(path, mtime, size):
    return Path(path).read_text(encoding="utf-8-sig")


class Module:
    def __init__(self, name, text, path):
        self.name, self.text, self.path = name, text, path
        self.tree = ast.parse(text, filename=path)
        self.definitions = {}
        self.classes = {}
        self.imports = {}
        self.bindings = {}
        self.globals = {}
        self.parents = {}
        self.functions = []
        self.setters = {}
        package = name.split(".") if path.endswith("__init__.py") else name.split(".")[:-1]

        def collect(body, prefix=""):
            bindings = self.bindings.setdefault(prefix.rstrip("."), {})
            for node in body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qualified = prefix + node.name
                    setter = any(isinstance(d, ast.Attribute) and d.attr == "setter"
                                 and dotted(d.value) == node.name for d in node.decorator_list)
                    if setter:
                        self.setters[qualified] = qualified + ".<setter>"
                        qualified = self.setters[qualified]
                    self.definitions[qualified] = node
                    bindings[node.name] = ("definition", qualified)
                    self.functions.append((qualified, node))
                    collect(node.body, qualified + ".")
                elif isinstance(node, ast.ClassDef):
                    qualified = prefix + node.name
                    self.classes[qualified] = node
                    bindings[node.name] = ("definition", qualified)
                    collect(node.body, qualified + ".")
                elif isinstance(node, ast.Import):
                    for item in node.names:
                        local = item.asname or item.name.split(".")[0]
                        imported = item.name if item.asname else item.name.split(".")[0]
                        bindings[local] = ("import", imported)
                        if not prefix:
                            self.imports[local] = imported
                elif isinstance(node, ast.ImportFrom):
                    parent = ".".join(package[:len(package) - node.level + 1]) if node.level else ""
                    origin = ".".join(p for p in (parent, node.module or "") if p)
                    for item in node.names:
                        local, imported = item.asname or item.name, origin + "." + item.name
                        bindings[local] = ("import", imported)
                        if not prefix:
                            self.imports[local] = imported
                elif not prefix and isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        if isinstance(target, ast.Name):
                            self.globals[target.id] = node.value
        collect(self.tree.body)
        for parent in ast.walk(self.tree):
            for child in ast.iter_child_nodes(parent):
                self.parents[child] = parent


class Analysis:
    """Queries use structural location keys, so callers may parse independently."""
    def __init__(self, text, path, repository_root=None):
        self.root = Path(repository_root) if repository_root is not None else Path(__file__).resolve().parents[1]
        clean = path.replace("\\", "/")
        name = clean[:-3].replace("/", ".") if clean.endswith(".py") else clean
        if name.startswith("src."):
            name = name[4:]
        if name.endswith(".__init__"):
            name = name[:-9]
        self.main = Module(name, text, path)
        self.modules = {name: self.main}
        self.definition_cache = {}
        self.values = {}
        self.kinds = {}
        self.attributes = set()
        self.references = set()
        self.allocations = set()
        self.sink_nodes = set()
        self.hazards = set()
        self.unknown_sinks = set()
        self.sink_issues = set()
        self.power_sinks = set()
        self.call_sink_arguments = {}
        self.active = set()
        self.globals_active = set()
        self.cache = {}
        self.module_envs = {}
        self.defaults = {}
        self.class_defaults = {}
        self.record_fields = {}
        self.field_write_effects = []
        self.last_field_mutations = {}
        self.sink_effects = []
        self.last_function_effects = []
        self.last_mutations = {}
        self.unproved_effects = []
        self.exception_prefixes = []
        self.loop_transfers = []
        self.contexts = {}
        self.last_unproved_effects = set()
        self._module_env(self.main)
        functions = [(qualified, node) for qualified, node in self.main.functions
                     if not (clean.startswith("tests/test_") and qualified.split(".")[0].startswith("test_"))]
        incoming = set()
        for qualified, node in functions:
            for call in ast.walk(node):
                if isinstance(call, ast.Call):
                    owner, target = self._definition(self._qualified(self.main, dotted(call.func), qualified))
                    if owner is self.main and target != qualified:
                        incoming.add(target)

        def entry(qualified, node):
            arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            supplied = [self._annotation(self.main, item.annotation) for item in arguments]
            if "." in qualified and arguments and arguments[0].arg in {"self", "cls"}:
                cls = qualified.rsplit(".", 1)[0]
                if cls in self.main.classes:
                    supplied[0] = value(objects={self.main.name + "." + cls})
            self._function(self.main, qualified, supplied, {})

        # Infer first-order callee facts from source callers, rather than first
        # poisoning every polymorphic helper with an invented unknown call.
        # Unreachable definitions and recursive components are still checked;
        # adding a new uncalled function never evades the admission gate.
        for qualified, node in functions:
            if qualified not in incoming:
                entry(qualified, node)
        for qualified, node in functions:
            if not any(signature[0:2] == (self.main.name, qualified) for signature in self.cache):
                entry(qualified, node)

    def _module(self, name):
        if name in self.modules:
            return self.modules[name]
        for base in (self.root / "src", self.root, self.root / "tests", self.root / "tools"):
            path = base.joinpath(*name.split("."))
            for candidate in (path.with_suffix(".py"), path / "__init__.py"):
                if candidate.is_file():
                    stat = candidate.stat()
                    module = Module(name, _read_module(str(candidate), stat.st_mtime_ns, stat.st_size), str(candidate))
                    self.modules[name] = module
                    return module
        self.modules[name] = None
        return None

    def _qualified(self, module, spelling, scope=""):
        head, _, tail = spelling.partition(".")
        scopes = [".".join(scope.split(".")[:i]) for i in range(len(scope.split(".")), 0, -1)] if scope else []
        for lexical in (*scopes, ""):
            binding = module.bindings.get(lexical, {}).get(head)
            if binding is not None:
                kind, bound = binding
                base = module.name + "." + bound if kind == "definition" else bound
                return base + ("." + tail if tail else "")
        return spelling

    @staticmethod
    def _module_value(result):
        if result.types or result.bad or len(result.objects) != 1:
            return None
        name = next(iter(result.objects))
        return name[7:] if name.startswith("module:") else None

    def _bound_name(self, module, scope, spelling, env):
        """Resolve direct module aliases, never values extracted from containers."""
        head, _, tail = spelling.partition(".")
        if head in env:
            alias = self._module_value(env[head])
            if alias is None:
                return "", True
            name = alias + ("." + tail if tail else "")
        else:
            name = self._qualified(module, spelling, scope)
        if any(name == marker[16:] or name.startswith(marker[16:] + ".")
               for marker in env if marker.startswith("<mutated-module:")):
            return "", True
        return name, False

    def _source_value(self, qualified):
        """A source data binding is not a callable exemption or import execution."""
        if qualified in MODELED_MODULES or self._module(qualified) is not None:
            return value(objects={"module:" + qualified})
        parts = qualified.split(".")
        for split in range(len(parts) - 1, 0, -1):
            owner = self._module(".".join(parts[:split]))
            field = ".".join(parts[split:])
            if owner is None or "." in field:
                continue
            if field in owner.globals:
                return self._module_env(owner).get(field, value(UNKNOWN))
            if field in owner.imports:
                redirected = owner.imports[field]
                if redirected != qualified:
                    marker = (qualified, "imported-value")
                    if marker not in self.globals_active:
                        self.globals_active.add(marker)
                        result = self._source_value(redirected)
                        self.globals_active.remove(marker)
                        return result
        return None

    @staticmethod
    def _data_value(result):
        return (bool(result.types) and result.types <= {I, Q, F, B, S, N}
                and all(item.startswith(("container:", "literal:", "sequence:")) for item in result.objects))

    def _prepare_write(self, module, scope, target, env):
        if isinstance(target, (ast.Tuple, ast.List)):
            for child in target.elts:
                self._prepare_write(module, scope, child, env)
        elif isinstance(target, ast.Attribute):
            owner = self._expr(module, scope, target.value, env)
            namespace = self._module_value(owner)
            if namespace is not None:
                env["<mutated-module:" + namespace] = value(UNKNOWN)
                if self.unproved_effects:
                    self.unproved_effects[-1].add((module.name, scope, "module-write"))

    def _definition(self, qualified):
        if qualified in self.definition_cache:
            return self.definition_cache[qualified]
        self.definition_cache[qualified] = (None, None)
        parts = qualified.split(".")
        for split in range(len(parts) - 1, 0, -1):
            module = self._module(".".join(parts[:split]))
            if module is not None:
                name = ".".join(parts[split:])
                if name in module.definitions or name in module.classes:
                    self.definition_cache[qualified] = module, name
                    return module, name
                head, _, tail = name.partition(".")
                if head in module.imports:
                    redirected = module.imports[head] + ("." + tail if tail else "")
                    if redirected != qualified:
                        result = self._definition(redirected)
                        self.definition_cache[qualified] = result
                        return result
        return None, None

    def _class_chain(self, module, cls, seen=()):
        """Known single-inheritance source chain; no guessed dynamic/C3 MRO."""
        marker = (module.name, cls)
        if marker in seen or cls not in module.classes:
            return None
        bases = module.classes[cls].bases
        if not bases:
            return [(module, cls)]
        base_names = [self._qualified(module, dotted(base), cls) for base in bases]
        # Ordinary literal string Enums have a known stdlib constructor and no
        # user lifecycle body. This is not permission for arbitrary metaclasses.
        if set(base_names) == {"str", "enum.Enum"} and all(isinstance(member, (ast.Assign, ast.Expr, ast.Pass)) for member in module.classes[cls].body):
            return [(module, cls)]
        if len(bases) != 1:
            return None
        base = base_names[0]
        if base in {"object", "builtins.object"} | EXCEPTIONS:
            return [(module, cls)]
        owner, parent = self._definition(base)
        if owner is None or parent not in owner.classes:
            return None
        tail = self._class_chain(owner, parent, (*seen, marker))
        return None if tail is None else [(module, cls), *tail]

    def _method(self, module, cls, member, *, setter=False):
        chain = self._class_chain(module, cls)
        for owner, ancestor in chain or ():
            name = ancestor + "." + member
            if setter:
                name = owner.setters.get(name)
            if name in owner.definitions:
                return owner, name
        return None, None

    def _invoke(self, module, scope, node, env, owner, target, args, keywords,
                argument_nodes=(), closure=None):
        """Replay the same return, heap, sink and unknown effects for every call."""
        result = self._function(owner, target, args, keywords, closure=closure)
        definition = owner.definitions[target]
        parameters = [*definition.args.posonlyargs, *definition.args.args]
        actual = {parameter.arg: (passed, argument_nodes[index] if index < len(argument_nodes) else None)
                  for index, (parameter, passed) in enumerate(zip(parameters, args))}
        actual.update({name: (passed, None) for name, passed in keywords.items()})
        for parameter, (passed, argument) in actual.items():
            for (changed_parameter, field), changed in self.last_field_mutations.items():
                if changed_parameter != parameter:
                    continue
                for ref in passed.refs:
                    fields = self.record_fields.setdefault(ref, {})
                    fields[field] = join(fields.get(field, EMPTY), changed)
                    if self.field_write_effects:
                        marker = (ref, field)
                        self.field_write_effects[-1][marker] = join(self.field_write_effects[-1].get(marker, EMPTY), changed)
            if parameter in self.last_mutations:
                for local, old in list(env.items()):
                    if (isinstance(argument, ast.Name) and local == argument.id) or passed.refs & old.refs:
                        env[local] = join(old, self.last_mutations[parameter])
        if module is self.main and node is not None and self.last_function_effects:
            visible = list(node.args) if isinstance(node, ast.Call) else []
            positions = {visible.index(argument_node) for argument_node, argument in zip(argument_nodes, args)
                         if argument_node in visible and any(argument.origins & affected.origins for affected, _, _ in self.last_function_effects)}
            positions.update(name for name, argument in keywords.items()
                             if any(argument.origins & affected.origins for affected, _, _ in self.last_function_effects))
            self.call_sink_arguments.setdefault(key(node), set()).update(positions)
            if positions:
                self.sink_nodes.add(key(node))
            if any(affected.bad for affected, _, _ in self.last_function_effects):
                self.sink_issues.add(key(node))
        return result

    def _assign(self, module, scope, target, result, env):
        if isinstance(target, ast.Attribute):
            receiver = self._expr(module, scope, target.value, env)
            setters = []
            for obj in receiver.objects:
                owner, cls = self._definition(obj)
                if owner is not None and cls in owner.classes:
                    setter_owner, setter = self._method(owner, cls, target.attr, setter=True)
                    if setter_owner is not None:
                        setters.append((setter_owner, setter))
            if setters:
                for owner, setter in setters:
                    self._invoke(module, scope, target, env, owner, setter,
                                 [receiver, result], {}, [target.value])
                return
        self._prepare_write(module, scope, target, env)
        self._bind(target, result, env)

    def _annotation(self, module, node):
        if node is None:
            return value(INPUT)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                node = ast.parse(node.value, mode="eval").body
            except SyntaxError:
                return value(INPUT)
        name = self._qualified(module, dotted(node))
        if name in {"int", "builtins.int"}:
            return value(I)
        if name in {"float", "builtins.float"}:
            return value(F)
        if name in {"Fraction", "fractions.Fraction"}:
            return value(Q)
        if name in {"bool", "builtins.bool"}:
            return value(B)
        if name in {"str", "bytes", "Path", "pathlib.Path"}:
            return value(S, objects={name})
        if isinstance(node, ast.Subscript):
            base = dotted(node.value).split(".")[-1]
            children = list(node.slice.elts) if isinstance(node.slice, ast.Tuple) else [node.slice]
            element = join(*(self._annotation(module, child) for child in children if not (isinstance(child, ast.Constant) and child.value is Ellipsis)))
            if base in {"tuple", "list", "set", "frozenset", "dict", "Sequence", "Iterable", "Iterator", "Mapping", "Optional", "Union"}:
                nonempty = base == "tuple" and bool(children) and not any(isinstance(child, ast.Constant) and child.value is Ellipsis for child in children)
                return join(element, value(objects={"container:" + base} | ({"sequence:nonempty"} if nonempty else set())))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return join(self._annotation(module, node.left), self._annotation(module, node.right))
        owner, cls = self._definition(name)
        if owner is not None and cls in owner.classes:
            return value(objects={name})
        # Source-level type aliases (Vec3, Number, etc.), not spelling guesses.
        if isinstance(node, ast.Name) and node.id in module.globals:
            marker = (module.name, node.id, "annotation")
            if marker not in self.globals_active:
                self.globals_active.add(marker)
                result = self._annotation(module, module.globals[node.id])
                self.globals_active.remove(marker)
                return result
        return value(INPUT)

    def _module_env(self, module):
        if module.name in self.module_envs:
            return dict(self.module_envs[module.name])
        env = {}
        self.module_envs[module.name] = env
        # Evaluation order matters: a retained alias/default is a snapshot,
        # not an expression re-evaluated after the source name is rebound.
        for node in module.tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                result = self._expr(module, "", node.value, env) if node.value is not None else self._annotation(module, node.annotation)
                for target in targets:
                    self._prepare_write(module, "", target, env)
                    self._bind(target, result, env)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for parameter, expression in self._default_nodes(node).items():
                    self.defaults[(module.name, node.name, parameter)] = self._expr(module, "", expression, env)
            elif isinstance(node, ast.ClassDef):
                for member in node.body:
                    if isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name) and member.value is not None:
                        self.class_defaults[(module.name, node.name, member.target.id)] = self._expr(module, "", member.value, env)
        return dict(env)

    @staticmethod
    def _default_nodes(node):
        parameters = [*node.args.posonlyargs, *node.args.args]
        defaults = dict(zip((item.arg for item in parameters[-len(node.args.defaults):]), node.args.defaults)) if node.args.defaults else {}
        defaults.update({item.arg: default for item, default in zip(node.args.kwonlyargs, node.args.kw_defaults) if default is not None})
        return defaults

    def _record(self, module, node, result):
        if module is self.main:
            marker = key(node)
            result = join(result, value(origins={marker}))
            self.values[marker] = join(self.values.get(marker, EMPTY), result)
        return result

    def _classify(self, module, node, kind):
        if module is self.main:
            marker = key(node)
            previous = self.kinds.get(marker)
            if previous is None or kind in {"unknown", "dynamic"}:
                self.kinds[marker] = kind

    def _sink(self, result, module=None, node=None):
        if self.sink_effects:
            self.sink_effects[-1].append((result, module, node))
            return
        self.sink_nodes.update(result.origins)
        self.hazards.update(result.bad)
        if result.bad and module is self.main and node is not None:
            self.sink_issues.add(key(node))
        if UNKNOWN in result.types:
            self.unknown_sinks.update(result.origins)

    def _bind(self, target, result, env):
        if isinstance(target, ast.Name):
            env[target.id] = result
        elif isinstance(target, (ast.Tuple, ast.List)):
            for child in target.elts:
                self._bind(child, result, env)
        elif isinstance(target, ast.Starred):
            self._bind(target.value, result, env)
        elif isinstance(target, (ast.Subscript, ast.Attribute)) and isinstance(target.value, ast.Name):
            if isinstance(target, ast.Attribute):
                owner = env.get(target.value.id, EMPTY)
                for ref in owner.refs:
                    fields = self.record_fields.setdefault(ref, {})
                    fields[target.attr] = join(fields.get(target.attr, EMPTY), result)
                    if self.field_write_effects:
                        marker = (ref, target.attr)
                        previous = self.field_write_effects[-1].get(marker, EMPTY)
                        self.field_write_effects[-1][marker] = join(previous, result)
            if isinstance(target, ast.Subscript):
                env[target.value.id] = join(env.get(target.value.id, EMPTY), result)

    def _function(self, module, name, supplied, keywords, closure=None):
        node = module.definitions[name]
        parameters = [*node.args.posonlyargs, *node.args.args]
        env = self._module_env(module)
        if closure is not None:
            env.update(closure)
        defaults = self._default_nodes(node)
        for index, parameter in enumerate([*parameters, *node.args.kwonlyargs]):
            result = supplied[index] if index < len(supplied) else keywords.get(parameter.arg)
            if result is None:
                captured = (closure or {}).get("<default:" + name + ":" + parameter.arg + ">", self.defaults.get((module.name, name, parameter.arg)))
                result = captured if captured is not None else self._expr(module, name, defaults[parameter.arg], env) if parameter.arg in defaults else self._annotation(module, parameter.annotation)
            # A fixed-tuple parameter contract supplies arity, not element
            # rounding/type facts. Valid calls to Point/Vec3 are nonempty even
            # when a preceding comprehension has forgotten their arity.
            annotation = self._annotation(module, parameter.annotation)
            if "sequence:nonempty" in annotation.objects and any(obj.startswith("container:") for obj in result.objects):
                result = join(result, value(objects={"sequence:nonempty"}))
            env[parameter.arg] = result
        if node.args.vararg:
            env[node.args.vararg.arg] = join(*supplied[len(parameters):], value(objects={"container:tuple"}))
        if node.args.kwarg:
            env[node.args.kwarg.arg] = join(*keywords.values(), value(objects={"container:dict"}))
        argument_names = [p.arg for p in [*parameters, *node.args.kwonlyargs]]
        argument_names += [p.arg for p in [node.args.vararg, node.args.kwarg] if p is not None]
        if closure is not None:
            argument_names += [p for p in closure if p not in argument_names]
        actual = {p: env[p] for p in argument_names}
        actual_fields = {p: {field: join(*(self.record_fields.get(ref, {}).get(field, EMPTY) for ref in result.refs))
                             for field in set().union(*(set(self.record_fields.get(ref, {})) for ref in result.refs))}
                         for p, result in actual.items()}
        signature = (module.name, name, tuple((p, v.types, bool(v.bad), v.objects,
                     tuple(sorted((field, fv.types, bool(fv.bad), fv.objects) for field, fv in actual_fields[p].items())))
                     for p, v in actual.items()))
        substitutions = {}
        for p, result in actual.items():
            marker = ("parameter", module.name, name, p)
            substitutions[marker] = result
            env[p] = value(*result.types, origins={marker}, bad={marker} if result.bad else (), objects=result.objects,
                           refs={marker} if result.objects else ())
        # Field provenance is not the union of every constructor argument.
        # Abstract each known field independently and include its type/rounding
        # shape in the cache key, so a position cannot taint an exact normal.
        for p, fields in actual_fields.items():
            parameter_ref = ("parameter", module.name, name, p)
            self.record_fields[parameter_ref] = {}
            for field, result in fields.items():
                marker = ("parameter-field", module.name, name, p, field)
                substitutions[marker] = result
                self.record_fields[parameter_ref][field] = value(*result.types, origins={marker},
                    bad={marker} if result.bad else (), objects=result.objects,
                    refs={marker} if result.objects else ())
        initial_parameters = {p: env[p] for p in actual}

        def instantiate(result):
            origins, bad, refs = set(), set(), set()
            for marker in result.origins:
                origins.update(substitutions[marker].origins if marker in substitutions else {marker})
            for marker in result.bad:
                if marker in substitutions:
                    actual_value = substitutions[marker]
                    bad.update(actual_value.bad or actual_value.origins)
                else:
                    bad.add(marker)
            for marker in result.refs:
                refs.update(substitutions[marker].refs if marker in substitutions else {marker})
            return value(*result.types, origins=origins, bad=bad, objects=result.objects, refs=refs)

        if signature in self.cache:
            result, effects, mutations, unproved, field_mutations = self.cache[signature]
            instantiated = [(instantiate(affected), sink_module, sink_node) for affected, sink_module, sink_node in effects]
            for affected, sink_module, sink_node in instantiated:
                self._sink(affected, sink_module, sink_node)
            self.last_function_effects = instantiated
            self.last_mutations = {p: instantiate(v) for p, v in mutations.items()}
            self.last_field_mutations = {(p, field): instantiate(v) for (p, field), v in field_mutations.items()}
            self.last_unproved_effects = unproved
            if self.unproved_effects:
                self.unproved_effects[-1].update(unproved)
            return instantiate(result)
        recursion = (module.name, name)
        if recursion in self.active:
            # Recursive numerical transfer is not silently assumed exact.
            self.last_function_effects = []
            self.last_mutations = {}
            self.last_field_mutations = {}
            self.last_unproved_effects = {(module.name, name, "recursive-transfer")}
            return join(*supplied, *keywords.values(), value(UNKNOWN))
        self.active.add(recursion)
        self.sink_effects.append([])
        self.unproved_effects.append(set())
        self.field_write_effects.append({})
        returned = []
        self._block(module, name, node.body, env, returned)
        effects = list(dict.fromkeys(self.sink_effects.pop()))
        unproved = self.unproved_effects.pop()
        field_writes = self.field_write_effects.pop()
        self.active.remove(recursion)
        result = join(*returned) if returned else value(N)
        mutations = {p: env[p] for p in actual if env[p] != initial_parameters[p] and initial_parameters[p].objects}
        field_mutations = {(p, field): changed for p in actual for (ref, field), changed in field_writes.items() if ref in initial_parameters[p].refs}
        self.cache[signature] = result, effects, mutations, unproved, field_mutations
        instantiated = [(instantiate(affected), sink_module, sink_node) for affected, sink_module, sink_node in effects]
        for affected, sink_module, sink_node in instantiated:
            self._sink(affected, sink_module, sink_node)
        self.last_function_effects = instantiated
        self.last_mutations = {p: instantiate(v) for p, v in mutations.items()}
        self.last_field_mutations = {(p, field): instantiate(v) for (p, field), v in field_mutations.items()}
        self.last_unproved_effects = unproved
        if self.unproved_effects:
            self.unproved_effects[-1].update(unproved)
        return instantiate(result)

    def _block(self, module, scope, body, env, returned):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = scope + "." + node.name if scope else node.name
                for parameter, expression in self._default_nodes(node).items():
                    env["<default:" + name + ":" + parameter + ">"] = self._expr(module, scope, expression, env)
                continue
            if isinstance(node, (ast.ClassDef, ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Assign):
                result = self._expr(module, scope, node.value, env)
                if isinstance(node.value, (ast.Tuple, ast.List)) and len(node.targets) == 1 and isinstance(node.targets[0], (ast.Tuple, ast.List)) and len(node.targets[0].elts) == len(node.value.elts):
                    for target, expression in zip(node.targets[0].elts, node.value.elts):
                        self._assign(module, scope, target, self._expr(module, scope, expression, env), env)
                else:
                    for target in node.targets:
                        self._assign(module, scope, target, result, env)
            elif isinstance(node, ast.AnnAssign):
                result = self._expr(module, scope, node.value, env) if node.value is not None else self._annotation(module, node.annotation)
                self._assign(module, scope, node.target, result, env)
            elif isinstance(node, ast.AugAssign):
                result = self._arithmetic(module, node, self._expr(module, scope, node.target, env), self._expr(module, scope, node.value, env))
                self._assign(module, scope, node.target, result, env)
            elif isinstance(node, ast.Return):
                returned.append(self._expr(module, scope, node.value, env))
                break
            elif isinstance(node, (ast.Break, ast.Continue, ast.Raise)):
                # Stop this path: statements after a transfer do not overwrite
                # its numerical provenance.  Joining loop exits is conservative.
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.expr):
                        self._expr(module, scope, child, env)
                if isinstance(node, (ast.Break, ast.Continue)):
                    for owner, function, transfers in reversed(self.loop_transfers):
                        if owner is module and function == scope:
                            for name in set(transfers) | set(env):
                                transfers[name] = join(transfers.get(name, EMPTY), env.get(name, EMPTY))
                            break
                break
            elif isinstance(node, ast.If):
                condition = self._expr(module, scope, node.test, env)
                branches = []
                truth = self._truth(condition)
                candidates = (node.body,) if truth is True else (node.orelse,) if truth is False else (node.body, node.orelse)
                for branch in candidates:
                    local = dict(env)
                    self._block(module, scope, branch, local, returned)
                    branches.append(local)
                for name in set().union(*(set(branch) for branch in branches)):
                    env[name] = join(*(branch.get(name, EMPTY) for branch in branches))
            elif isinstance(node, (ast.For, ast.While)):
                before = dict(env)
                transfers = {}
                self.loop_transfers.append((module, scope, transfers))
                if isinstance(node, ast.For):
                    self._bind(node.target, self._expr(module, scope, node.iter, env), env)
                else:
                    self._expr(module, scope, node.test, env)
                # Monotone iteration over a finite source-key/type domain.
                while True:
                    previous = dict(env)
                    self._block(module, scope, node.body, env, returned)
                    for name in set(before) | set(env) | set(transfers):
                        env[name] = join(before.get(name, EMPTY), previous.get(name, EMPTY), env.get(name, EMPTY), transfers.get(name, EMPTY))
                    if env == previous:
                        break
                self.loop_transfers.pop()
                # The else arm is skipped by a break. Retain the exit state as
                # well as its else-updated copy; never wash taint on that edge.
                otherwise = dict(env)
                self._block(module, scope, node.orelse, otherwise, returned)
                for name in set(env) | set(otherwise):
                    env[name] = join(env.get(name, EMPTY), otherwise.get(name, EMPTY))
            elif isinstance(node, (ast.Try, ast.With)):
                if isinstance(node, ast.With):
                    context_proved = True
                    for item in node.items:
                        result = self._expr(module, scope, item.context_expr, env)
                        context_proved = context_proved and bool(result.objects & {"stdlib:file", "pytest:assertion"})
                        if item.optional_vars:
                            self._bind(item.optional_vars, result, env)
                    if module is self.main:
                        self.contexts[key(node)] = self.contexts.get(key(node), True) and context_proved
                    if not context_proved and self.unproved_effects:
                        self.unproved_effects[-1].add((module.name, scope, node.lineno, "unknown-context-protocol"))
                prefix = dict(env)
                self.exception_prefixes.append((module, scope, prefix))
                self._block(module, scope, node.body, env, returned)
                self.exception_prefixes.pop()
                normal = dict(env)
                self._block(module, scope, getattr(node, "orelse", ()), normal, returned)
                # __exit__ may suppress an exception at any statement prefix.
                # Unknown protocols are separately refused, not guessed pure.
                branches = [normal, prefix] if isinstance(node, ast.With) else [normal]
                for handler in getattr(node, "handlers", ()):
                    # An exception may occur before any later overwrite in the
                    # try body. Every prefix, not only the last one, can reach
                    # a handler. This summary deliberately over-approximates.
                    local = dict(prefix)
                    if handler.name:
                        local[handler.name] = value(UNKNOWN)
                    self._block(module, scope, handler.body, local, returned)
                    branches.append(local)
                for name in set().union(*(set(branch) for branch in branches)):
                    env[name] = join(*(branch.get(name, EMPTY) for branch in branches))
                self._block(module, scope, getattr(node, "finalbody", ()), env, returned)
            else:
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.expr):
                        self._expr(module, scope, child, env)
            for owner, function, prefix in self.exception_prefixes:
                if owner is module and function == scope:
                    for name in set(prefix) | set(env):
                        prefix[name] = join(prefix.get(name, EMPTY), env.get(name, EMPTY))

    def _arithmetic(self, module, node, left, right):
        combined = join(left, right)
        types = combined.types
        exact = bool(types) and types <= {I, Q, B}
        if isinstance(node.op, ast.Div):
            exact = exact and Q in types
        if isinstance(node.op, ast.Pow):
            exponent = getattr(node, "right", getattr(node, "value", None))
            # A non-integral power can be a root even when the exponent is
            # computed (1/2), not the spelling ``** 0.5``.  The four ordinary
            # float arithmetic operations are not a permit to hide this sink.
            if not right.types or not right.types <= {I, B}:
                if module is self.main:
                    self.power_sinks.add(key(node))
                self._sink(left, module, node)
            exact = exact and ((left.types <= {Q, I, B} and Q in left.types and right.types <= {I, B}) or
                              isinstance(exponent, ast.Constant) and type(exponent.value) is int and exponent.value >= 0)
        if isinstance(node.op, ast.Div) and "pathlib.Path" in left.objects:
            return self._record(module, node, value(origins=combined.origins, bad=combined.bad, objects={"pathlib.Path"}, refs=left.refs))
        sequence_nodes = (ast.List, ast.Tuple, ast.ListComp)
        if isinstance(node, ast.BinOp) and ((isinstance(node.op, ast.Add) and isinstance(node.left, sequence_nodes) and isinstance(node.right, sequence_nodes)) or
                isinstance(node.op, ast.Mult) and (isinstance(node.left, sequence_nodes) and right.types <= {I, B} or isinstance(node.right, sequence_nodes) and left.types <= {I, B})):
            return self._record(module, node, combined)
        # Concatenating sequence slices changes no scalar representation.
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) and all(isinstance(part, ast.Subscript) and isinstance(part.slice, ast.Slice) for part in (node.left, node.right)):
            return self._record(module, node, combined)
        bad = combined.bad
        if not exact and not types <= {S, N}:
            bad = bad | ({key(node)} if module is self.main else combined.origins or {("external-arithmetic", module.name, node.lineno)})
        result_type = Q if exact and Q in types else I if exact else S if types <= {S} else F
        return self._record(module, node, value(result_type, origins=combined.origins, bad=bad))

    def _expr(self, module, scope, node, env):
        if node is None:
            return value(N)
        if isinstance(node, ast.Constant):
            typ = {int: I, float: F, bool: B, str: S, bytes: S, type(None): N}.get(type(node.value), UNKNOWN)
            return self._record(module, node, value(typ, objects={"literal:" + str(node.value)} if type(node.value) is bool else ()))
        if isinstance(node, ast.Name):
            result = env.get(node.id, value(INPUT))
            if node.id not in env:
                name, shadowed = self._bound_name(module, scope, node.id, env)
                source = self._source_value(name) if name and not shadowed else None
                if source is not None:
                    result = source
                    if module is self.main and (self._data_value(source) or self._module_value(source)):
                        self.references.add(key(node))
            if module is self.main and node.id in env:
                self.references.add(key(node))
            return self._record(module, node, result)
        if isinstance(node, ast.BinOp):
            return self._arithmetic(module, node, self._expr(module, scope, node.left, env), self._expr(module, scope, node.right, env))
        if isinstance(node, ast.UnaryOp):
            result = self._expr(module, scope, node.operand, env)
            truth = self._truth(result)
            negated = value(B, objects={"literal:" + str(not truth)} if truth is not None else ())
            return self._record(module, node, negated if isinstance(node.op, ast.Not) else result)
        if isinstance(node, ast.Compare):
            left = self._expr(module, scope, node.left, env)
            for child in node.comparators:
                self._expr(module, scope, child, env)
            truth = None
            if len(node.ops) == 1 and isinstance(node.ops[0], (ast.Is, ast.IsNot)):
                name, shadowed = self._bound_name(module, scope, dotted(node.comparators[0]), env)
                builtin_type = {"float": F, "int": I, "bool": B, "str": S}.get(name)
                tags = {item for item in left.objects if item.startswith("type:")}
                if not shadowed and builtin_type is not None and tags:
                    wanted = "type:" + str(builtin_type)
                    truth = True if tags == {wanted} else False if wanted not in tags else None
                    if truth is not None and isinstance(node.ops[0], ast.IsNot):
                        truth = not truth
                    if module is self.main:
                        self.references.add(key(node.comparators[0]))
            return self._record(module, node, value(B, objects={"literal:" + str(truth)} if truth is not None else ()))
        if isinstance(node, ast.BoolOp):
            return self._record(module, node, join(*(self._expr(module, scope, child, env) for child in node.values)))
        if isinstance(node, ast.IfExp):
            self._expr(module, scope, node.test, env)
            return self._record(module, node, join(self._expr(module, scope, node.body, env), self._expr(module, scope, node.orelse, env)))
        if isinstance(node, ast.NamedExpr):
            result = self._expr(module, scope, node.value, env)
            self._bind(node.target, result, env)
            return self._record(module, node, result)
        if isinstance(node, (ast.Tuple, ast.List, ast.Set, ast.Dict)):
            children = [*node.keys, *node.values] if isinstance(node, ast.Dict) else node.elts
            contents = [self._expr(module, scope, child, env) for child in children if child is not None]
            nonempty = any(not isinstance(child, ast.Starred) for child in children if child is not None) or any("sequence:nonempty" in part.objects for part in contents)
            result = join(*contents, value(objects={"container:" + type(node).__name__.lower()} | ({"sequence:nonempty"} if nonempty else set()), refs={("allocation", module.name, node.lineno, node.col_offset)}))
            if module is self.main:
                self.allocations.add(key(node))
            return self._record(module, node, result)
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            local = dict(env)
            nonempty = True
            for generator in node.generators:
                sequence = self._expr(module, scope, generator.iter, local)
                nonempty = nonempty and not generator.ifs and "sequence:nonempty" in sequence.objects
                self._bind(generator.target, sequence, local)
                for condition in generator.ifs:
                    self._expr(module, scope, condition, local)
            children = [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
            result = join(*(self._expr(module, scope, child, local) for child in children), value(objects={"container:generator"} | ({"sequence:nonempty"} if nonempty else set()), refs={("allocation", module.name, node.lineno, node.col_offset)}))
            return self._record(module, node, result)
        if isinstance(node, ast.Subscript):
            result = self._expr(module, scope, node.value, env)
            self._expr(module, scope, node.slice, env)
            return self._record(module, node, result)
        if isinstance(node, ast.Attribute):
            owner = self._expr(module, scope, node.value, env)
            results = []
            # A property descriptor takes precedence over an annotated/stored
            # field of the same spelling, just as it does at runtime.
            for obj in owner.objects:
                cls_module, cls = self._definition(obj)
                if cls_module is not None and cls in cls_module.classes:
                    method_owner, method = self._method(cls_module, cls, node.attr)
                    if method_owner is not None and any(dotted(d) == "property" for d in method_owner.definitions[method].decorator_list):
                        results.append(self._invoke(module, scope, node, env, method_owner, method, [owner], {}, [node.value]))
            if results:
                if module is self.main:
                    self.attributes.add(key(node))
                return self._record(module, node, join(*results))
            stored = [self.record_fields[ref][node.attr] for ref in owner.refs if node.attr in self.record_fields.get(ref, {})]
            if stored:
                if module is self.main:
                    self.attributes.add(key(node))
                return self._record(module, node, join(*stored, value(origins=owner.origins, bad=owner.bad)))
            if node.attr in {"numerator", "denominator"} and owner.types <= {I, Q, B}:
                results.append(value(I, origins=owner.origins, bad=owner.bad))
            for obj in owner.objects:
                cls_module, cls = self._definition(obj)
                if cls_module is not None and cls in cls_module.classes:
                    for member in cls_module.classes[cls].body:
                        if isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name) and member.target.id == node.attr:
                            default = self.class_defaults.get((cls_module.name, cls, member.target.id))
                            typed = self._annotation(cls_module, member.annotation)
                            # dataclasses.field(...) is metadata, not the field
                            # value; ordinary initializers, however, are real
                            # evaluated values and annotations cannot unround it.
                            if default is not None and default.types != {N}:
                                typed = default
                            results.append(join(typed, value(origins=owner.origins, bad=owner.bad)))
            qualified, shadowed = self._bound_name(module, scope, dotted(node), env)
            if qualified in {"math.inf", "math.nan", "math.pi", "math.e", "math.tau"}:
                results.append(value(F))
            imported = self._source_value(qualified) if qualified and not shadowed else None
            if imported is not None and (self._data_value(imported) or self._module_value(imported)):
                results.append(imported)
                if module is self.main:
                    self.references.add(key(node))
            if results:
                if module is self.main:
                    self.attributes.add(key(node))
                return self._record(module, node, join(*results))
            return self._record(module, node, join(owner, value(UNKNOWN)))
        if isinstance(node, ast.Call):
            return self._call(module, scope, node, env)
        if isinstance(node, (ast.JoinedStr, ast.FormattedValue)):
            children = [self._expr(module, scope, child, env) for child in ast.iter_child_nodes(node) if isinstance(child, ast.expr)]
            result = join(*children)
            return self._record(module, node, value(S, origins=result.origins, bad=result.bad | ({key(node)} if module is self.main else result.origins)))
        if isinstance(node, ast.Starred):
            return self._expr(module, scope, node.value, env)
        return self._record(module, node, value(UNKNOWN))

    @staticmethod
    def _truth(result):
        markers = result.objects & {"literal:True", "literal:False"}
        if result.types <= {B} and len(markers) == 1:
            return "literal:True" in markers
        return None

    def _call(self, module, scope, node, env):
        args = [self._expr(module, scope, item, env) for item in node.args]
        keywords = {item.arg: self._expr(module, scope, item.value, env) for item in node.keywords}
        combined = join(*args, *keywords.values())
        spelling = dotted(node.func)
        name, shadowed = self._bound_name(module, scope, spelling, env)
        defined_owner, defined_target = self._definition(name)
        if defined_owner is not None:
            name = defined_owner.name + "." + defined_target
        leaf = name.rsplit(".", 1)[-1]
        kind, result = "unknown", join(combined, value(UNKNOWN))
        if leaf in DYNAMIC or isinstance(node.func, (ast.Call, ast.Subscript, ast.Lambda)):
            kind = "dynamic"
        elif not shadowed and leaf in CONSTRUCTION and (name.startswith("eab.construction.") or name in CONSTRUCTION):
            # The scan_text API and the legacy pass also recognize bare
            # construction intrinsics in injected snippets. Resolve them here
            # too, or an unknown attribute can be mistaken for an off-sink
            # data read. A lexical binding still shadows this finite vocabulary.
            kind = "construction"
            if leaf in SINKS:
                self._sink(combined, module, node)
            result = value(F, origins=combined.origins, bad=combined.bad | ({key(node)} if module is self.main else combined.origins))
        elif not shadowed and name in {"Fraction", "fractions.Fraction", "fractions.Fraction.from_float"}:
            kind, result = "pure", value(Q, origins=combined.origins, bad=combined.bad)
        elif not shadowed and name in {"int", "builtins.int"}:
            kind, result = "pure", value(I, origins=combined.origins, bad=combined.bad)
        elif not shadowed and name in {"float", "builtins.float"}:
            kind, result = "pure", value(F, origins=combined.origins, bad=combined.bad | ({key(node)} if module is self.main else combined.origins))
        elif not shadowed and name in SCALAR_PURE:
            numeric = join(*args, *(v for k, v in keywords.items() if k != "key"))
            kind, result = "pure", numeric
            if name == "sum" and not combined.types <= {I, Q, B}:
                result = join(result, value(F, bad={key(node)} if module is self.main else combined.origins))
        elif not shadowed and name in CONTAINERS:
            numeric = join(*args, *(v for k, v in keywords.items() if k not in {"key", "reverse"}))
            kind, result = "pure", join(numeric, value(I) if name in {"range", "enumerate"} else EMPTY, value(objects={"container:" + name}, refs={("allocation", module.name, node.lineno, node.col_offset)}))
        elif not shadowed and name in DISCRETE | EXCEPTIONS:
            kind, result = "pure", value(I if name in {"len", "hash", "id", "ord"} else B)
            if name in {"all", "any"} and len(args) == 1:
                truth = self._truth(args[0])
                # all(True) / any(False) are valid even for empty iterables;
                # the opposite answers additionally require nonemptiness.
                if truth is not None and ("sequence:nonempty" in args[0].objects or truth == (name == "all")):
                    result = value(B, objects={"literal:" + str(truth)})
        elif not shadowed and name == "type" and len(args) == 1 and not keywords:
            types = args[0].types
            kind, result = "pure", value(N, objects={"type:" + str(t) for t in types} if types and types <= {I, Q, F, B, S, N} else ())
        elif not shadowed and name == "next":
            kind, result = "pure", combined
        elif not shadowed and name == "dict.fromkeys":
            kind, result = "pure", join(combined, value(objects={"container:dict"}, refs={("allocation", module.name, node.lineno, node.col_offset)}))
        elif not shadowed and name in {"str", "repr", "bytes"}:
            kind, result = "pure", value(S, origins=combined.origins, bad=combined.bad)
        elif name.startswith("math.") and leaf in MATH_INT | MATH_BOOL | MATH_FLOAT:
            kind = "pure"
            if leaf in {"sqrt", "hypot", "dist"}:
                self._sink(combined, module, node)
            elif leaf == "pow" and len(args) > 1 and (not args[1].types or not args[1].types <= {I, B}):
                if module is self.main:
                    self.power_sinks.add(key(node))
                self._sink(args[0], module, node)
            result = value(I if leaf in MATH_INT else B if leaf in MATH_BOOL else F,
                           origins=combined.origins if leaf not in MATH_BOOL else (),
                           bad=combined.bad if leaf not in MATH_BOOL else ())
            if leaf in MATH_FLOAT:
                result = join(result, value(bad={key(node)} if module is self.main else combined.origins))
        elif name in {"dataclasses.dataclass", "dataclasses.field", "functools.lru_cache", "functools.cache"}:
            kind, result = "pure", value(N)
        elif name in {"dataclasses.asdict", "dataclasses.astuple", "dataclasses.replace", "dataclasses.fields"}:
            kind, result = "pure", join(combined, value(objects={"container:tuple" if name.endswith(("astuple", "fields")) else "container:dict"}))
        elif name == "dataclasses.is_dataclass":
            kind, result = "pure", value(B)
        elif name in {"pathlib.Path", "pathlib.PurePath", "pathlib.PosixPath", "pathlib.WindowsPath"}:
            kind, result = "record", value(S, origins=combined.origins, bad=combined.bad, objects={"pathlib.Path"}, refs={("allocation", module.name, node.lineno, node.col_offset)})
        elif not shadowed and name == "open":
            kind, result = "record", value(objects={"stdlib:file"}, refs={("allocation", module.name, node.lineno, node.col_offset)})
        elif name in {"json.load", "json.loads"}:
            kind, result = "pure", value(INPUT, origins=combined.origins, bad=combined.bad, objects={"container:json"})
        elif name in {"json.dump", "json.dumps"}:
            kind, result = "pure", value(S, origins=combined.origins, bad=combined.bad)
        elif name in {"csv.DictReader", "csv.reader"}:
            kind, result = "pure", value(S, origins=combined.origins, bad=combined.bad, objects={"container:csv"})
        elif name in {"collections.Counter", "collections.defaultdict", "collections.OrderedDict", "collections.deque"}:
            kind, result = "pure", join(combined, value(objects={"container:dict"}, refs={("allocation", module.name, node.lineno, node.col_offset)}))
        elif name == "random.Random":
            kind, result = "record", value(objects={"random.Random"}, refs={("allocation", module.name, node.lineno, node.col_offset)})
        elif name in {"pytest.approx", "pytest.raises", "pytest.fail"}:
            kind, result = "pure", join(combined, value(UNKNOWN, objects={"pytest:assertion"}))
        elif name in {"itertools.combinations", "itertools.combinations_with_replacement", "itertools.permutations", "itertools.product", "itertools.chain", "itertools.chain.from_iterable", "itertools.repeat"}:
            kind, result = "pure", join(combined, value(objects={"container:iterator"}))
        elif name == "itertools.count":
            if len(args) <= 2 and set(keywords) <= {"start", "step"} and combined.types <= {I, B}:
                kind, result = "pure", value(I, origins=combined.origins, bad=combined.bad, objects={"container:iterator"})
        elif name in {"struct.pack", "struct.unpack"} and node.args:
            fmt = _struct_format(node.args[0])
            if fmt is not None and not keywords:
                arity, types, floating, narrow = fmt
                if name == "struct.pack" and len(args) == arity + 1:
                    payload = join(*args[1:])
                    converts = any(not args[index + 1].types <= {F} for index in floating)
                    rounding = bool(narrow) or converts
                    bad = payload.bad | (({key(node)} if module is self.main else payload.origins or {("external-struct-rounding", module.name, node.lineno)}) if rounding else set())
                    kind, result = "pure", value(S, origins=payload.origins, bad=bad)
                elif name == "struct.unpack" and len(args) == 2:
                    kind, result = "pure", value(*types, origins=args[1].origins, bad=args[1].bad, objects={"container:tuple"})
        else:
            owner, target = self._definition(name)
            if owner is not None and target in owner.definitions and not shadowed:
                kind = "defined"
                definition = owner.definitions[target]
                parameters = [*definition.args.posonlyargs, *definition.args.args]
                used = {n.id for n in ast.walk(definition) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
                if module is self.main:
                    for argument, parameter in zip(node.args, parameters):
                        if parameter.arg not in used and isinstance(argument, (ast.Name, ast.Attribute)):
                            self.references.add(key(argument))
                lexical = env if owner is module and "." in target and target.rsplit(".", 1)[0] not in owner.classes else None
                result = self._invoke(module, scope, node, env, owner, target, args, keywords,
                                      node.args, closure=lexical)
                if self.last_unproved_effects:
                    kind = "unknown"
            elif owner is not None and target in owner.classes and not shadowed:
                self._module_env(owner)
                cls = owner.classes[target]
                chain = self._class_chain(owner, target) or [(owner, target)]
                fields = {}
                for field_owner, field_class in reversed(chain):
                    for member in field_owner.classes[field_class].body:
                        if isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
                            fields[member.target.id] = (field_owner, field_class, member)
                stored = {}
                init_owner, initializer = self._method(owner, target, "__init__")
                generated_init = False
                # An undecorated subclass inherits a generated dataclass init
                # too. Stop at the nearest explicit or generated initializer.
                for class_owner, class_name in chain:
                    if class_name + ".__init__" in class_owner.definitions:
                        break
                    decorators = [d for d in class_owner.classes[class_name].decorator_list
                                  if self._qualified(class_owner, dotted(d.func if isinstance(d, ast.Call) else d)) == "dataclasses.dataclass"]
                    if decorators and not any(isinstance(d, ast.Call) and any(
                        item.arg == "init" and isinstance(item.value, ast.Constant) and item.value.value is False
                        for item in d.keywords) for d in decorators):
                        generated_init = True
                        init_owner, initializer = None, None
                        break
                dataclass = generated_init
                for index, (field_name, (field_owner, field_class, field)) in enumerate(fields.items()):
                    supplied = keywords.get(field_name)
                    if supplied is None and dataclass and index < len(args):
                        supplied = args[index]
                    if supplied is None:
                        supplied = self.class_defaults.get((field_owner.name, field_class, field_name), self._annotation(field_owner, field.annotation))
                        if isinstance(field.value, ast.Call) and self._qualified(field_owner, dotted(field.value.func)) == "dataclasses.field":
                            default = next((item.value for item in field.value.keywords if item.arg == "default"), None)
                            supplied = self._expr(field_owner, field_class, default, {}) if default is not None else self._annotation(field_owner, field.annotation)
                    stored[field_name] = supplied
                record_ref = ("record", module.name, node.lineno, node.col_offset,
                              tuple((field, item.types, bool(item.bad), item.objects) for field, item in stored.items()))
                self.record_fields[record_ref] = stored
                kind, result = "record", value(objects={name}, refs={record_ref})
                # A generated dataclass initializer supersedes an inherited one.
                own_init = target + ".__init__" in owner.definitions
                lifecycle = [(init_owner, initializer, [result, *args], keywords)] if init_owner is not None and (own_init or not generated_init) else []
                if generated_init and not own_init:
                    post_owner, post_init = self._method(owner, target, "__post_init__")
                    if post_owner is not None:
                        lifecycle.append((post_owner, post_init, [result], {}))
                for lifecycle_owner, method, supplied, named in lifecycle:
                    self._invoke(module, scope, node, env, lifecycle_owner, method, supplied, named)
                    definition = lifecycle_owner.definitions[method]
                    self_name = definition.args.args[0].arg if definition.args.args else "self"
                    result = join(result, self.last_mutations.get(self_name, EMPTY))
                    if self.last_unproved_effects:
                        kind = "unknown"
                if self._class_chain(owner, target) is None:
                    kind = "unknown"
                # These protocols can replace the instance or reinterpret a
                # field independently of its declaration.  They have no
                # first-order record summary here, so do not guess one.
                if any(self._method(owner, target, protocol)[0] is not None for protocol in
                       ("__new__", "__getattribute__", "__getattr__", "__setattr__", "__delattr__")):
                    kind = "unknown"
            elif isinstance(node.func, ast.Attribute):
                receiver = self._expr(module, scope, node.func.value, env)
                if node.func.attr in CONTAINER_METHODS and any(obj.startswith("container:") for obj in receiver.objects):
                    kind, result = "pure", join(receiver, combined)
                    if isinstance(node.func.value, ast.Name) and node.func.attr in {"append", "extend", "insert", "add", "update", "setdefault"}:
                        identities = receiver.refs
                        for local, old in list(env.items()):
                            if local == node.func.value.id or identities & old.refs:
                                env[local] = join(old, result)
                elif node.func.attr in TEXT_METHODS and receiver.types <= {S}:
                    kind, result = "pure", join(receiver, combined)
                elif "pathlib.Path" in receiver.objects and node.func.attr in {"read_text", "read_bytes", "as_posix", "__fspath__"}:
                    kind, result = "pure", value(S)
                elif "pathlib.Path" in receiver.objects and node.func.attr in {"is_file", "is_dir", "exists", "is_absolute", "is_relative_to"}:
                    kind, result = "pure", value(B)
                elif "pathlib.Path" in receiver.objects and node.func.attr in {"resolve", "absolute", "relative_to", "joinpath", "with_name", "with_suffix", "expanduser"}:
                    kind, result = "pure", receiver
                elif "pathlib.Path" in receiver.objects and node.func.attr == "open":
                    kind, result = "record", value(objects={"stdlib:file"}, refs={("allocation", module.name, node.lineno, node.col_offset)})
                elif "stdlib:file" in receiver.objects and node.func.attr in {"read", "readline", "readlines"}:
                    kind, result = "pure", value(S, objects={"container:list"} if node.func.attr == "readlines" else ())
                elif "stdlib:file" in receiver.objects and node.func.attr in {"write", "writelines", "close", "flush"}:
                    kind, result = "pure", value(I if node.func.attr == "write" else N)
                elif "random.Random" in receiver.objects and node.func.attr in {"random", "uniform", "gauss", "normalvariate", "triangular"}:
                    kind, result = "pure", value(F)
                elif "random.Random" in receiver.objects and node.func.attr in {"randint", "randrange", "getrandbits"}:
                    kind, result = "pure", value(I)
                elif "random.Random" in receiver.objects and node.func.attr in {"choice", "sample", "choices", "shuffle"}:
                    kind, result = "pure", combined
                elif node.func.attr == "bit_length" and receiver.types <= {I, B}:
                    kind, result = "pure", value(I)
                elif node.func.attr in {"as_integer_ratio"} and receiver.types <= {I, Q, F, B}:
                    kind, result = "pure", value(I, origins=receiver.origins, bad=receiver.bad, objects={"container:tuple"})
                else:
                    method_results = []
                    for obj in receiver.objects:
                        owner, cls = self._definition(obj)
                        if owner is not None and cls in owner.classes:
                            method_owner, method = self._method(owner, cls, node.func.attr)
                            if method_owner is not None:
                                method_results.append(self._invoke(module, scope, node, env, method_owner, method,
                                                                   [receiver, *args], keywords, [node.func.value, *node.args]))
                    if method_results:
                        kind, result = "unknown" if self.last_unproved_effects else "defined", join(*method_results)
        self._classify(module, node, kind)
        if kind in {"unknown", "dynamic"} and self.unproved_effects:
            self.unproved_effects[-1].add((module.name, scope, node.lineno, kind))
        return self._record(module, node, result)

    def call_kind(self, node):
        return self.kinds.get(key(node), "unknown")

    def import_proved(self, node):
        """Admit a resolved source import, not every call into that module."""
        if isinstance(node, ast.Import):
            return all(self._module(alias.name) is not None or alias.name == "math" for alias in node.names)
        if not isinstance(node, ast.ImportFrom) or any(alias.name == "*" for alias in node.names):
            return False
        package = self.main.name.split(".") if self.main.path.endswith("__init__.py") else self.main.name.split(".")[:-1]
        parent = ".".join(package[:len(package) - node.level + 1]) if node.level else ""
        name = ".".join(piece for piece in (parent, node.module or "") if piece)
        if name == "fractions":
            return all(alias.name == "Fraction" for alias in node.names)
        if name == "math":
            return all(alias.name in MATH_INT | MATH_BOOL | MATH_FLOAT | {"inf", "nan", "pi", "e", "tau"} for alias in node.names)
        module = self._module(name)
        if module is None:
            return False
        return all(alias.name in module.definitions or alias.name in module.classes or alias.name in module.imports or alias.name in module.globals
                   or self._module(name + "." + alias.name) is not None for alias in node.names)

    def call_proved(self, node):
        return self.call_kind(node) not in {"unknown", "dynamic"}

    def call_may_round(self, node):
        """Preserve derived return provenance in the mature caller CFG too."""
        return bool(self.values.get(key(node), EMPTY).bad)

    def context_proved(self, node):
        return self.contexts.get(key(node), False)

    def arithmetic_issue(self, node):
        return key(node) in self.hazards

    def may_round(self, node):
        """Whether a numeric operation lacks an exact int/Fraction proof.

        This is a transfer fact, not a violation: a caller with its own mature
        CFG/heap analysis may carry it until a forbidden construction sink.
        """
        if not isinstance(node, (ast.BinOp, ast.AugAssign)):
            return False
        result = self.values.get(key(node))
        return result is None or not result.types <= {I, Q, B, S, N}

    def reaches_sink(self, node):
        return key(node) in self.sink_nodes

    def sink_issue(self, node):
        return key(node) in self.sink_issues

    def power_sink(self, node):
        """A type fact only; the mature CFG must supply current operand taint."""
        return key(node) in self.power_sinks

    def sink_arguments(self, node):
        """Indices/keyword names whose source values reach a callee sink."""
        return frozenset(self.call_sink_arguments.get(key(node), ()))

    def attribute_proved(self, node):
        return key(node) in self.attributes

    def reference_proved(self, node):
        return key(node) in self.references

    def return_kind(self, node):
        types = self.values.get(key(node), value(UNKNOWN)).types
        return "exact" if types and types <= {I, Q, B} else "unknown" if UNKNOWN in types else "input" if INPUT in types else "float" if F in types else "data"


def analyze(text, path="<injected>", repository_root=None):
    return Analysis(text, path, repository_root)
