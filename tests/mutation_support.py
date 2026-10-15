"""Source-body mutation instrumentation, never a numerical oracle.

Proof domain: test-only extraction of an explicitly supplied Python function,
unique literal replacements, compilation in a COPY of its module globals, and
return of that function. No file is edited; production algorithms and numeric
expectations are outside this module. The static policy reviews this module
once, by exact file bytes and a closed list of instrumentation-only rules.
"""
import inspect
from textwrap import dedent


def mutated_function(function, module, replacements):
    """Return a genuinely altered function body; every anchor must be unique."""
    source = dedent(inspect.getsource(function))
    for decorator in ("@property\n", "@classmethod\n", "@staticmethod\n"):
        if source.startswith(decorator):
            source = source[len(decorator):]
    for before, after in replacements:
        assert source.count(before) == 1, "mutation anchor must be unique"
        source = source.replace(before, after, 1)
    namespace = dict(vars(module))
    exec(compile(source, "<internal source-body mutation>", "exec"), namespace)
    return namespace[function.__name__]


def mutated_callable(module, name, replacements):
    return mutated_function(getattr(module, name), module, replacements)


def replace_module_callable(monkeypatch, module, name, replacements):
    changed = mutated_callable(module, name, replacements)
    monkeypatch.setattr(module, name, changed)
    return changed
