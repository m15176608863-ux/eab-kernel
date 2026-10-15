"""Test-only in-memory source mutation; no geometry and no disk writes.

This reflection/compile scaffolding is deliberately separate from the exact
numeric oracle helpers. The supplied replacement executes inside the genuine
SUT function, rather than modifying a returned result. The caller owns the
monkeypatch context and must check the named semantic red then restored green.
"""
import inspect
import textwrap


def mutate(monkeypatch, module, function, before, after):
    source = textwrap.dedent(inspect.getsource(function))
    assert source.count(before) == 1, 'unambiguous internal mutation site'
    namespace = dict(vars(module))
    exec(compile(source.replace(before, after), '<M3c internal section mutant>',
                 'exec'), namespace)
    monkeypatch.setattr(module, function.__name__, namespace[function.__name__])
