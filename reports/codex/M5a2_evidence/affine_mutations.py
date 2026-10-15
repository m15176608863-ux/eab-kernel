"""Small internal-body mutation audit; no source-hash tripwire is invoked."""
from pathlib import Path
import importlib.util
import inspect
import json
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools"), str(ROOT / "tests")]
from eab.kernel2d import affine_motion as module
import test_m5a2_affine as gates


def mutant(function, old, new):
    source = textwrap.dedent(inspect.getsource(function))
    assert source.count(old) == 1
    namespace = dict(vars(module))
    exec(compile(source.replace(old, new), "<m5a2-internal-mutation>", "exec"), namespace)
    return namespace[function.__name__]


def main():
    records = []
    specs = (
        ("affine_fit_cross_sign", "fit", module.fit_affine,
         "row[0]*yy-row[1]*xy", "row[0]*yy+row[1]*xy",
         "affine endpoint independent normal-equation oracle"),
        ("positive_affine_residual_certified", "certificate", module.AffineFit.endpoint_certificate.fget,
         "self.delta == 0", "self.delta <= F(1, 2**52)",
         "positive residual must not receive endpoint-exact certificate"),
        ("residual_correction_sign", "correction", module.DDAAffineMotion.corrected_at,
         "value[k]+s*residual[k]", "value[k]-s*residual[k]",
         "corrected path exactly closes original snapshot endpoint"),
    )
    for name, kind, function, old, new, expected in specs:
        changed = mutant(function, old, new)
        original_fit = gates.fit_affine
        original_certificate = module.AffineFit.endpoint_certificate
        original_correction = module.DDAAffineMotion.corrected_at
        if kind == "correction":
            gate = gates.test_linear_residual_correction_closes_data_without_certification
        else:
            gate = lambda: gates.test_fit_matches_independent_three_point_and_normal_equation_oracles(gates.POINTS, True)
        gate()
        if kind == "fit":
            gates.fit_affine = changed
        elif kind == "certificate":
            module.AffineFit.endpoint_certificate = changed
        else:
            module.DDAAffineMotion.corrected_at = changed
        try:
            try:
                gate()
            except AssertionError as failure:
                assert str(failure) == expected, (name, "wrong red assertion", str(failure))
                records.append({"mutation": name, "result": "KILLED", "semantic_assertion": str(failure),
                                "injection": "compiled production function body before execution",
                                "source_hash_tripwire": "not invoked", "baseline": "PASS"})
            else:
                raise AssertionError(name+" survived")
        finally:
            gates.fit_affine = original_fit
            module.AffineFit.endpoint_certificate = original_certificate
            module.DDAAffineMotion.corrected_at = original_correction
    output = Path(__file__).with_name("affine_mutations.json")
    output.write_text(json.dumps({"complete": True, "records": records}, indent=2)+"\n", encoding="utf-8")
    print("3 internal affine mutations killed on their designated semantic assertion")


if __name__ == "__main__":
    main()
