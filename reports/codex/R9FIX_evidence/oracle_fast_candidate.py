"""Scratch-only R9 oracle optimization; never writes source or tests.

Run: PYTHONDONTWRITEBYTECODE=1 python -X utf8 <this file>.
Decimal/float supply candidates only. Exact Fraction midpoint cells certify
every accepted candidate; ambiguous candidates use the unchanged bit search.
"""
from decimal import Decimal, DecimalException, localcontext
from fractions import Fraction as F
from pathlib import Path
import json
import math
import random
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from eab import oracle_construction as original
from test_r9fix_construction_rounding import _certificate, CELLS


SUCCESSOR_OF_MAX = F(2)**1024
BIT_SEARCH = original._round_positive.__wrapped__


def candidate(value, power):
    try:
        if power == 1:
            return float(value)
        with localcontext() as context:
            context.prec = 80
            return float((Decimal(value.numerator)/Decimal(value.denominator)).sqrt())
    except (OverflowError, ValueError, DecimalException):
        return None


def certified(value, power, result):
    if result is None or not math.isfinite(result) or result < 0:
        return False
    even = struct.unpack('>Q', struct.pack('>d', result))[0] % 2 == 0
    center = F(result)
    if result:
        lower = ((F(math.nextafter(result, 0.0))+center)/2)**power
        if value < lower or (value == lower and not even):
            return False
    upper_float = math.nextafter(result, math.inf)
    upper = ((center+(F(upper_float) if math.isfinite(upper_float)
                     else SUCCESSOR_OF_MAX))/2)**power
    return value < upper or (value == upper and even)


def proposed(value, power, allow_underflow, *, propose=candidate, counters=None):
    result = propose(value, power)
    if certified(value, power, result):
        if value and result == 0 and not allow_underflow:
            raise ArithmeticError('nonzero oracle construction is below binary64 output range')
        if counters is not None:
            counters['certified_fast'] += 1
        return result
    if counters is not None:
        counters['bit_fallback'] += 1
    return BIT_SEARCH(value, power, allow_underflow)


def outcome(function, value, power, allow=True, **kwargs):
    try:
        result = function(value, power, allow, **kwargs)
    except (ArithmeticError, ValueError) as error:
        return type(error).__name__
    _certificate(result, value, power)
    return result


def run():
    rng = random.Random(901207)
    cases = [(q, 1) for q in CELLS] + [(q*q, 2) for q in CELLS]
    cases += [(F(rng.getrandbits(127)+1, rng.getrandbits(121)+1)*F(2)**rng.randrange(-2300, 2200), power)
              for power in (1,2) for _ in range(2000)]
    # Make Decimal80 deliberately unable to resolve which side of a binary64
    # midpoint the root lies on. The exact certificate must reject its guess.
    for exponent in (-1074,-1022,-600,0,600,1023):
        lower = math.ldexp(1.,exponent)
        upper = math.nextafter(lower, math.inf)
        middle = (F(lower)+F(upper))/2
        epsilon = F(2)**(2*exponent-5000)
        cases += [(middle*middle+sign*epsilon,2) for sign in (-1,0,1)]
    counters = {'certified_fast': 0, 'bit_fallback': 0}
    for value,power in cases:
        expected = outcome(BIT_SEARCH,value,power)
        got = outcome(proposed,value,power,counters=counters)
        assert got == expected,(value,power,got,expected)
    forced = {'certified_fast': 0, 'bit_fallback': 0}
    for value,power in cases[:96]:
        expected = outcome(BIT_SEARCH,value,power)
        got = outcome(proposed,value,power,propose=lambda q,p:0.,counters=forced)
        assert got == expected
    # Explicitly retain the default underflow error contract as well.
    for power in (1,2):
        assert outcome(proposed,F(2)**(-1080*power),power,False) == 'ArithmeticError'
    times = {}
    # Benchmark common finite, non-midpoint Fraction outputs without any cache.
    workload = [(F(rng.getrandbits(112)+1,rng.getrandbits(100)+1)*F(2)**rng.randrange(-1200,1200),2)
                for _ in range(3000)]
    for name,function in [('unchanged_bit_search',BIT_SEARCH),('certified_candidate',proposed)]:
        started = time.perf_counter()
        results = [function(q,p,True) for q,p in workload]
        times[name] = time.perf_counter()-started
        assert len(results) == len(workload)
    return {'verification_cases':len(cases),'candidate_counts':counters,
            'forced_zero_candidate_counts':forced,'benchmark_cases':len(workload),
            'benchmark_seconds':times,
            'speedup':times['unchanged_bit_search']/times['certified_candidate'],
            'source_or_test_changes':False,
            'contract':'each fast answer has a Fraction RN-even midpoint certificate; failures fall back to unchanged reference bit search'}


if __name__ == '__main__':
    data=run()
    target=Path(__file__).with_suffix('.json')
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(data,ensure_ascii=False,indent=2))
