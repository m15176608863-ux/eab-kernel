#include "numeric.hpp"
#include <array>
#include <cstdint>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace eab2::numeric;
namespace {
std::size_t checks = 0;
constexpr std::uint64_t negative_mask = UINT64_C(0x8000000000000000);
constexpr std::uint64_t maximum = UINT64_C(0x7fefffffffffffff);

void check(bool condition, const char* name) {
    ++checks;
    if (!condition) throw std::runtime_error(name);
}
template <class F> void fails(std::uint32_t code, F action, const char* name) {
    ++checks;
    try { action(); }
    catch (const Error& error) { if (error.code == code) return; throw std::runtime_error(std::string(name) + ": wrong error code"); }
    throw std::runtime_error(std::string(name) + ": did not fail");
}
Rational power(int exponent) {
    return exponent >= 0 ? Rational(Int(1) << static_cast<std::size_t>(exponent))
                         : Rational(Int(1), Int(1) << static_cast<std::size_t>(-exponent));
}

void midpoint_matrix() {
    // Expected bits come from cell identity/parity, not the production rounder.
    const std::array<std::uint64_t, 12> anchors{
        0, 1, 2, UINT64_C(0x000fffffffffffff), UINT64_C(0x0010000000000000),
        UINT64_C(0x1a70000000000000), UINT64_C(0x3ff0000000000000), UINT64_C(0x3ff0000000000001),
        UINT64_C(0x3fdb6db6db6db6db), UINT64_C(0x6570000000000000), maximum - 1, maximum};
    for (const auto anchor : anchors) {
        const auto lower = decode_binary64(anchor);
        const auto upper = anchor == maximum ? power(1024) : decode_binary64(anchor + 1);
        const auto middle = (lower + upper) / Rational(2);
        const auto jitter = (upper - lower) / Rational(16);
        const std::array<Rational, 4> values{lower, middle - jitter, middle, middle + jitter};
        const std::array<std::uint64_t, 4> expected{anchor, anchor, anchor + (anchor & 1), anchor + 1};
        for (std::size_t i = 0; i < values.size(); ++i) {
            const auto& value = values[i];
            for (const int sign : {-1, 1}) {
                const auto signed_value = Rational(sign) * value;
                const auto comparator = [&](const Rational& q) { return (signed_value - q).sign(); };
                if (expected[i] > maximum) {
                    fails(4, [&] { scalar_rational(signed_value, true); }, "scalar overflow midpoint");
                    fails(4, [&] { scalar_algebraic(comparator, true); }, "algebraic overflow midpoint");
                    fails(4, [&] { ratio_rational(signed_value * Rational(7), Rational(7), true); }, "ratio overflow midpoint");
                } else {
                    const auto wanted = expected[i] | (sign < 0 && value.sign() ? negative_mask : 0);
                    check(scalar_rational(signed_value, true) == wanted, "scalar RN cell");
                    check(scalar_algebraic(comparator, true) == wanted, "algebraic rational RN cell");
                    check(ratio_rational(signed_value * Rational(7), Rational(7), true) == wanted, "ratio RN cell");
                }
            }
            const auto square = value * value;
            const auto root_compare = [&](const Rational& q) { return q.sign() < 0 ? 1 : (square - q * q).sign(); };
            if (expected[i] > maximum) {
                fails(4, [&] { sqrt_rational(square, true); }, "sqrt overflow midpoint");
                fails(4, [&] { scalar_algebraic(root_compare, true); }, "algebraic sqrt overflow midpoint");
            } else {
                check(sqrt_rational(square, true) == expected[i], "sqrt RN cell");
                check(scalar_algebraic(root_compare, true) == expected[i], "algebraic sqrt RN cell");
            }
        }
    }
    // Independent integer square midpoint certificate for non-square subnormal roots.
    for (std::int64_t m = 1; m <= 24; ++m) {
        const auto square = Rational(m * m) / Rational(3) * power(-2148);
        const auto result = sqrt_rational(square);
        const auto center = decode_binary64(result);
        const auto below = result ? (center + decode_binary64(result - 1)) / Rational(2) : Rational(0);
        const auto above = (center + decode_binary64(result + 1)) / Rational(2);
        check(square >= below * below && square <= above * above, "non-square subnormal midpoint certificate");
        check(square != below * below || !(result & 1), "non-square lower tie parity");
        check(square != above * above || !(result & 1), "non-square upper tie parity");
    }
}

void exact_and_construction() {
    check(Int(0).bit_length() == 0, "msb zero guarded");
    check(eab2::exact::isqrt(Int(0)) == Int(0), "isqrt zero");
    check(eab2::exact::isqrt(Int(15)) == Int(3) && eab2::exact::isqrt(Int(16)) == Int(4), "integer root bracket");
    const auto minimum = power(-1074);
    const auto max = decode_binary64(maximum);
    const std::array<std::uint64_t, 12> bits{0, negative_mask, 1, negative_mask | 1, UINT64_C(0x000fffffffffffff),
        UINT64_C(0x0010000000000000), UINT64_C(0x3ff0000000000000), UINT64_C(0xbff0000000000000),
        UINT64_C(0x3fd5555555555555), UINT64_C(0x7fe0000000000000), maximum, maximum | negative_mask};
    for (const auto b : bits) check(scalar_rational(decode_binary64(b)) == (b == negative_mask ? 0 : b), "lossless finite bits exact lift");
    check(decode_binary64(1) == minimum, "independent minsub formula");
    check(decode_binary64(negative_mask | 1).numerator() == Int(-1) &&
          decode_binary64(negative_mask | 1).denominator() == (Int(1) << 1074), "negative minsub numerator denominator");
    check(decode_binary64(UINT64_C(0x000fffffffffffff)).numerator() == ((Int(1) << 52) - Int(1)) &&
          decode_binary64(UINT64_C(0x000fffffffffffff)).denominator() == (Int(1) << 1074), "max subnormal numerator denominator");
    check(decode_binary64(UINT64_C(0x0010000000000000)).numerator() == Int(1) &&
          decode_binary64(UINT64_C(0x0010000000000000)).denominator() == (Int(1) << 1022), "min normal numerator denominator");
    check(decode_binary64(UINT64_C(0x3ff0000000000001)).numerator() == ((Int(1) << 52) + Int(1)) &&
          decode_binary64(UINT64_C(0x3ff0000000000001)).denominator() == (Int(1) << 52), "normal odd mantissa numerator denominator");
    check(decode_binary64(maximum).numerator() == (((Int(1) << 53) - Int(1)) << 971) &&
          decode_binary64(maximum).denominator() == Int(1), "max finite numerator denominator");
    check(decode_binary64(negative_mask).numerator() == Int(0) && decode_binary64(negative_mask).denominator() == Int(1), "negative zero exact canonical fraction");
    check(max == power(1024) - power(971), "independent maxfinite formula");
    check(scalar_rational(max + power(969)) == maximum, "upper finite overflow cell");
    fails(4, [&] { scalar_rational(power(1024) - power(970)); }, "exact overflow threshold");
    fails(4, [&] { scalar_rational(minimum / Rational(2)); }, "default underflow midpoint");
    check(scalar_rational(-minimum / Rational(2), true) == negative_mask, "negative allowed underflow zero");
    check(sqrt_rational(Rational(1) / Rational(2)) == UINT64_C(0x3fe6a09e667f3bcd), "negative odd sqrt exponent");
    fails(1, [&] { sqrt_rational(Rational(-1)); }, "negative root");
    fails(1, [&] { ratio_rational(Rational(1), Rational(0)); }, "zero denominator");
    fails(1, [&] { unit_rational({Rational(0), Rational(0)}); }, "zero unit");
    check(vector_rational({}).empty(), "empty vector");
    check(norm_rational({}) == 0, "empty norm");
    check(norm_rational({Rational(3), Rational(-4), Rational(12)}) == UINT64_C(0x402a000000000000), "norm 3 4 12");
    const auto direction = unit_rational({Rational(3), Rational(-4)});
    check(direction == std::vector<std::uint64_t>{UINT64_C(0x3fe3333333333333), UINT64_C(0xbfe999999999999a)}, "unit exact 3 4");
    const auto huge_direction = unit_rational({power(2000), -power(2000), power(926)}, true);
    check(huge_direction[0] == UINT64_C(0x3fe6a09e667f3bcd) && huge_direction[1] == UINT64_C(0xbfe6a09e667f3bcd), "unit overflowing unscaled norm");
    check(unit_rational({Rational(1), -power(-1076)}, true)[1] == negative_mask, "unit negative underflow zero");
    fails(4, [&] { unit_rational({Rational(1), power(-1076)}); }, "unit default tiny component failure");
    const auto big = power(1100);
    check(normalized_difference_rational(big, Rational(1), big - Rational(1)) == UINT64_C(0x3ff0000000000000), "difference finite after huge cancellation");
    check(normalized_difference_rational(-big, Rational(1), Rational(1) - big) == UINT64_C(0xbff0000000000000), "negative huge cancellation");
    check(normalized_difference_rational(max + power(969) + Rational(1), Rational(1), Rational(1)) == maximum, "difference overflow cell");
    fails(4, [&] { normalized_difference_rational(Rational(1) + power(-1076), Rational(1), Rational(1)); }, "difference default underflow");
    check(normalized_difference_rational(Rational(1), Rational(1), Rational(1) + power(-1076), true) == negative_mask, "difference signed zero underflow");
    check(normalized_difference_rational(Rational(-1), Rational(1), Rational(-1)) == 0, "difference exact zero positive sign");
    fails(1, [&] { normalized_difference_rational(Rational(1), Rational(0), Rational(0)); }, "difference positive nn");
    for (const int exponent : {70, 665}) {
        const auto m = power(exponent);
        const auto nn = m * m + Rational(1);
        const auto result = normalized_difference_rational(nn, nn, m);
        const auto value = decode_binary64(result);
        const auto lower = (value + decode_binary64(result - 1)) / Rational(2);
        const auto upper = (value + decode_binary64(result + 1)) / Rational(2);
        check((m + lower) * (m + lower) < nn && nn < (m + upper) * (m + upper), "irrational cancellation independent midpoint");
    }
}

void predicates_and_aabb() {
    const auto big = decode_binary64(maximum), tiny = power(-1074);
    check(orient2d({big, big}, {-big, -big}, {tiny, Rational(0)}) == 1, "orientation exact difference not rounded first");
    check(orient2d({Rational(0), Rational(0)}, {Rational(1), Rational(0)}, {Rational(0), Rational(1)}) == 1, "orientation positive standard");
    check(orient2d({Rational(0), Rational(0)}, {Rational(0), Rational(1)}, {Rational(1), Rational(0)}) == -1, "orientation negative standard");
    check(cross2_sign({big, big}, {big, big}) == 0, "overflowing cross cancellation");
    check(cross2_sign({tiny, Rational(0)}, {Rational(0), tiny}) == 1, "underflowing cross nonzero");
    check(dot_sign({big, big, tiny}, {big, -big, tiny}) == 1, "dot full cancellation and subnormal square");
    const auto gap = power(-1100);
    const auto box = exact_aabb2({{Rational(1), Rational(-2)}, {Rational(1) + gap, Rational(3)}});
    check(box.min_x == Rational(1) && box.max_x == Rational(1) + gap, "AABB retains non-display microfeature");
    check(box.contains({Rational(1) + gap, Rational(3)}), "AABB inclusive maximum");
    check(!box.contains({Rational(1) + gap * Rational(2), Rational(0)}), "AABB does not use rounded display bounds");
    const auto touching = exact_aabb2({{Rational(1) + gap, Rational(3)}, {Rational(2), Rational(4)}});
    check(box.overlaps(touching) && touching.overlaps(box), "AABB touching bounds included");
    const auto separated = exact_aabb2({{Rational(1) + gap * Rational(2), Rational(0)}});
    check(!box.overlaps(separated), "AABB exact separated microfeature");
}

void input_and_dispatch() {
    check(parse_rational("-13/17") == Rational(Int(-13), Int(17)), "canonical rational parse");
    for (const auto* invalid : {"1", "1/0", "1/-2", "2/4", "0/2", "-0/1", "+1/2", "01/2", "1/02", "1 /2", "1/2/3", "/1"})
        fails(1, [&] { parse_rational(invalid); }, "malformed canonical rational");
    for (const auto* invalid : {"0", "3FF0000000000000", "0x3ff0000000000000", "7ff0000000000000", "fff0000000000000", "7ff8000000000000", "zz00000000000000"})
        fails(1, [&] { parse_bits(invalid); }, "invalid finite bits");
    check(parse_bits("8000000000000000") == negative_mask, "negative zero input provenance bits");
    check(evaluate(10, 1, {"8000000000000000"}, false)[0] == 0, "negative zero exact roundtrip");
    check(evaluate(5, 2, {"1/1", "-1/1"}, false).size() == 2, "vector dispatcher");
    check(evaluate(13, 2, {"1/1", "2/1", "-1/1", "1/1"}, false)[0] == UINT64_C(0x3ff0000000000000), "dot dispatcher");
    check(evaluate(14, 2, {"1/1", "-2/1", "3/1", "4/1"}, false) ==
          std::vector<std::uint64_t>{UINT64_C(0x3ff0000000000000), UINT64_C(0xc000000000000000), UINT64_C(0x4008000000000000), UINT64_C(0x4010000000000000)}, "AABB dispatcher");
    fails(1, [&] { evaluate(1, 2, {}, false); }, "scalar dimension mismatch");
    fails(1, [&] { evaluate(13, 2, {"1/1"}, false); }, "dot dimension mismatch");
    fails(1, [&] { evaluate(14, 2, {}, false); }, "empty AABB rejected");
    fails(1, [&] { evaluate(1, 3, {"1/1"}, false); }, "invalid encoding");
    fails(3, [&] { evaluate(99, 2, {"1/1"}, false); }, "unsupported operation");
}
} // namespace

int main() {
    try {
        midpoint_matrix(); exact_and_construction(); predicates_and_aabb(); input_and_dispatch();
        std::cout << "EAB2_NUMERIC_TESTS checks=" << checks << " failed=0\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "EAB2_NUMERIC_TESTS checks=" << checks << " failed=1 detail=" << error.what() << '\n';
        return 1;
    }
}
