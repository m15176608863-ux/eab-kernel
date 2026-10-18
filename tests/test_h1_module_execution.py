"""Declarative modules must execute during a fast test, not just collection."""
from h1_module_coverage import DECLARATIVE_MODULES, reload_declarative_modules


def test_declarative_modules_execute_in_fast_test():
    assert reload_declarative_modules() == DECLARATIVE_MODULES
