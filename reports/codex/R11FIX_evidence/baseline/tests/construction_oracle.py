"""Test-owned reference construction API, shared with the G0 exact oracles.

The independent bit-pattern search and Fraction certificates live in a source
module only so the installed G0 entry points can use the same audited boundary.
They import no production constructor or geometric primitive.
"""
from eab.oracle_construction import (
    scalar_exact, ratio_exact, vector_exact, sqrt_exact, norm_exact, unit_exact,
    assert_sqrt_rounding,
)
