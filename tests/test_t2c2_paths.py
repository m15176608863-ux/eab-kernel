"""Windows path budget for the actual src/tests/tools repository-copy scope.

The oracle is source-AST extraction plus a live file-name inventory, not a
shortened sample path. A 150-character basetemp and 30 extra cache-name
characters are reserved even though this work order disables bytecode writes.
This is a byte-copy test budget, not a claim of fresh Git-tree verification.
"""
import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
COPY_SCOPE = ("src", "tests", "tools")
COPY_TESTS = (
    ("tests/test_r12fixb_maintenance.py",
     "test_unrelated_source_comment_keeps_real_repository_gate_green"),
    ("tests/test_r12fix_static_closed.py",
     "test_l01_full_repository_copy_rejects_real_map_implant_and_changed_dependency"),
    ("tests/test_r13fix_static_lifecycle.py",
     "test_repository_scan_rejects_all_three_new_lifecycle_sources_without_waivers"),
)
BASE_TEMP_CHARACTERS = 150
CACHE_NAME_ALLOWANCE = 30
WINDOWS_PATH_LIMIT = 260


def _check_budget(prefix, relative_paths):
    _, longest = max((len(path), path) for path in relative_paths)
    total = BASE_TEMP_CHARACTERS + len(prefix) + len(longest) + CACHE_NAME_ALLOWANCE
    assert total < WINDOWS_PATH_LIMIT, ("Windows repository-copy path budget", total, prefix, longest)
    return total


def test_t2c2_repository_copy_paths_fit_150_character_basetemp_with_cache_reserve():
    def _copy_prefix(source, function_name):
        function = next(node for node in ast.parse(source).body
                        if isinstance(node, ast.FunctionDef) and node.name == function_name)
        assert "tmp_path_factory" in [arg.arg for arg in function.args.args]
        assignments = {target.id: node.value for node in ast.walk(function)
                       if isinstance(node, ast.Assign) for target in node.targets
                       if isinstance(target, ast.Name)}
        creation = assignments["tmp_path"]
        assert isinstance(creation, ast.Call) and isinstance(creation.func, ast.Attribute)
        assert ast.unparse(creation.func) == "tmp_path_factory.mktemp"
        assert len(creation.args) == 1 and not creation.keywords
        assert isinstance(creation.args[0], ast.Constant) and type(creation.args[0].value) is str
        basename = creation.args[0].value
        assert basename and "/" not in basename and "\\" not in basename
        loops = [node for node in ast.walk(function) if isinstance(node, ast.For)
                 and isinstance(node.target, ast.Name) and node.target.id == "folder"]
        assert len(loops) == 1 and isinstance(loops[0].iter, ast.Tuple)
        assert tuple(node.value for node in loops[0].iter.elts) == COPY_SCOPE
        copies = [node for node in ast.walk(loops[0]) if isinstance(node, ast.Call)
                  and ast.unparse(node.func) == "shutil.copytree"]
        assert len(copies) == 1 and ast.unparse(copies[0].args[0]) == "ROOT / folder"
        destination = copies[0].args[1]
        assert isinstance(destination, ast.BinOp) and isinstance(destination.op, ast.Div)
        assert isinstance(destination.right, ast.Name) and destination.right.id == "folder"
        base = destination.left
        if isinstance(base, ast.Name) and base.id == "copy_root":
            base = assignments["copy_root"]
        suffix = ""
        if isinstance(base, ast.BinOp):
            assert isinstance(base.op, ast.Div) and isinstance(base.right, ast.Constant)
            assert type(base.right.value) is str
            suffix = "/" + base.right.value
            base = base.left
        assert isinstance(base, ast.Name) and base.id == "tmp_path"
        # Each distinct basename is requested once in these non-parametrized tests.
        # The fixture factory therefore allocates the first numbered directory, 0.
        assert not function.decorator_list
        return basename, "/" + basename + "0" + suffix + "/"

    # Include every actual file in the copied trees, not only Python or tracked
    # files. Existing caches, if any, are included as well as the extra reserve.
    paths = [path.relative_to(ROOT).as_posix() for folder in COPY_SCOPE
             for path in (ROOT / folder).rglob("*") if path.is_file()]
    assert paths and {path.split("/", 1)[0] for path in paths} == set(COPY_SCOPE)
    prefixes = [_copy_prefix((ROOT / path).read_text("utf-8"), name)
                for path, name in COPY_TESTS]
    assert len({name for name, _ in prefixes}) == len(prefixes)
    for _, prefix in prefixes:
        _check_budget(prefix, paths)

    # The same guard must reject an internally lengthened copy-prefix and file.
    path, name = COPY_TESTS[0]
    source = (ROOT / path).read_text("utf-8")
    mutant = source.replace('mktemp("r12b")',
                            'mktemp("repository_copy_prefix_that_exceeds_the_entire_windows_path_budget")')
    assert mutant != source
    _, prefix = _copy_prefix(mutant, name)
    with unittest.TestCase().assertRaisesRegex(AssertionError, "Windows repository-copy path budget"):
        _check_budget(prefix, ["tests/data/example.json"])
    _, prefix = _copy_prefix(source, name)
    with unittest.TestCase().assertRaisesRegex(AssertionError, "Windows repository-copy path budget"):
        _check_budget(prefix, ["tests/" + "x" * 80 + ".py"])
