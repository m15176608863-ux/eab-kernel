#include "numeric.hpp"
#include <algorithm>
#include <limits>

#if defined(_M_FP_FAST) || defined(__FAST_MATH__) || defined(_M_FP_CONTRACT)
#error Unsupported floating-point compilation mode
#endif
#pragma fp_contract(off)

namespace eab2::numeric {
namespace {
constexpr std::uint64_t negative_bit = UINT64_C(0x8000000000000000);
constexpr std::uint64_t maximum_bits = UINT64_C(0x7fefffffffffffff);
constexpr std::uint64_t fraction_mask = UINT64_C(0x000fffffffffffff);

std::int64_t floor_log2_ratio(const Int& numerator, const Int& denominator) {
    const auto nbits = numerator.bit_length(), dbits = denominator.bit_length();
    if (!nbits || !dbits) throw std::logic_error("floor log requires positive integers");
    if (nbits > static_cast<std::size_t>(INT64_MAX) || dbits > static_cast<std::size_t>(INT64_MAX))
        throw Error(5, "integer exponent exceeds implementation index range");
    std::int64_t exponent = static_cast<std::int64_t>(nbits) - static_cast<std::int64_t>(dbits);
    if ((exponent >= 0 && numerator < (denominator << static_cast<std::size_t>(exponent))) ||
        (exponent < 0 && (numerator << static_cast<std::size_t>(-exponent)) < denominator)) --exponent;
    return exponent;
}

std::uint64_t pack_quantum(const Int& significand, std::int64_t quantum, bool negative,
                          bool allow_underflow, const char* quantity) {
    const auto width = significand.bit_length();
    if (!width) {
        if (!allow_underflow) throw Error(4, std::string(quantity) + ": nonzero exact value is below binary64 output range");
        return negative ? negative_bit : 0;
    }
    const std::int64_t exponent = quantum + static_cast<std::int64_t>(width) - 1;
    if (exponent > 1023) throw Error(4, std::string(quantity) + ": exact value is outside finite binary64 range");
    const auto mantissa = significand.u64();
    std::uint64_t bits;
    if (exponent < -1022) {
        if (quantum != -1074) throw std::logic_error("unexpected subnormal quantum");
        bits = mantissa;
    } else {
        if (width > 54) throw std::logic_error("unexpected significand width");
        const auto normalized = width <= 53 ? mantissa << (53 - width) : mantissa >> (width - 53);
        bits = (static_cast<std::uint64_t>(exponent + 1023) << 52) | (normalized & fraction_mask);
    }
    return bits | (negative ? negative_bit : 0);
}

Rational squared_sum(const std::vector<Rational>& values) {
    Rational sum;
    for (const auto& value : values) sum = sum + value * value;
    return sum;
}

int compare_signed_root(const Rational& c, const Rational& nn, const Rational& r) {
    if (c.sign() >= 0 && r.sign() < 0) return 1;
    if (c.sign() < 0 && r.sign() >= 0) return -1;
    const int order = (c * c - r * r * nn).sign();
    return c.sign() < 0 ? -order : order;
}

bool canonical_integer(const std::string& text, bool positive) {
    if (text.empty()) return false;
    const std::size_t first = text[0] == '-' ? 1 : 0;
    if (first && positive) return false;
    if (first == text.size()) return false;
    if (text[first] == '0' && (text.size() - first != 1 || first || positive)) return false;
    for (std::size_t i = first; i < text.size(); ++i) if (text[i] < '0' || text[i] > '9') return false;
    return true;
}
} // namespace

Rational decode_binary64(std::uint64_t bits) {
    const auto exponent = (bits >> 52) & 0x7ff;
    if (exponent == 0x7ff) throw Error(1, "bits: nonfinite binary64 input");
    const auto fraction = bits & fraction_mask;
    if (!exponent && !fraction) return Rational(0);
    Int numerator(static_cast<std::int64_t>(fraction | (exponent ? UINT64_C(0x0010000000000000) : 0)));
    const int quantum = exponent ? static_cast<int>(exponent) - 1075 : -1074;
    if (bits & negative_bit) numerator = -numerator;
    return quantum >= 0 ? Rational(numerator << static_cast<std::size_t>(quantum))
                        : Rational(numerator, Int(1) << static_cast<std::size_t>(-quantum));
}

std::uint64_t parse_bits(const std::string& text) {
    if (text.size() != 16) throw Error(1, "bits: require exactly 16 lowercase hexadecimal digits");
    std::uint64_t bits = 0;
    for (const char digit : text) {
        if (!((digit >= '0' && digit <= '9') || (digit >= 'a' && digit <= 'f')))
            throw Error(1, "bits: require exactly 16 lowercase hexadecimal digits");
        bits = (bits << 4) | static_cast<std::uint64_t>(digit <= '9' ? digit - '0' : digit - 'a' + 10);
    }
    if (((bits >> 52) & 0x7ff) == 0x7ff) throw Error(1, "bits: nonfinite binary64 input");
    return bits;
}

Rational parse_rational(const std::string& text) {
    const auto slash = text.find('/');
    if (slash == std::string::npos || text.find('/', slash + 1) != std::string::npos)
        throw Error(1, "rational: require canonical reduced numerator/denominator");
    const auto n = text.substr(0, slash), d = text.substr(slash + 1);
    if (!canonical_integer(n, false) || !canonical_integer(d, true))
        throw Error(1, "rational: invalid canonical integer or nonpositive denominator");
    const Rational value(Int::decimal(n), Int::decimal(d));
    if (value.canonical() != text) throw Error(1, "rational: require reduced form and zero 0/1");
    return value;
}

std::uint64_t scalar_rational(const Rational& value, bool allow_underflow) {
    if (!value.sign()) return 0;
    Int numerator = exact::abs(value.numerator()), denominator = value.denominator();
    const auto exponent = floor_log2_ratio(numerator, denominator);
    if (exponent > 1023) throw Error(4, "scalar_rational: exact scalar is outside finite binary64 range");
    const auto quantum = std::max<std::int64_t>(exponent - 52, -1074);
    if (quantum >= 0) denominator = denominator << static_cast<std::size_t>(quantum);
    else numerator = numerator << static_cast<std::size_t>(-quantum);
    Int significand = numerator / denominator;
    const Int twice_remainder = (numerator % denominator) * Int(2);
    if (twice_remainder > denominator || (twice_remainder == denominator && significand.odd()))
        significand = significand + Int(1);
    return pack_quantum(significand, quantum, value.sign() < 0, allow_underflow, "scalar_rational");
}

std::uint64_t scalar_algebraic(const std::function<int(const Rational&)>& compare, bool allow_underflow) {
    const int sign = compare(Rational(0));
    if (!sign) return 0;
    if (sign < 0) {
        const auto positive = [&compare](const Rational& q) { return -compare(-q); };
        return scalar_algebraic(positive, allow_underflow) | negative_bit;
    }
    const auto maximum = decode_binary64(maximum_bits);
    if (compare(maximum) > 0) {
        const auto midpoint = (maximum + Rational(Int(1) << 1024)) / Rational(2);
        if (compare(midpoint) >= 0) throw Error(4, "scalar_algebraic: exact real exceeds finite binary64 range");
        return maximum_bits;
    }
    std::uint64_t lo = 0, hi = maximum_bits;
    while (lo < hi) {
        const auto middle = lo + (hi - lo + 1) / 2;
        if (compare(decode_binary64(middle)) >= 0) lo = middle;
        else hi = middle - 1;
    }
    const auto lower = decode_binary64(lo);
    if (!compare(lower)) return lo;
    const auto midpoint = (lower + decode_binary64(lo + 1)) / Rational(2);
    const int order = compare(midpoint);
    const auto result = order < 0 || (!order && !(lo & 1)) ? lo : lo + 1;
    if (!result && !allow_underflow) throw Error(4, "scalar_algebraic: nonzero exact real is below binary64 output range");
    return result;
}

std::uint64_t ratio_rational(const Rational& numerator, const Rational& denominator, bool allow_underflow) {
    if (!denominator.sign()) throw Error(1, "ratio_rational: zero denominator");
    return scalar_rational(numerator / denominator, allow_underflow);
}

std::vector<std::uint64_t> vector_rational(const std::vector<Rational>& values, bool allow_underflow) {
    std::vector<std::uint64_t> result;
    result.reserve(values.size());
    for (const auto& value : values) result.push_back(scalar_rational(value, allow_underflow));
    return result;
}

std::uint64_t sqrt_rational(const Rational& value, bool allow_underflow) {
    if (value.sign() < 0) throw Error(1, "sqrt_rational: square root of negative rational");
    if (!value.sign()) return 0;
    Int numerator = value.numerator(), denominator = value.denominator();
    const auto exponent = floor_log2_ratio(numerator, denominator);
    // Python // rounds negative odd exponents downward; C++ / would not.
    const auto root_exponent = exponent >= 0 ? exponent / 2 : -((-exponent + 1) / 2);
    if (root_exponent > 1023) throw Error(4, "sqrt_rational: exact root is outside finite binary64 range");
    const auto quantum = std::max<std::int64_t>(root_exponent - 52, -1074);
    if (quantum >= 0) denominator = denominator << static_cast<std::size_t>(2 * quantum);
    else numerator = numerator << static_cast<std::size_t>(-2 * quantum);
    Int lower = exact::isqrt(numerator / denominator);
    const Int midpoint = lower * Int(2) + Int(1);
    const int comparison = (numerator * Int(4) - denominator * midpoint * midpoint).sign();
    if (comparison > 0 || (!comparison && lower.odd())) lower = lower + Int(1);
    return pack_quantum(lower, quantum, false, allow_underflow, "sqrt_rational");
}

std::uint64_t norm_rational(const std::vector<Rational>& values, bool allow_underflow) {
    return sqrt_rational(squared_sum(values), allow_underflow);
}

std::vector<std::uint64_t> unit_rational(const std::vector<Rational>& values, bool allow_underflow) {
    const auto square = squared_sum(values);
    if (!square.sign()) throw Error(1, "unit_rational: unit of zero vector");
    std::vector<std::uint64_t> result;
    result.reserve(values.size());
    for (const auto& value : values) {
        auto component = sqrt_rational(value * value / square, allow_underflow);
        if (value.sign() < 0) component |= negative_bit;
        result.push_back(component);
    }
    return result;
}

std::uint64_t normalized_difference_rational(const Rational& c, const Rational& nn,
                                           const Rational& offset, bool allow_underflow) {
    if (nn.sign() <= 0) throw Error(1, "normalized_difference_rational: normal squared length must be positive");
    return scalar_algebraic([&](const Rational& q) { return compare_signed_root(c, nn, offset + q); }, allow_underflow);
}

int cross2_sign(const Point2& a, const Point2& b) {
    // Positive denominators allow a pure cpp_int numerator sign, with no floating filter.
    const Int positive = a[0].numerator() * b[1].numerator() * a[1].denominator() * b[0].denominator();
    const Int negative = a[1].numerator() * b[0].numerator() * a[0].denominator() * b[1].denominator();
    return (positive - negative).sign();
}
int orient2d(const Point2& a, const Point2& b, const Point2& c) {
    return cross2_sign({b[0] - a[0], b[1] - a[1]}, {c[0] - a[0], c[1] - a[1]});
}
int dot_sign(const std::vector<Rational>& a, const std::vector<Rational>& b) {
    if (a.empty() || a.size() != b.size()) throw Error(1, "dot: require equal nonempty dimensions");
    Int numerator(0), denominator(1);
    for (std::size_t i = 0; i < a.size(); ++i) {
        const Int term_numerator = a[i].numerator() * b[i].numerator();
        const Int term_denominator = a[i].denominator() * b[i].denominator();
        numerator = numerator * term_denominator + term_numerator * denominator;
        denominator = denominator * term_denominator;
    }
    return numerator.sign();
}

bool Aabb2::contains(const Point2& point) const {
    return min_x <= point[0] && point[0] <= max_x && min_y <= point[1] && point[1] <= max_y;
}
bool Aabb2::overlaps(const Aabb2& other) const {
    return min_x <= other.max_x && other.min_x <= max_x && min_y <= other.max_y && other.min_y <= max_y;
}
Aabb2 exact_aabb2(const std::vector<Point2>& points) {
    if (points.empty()) throw Error(1, "AABB: require nonempty points");
    Aabb2 result{points[0][0], points[0][1], points[0][0], points[0][1]};
    for (const auto& point : points) {
        result.min_x = std::min(result.min_x, point[0]); result.min_y = std::min(result.min_y, point[1]);
        result.max_x = std::max(result.max_x, point[0]); result.max_y = std::max(result.max_y, point[1]);
    }
    return result;
}

std::vector<std::uint64_t> evaluate(std::uint32_t operation, std::uint32_t encoding,
                                  const std::vector<std::string>& texts, bool allow_underflow) {
    if (operation < 1 || operation > 14) throw Error(3, "numeric operation is unsupported");
    if (encoding != 1 && encoding != 2) throw Error(1, "numeric input encoding is invalid");
    std::vector<Rational> values;
    values.reserve(texts.size());
    for (const auto& text : texts) values.push_back(encoding == 1 ? decode_binary64(parse_bits(text)) : parse_rational(text));
    const auto require = [&values](std::size_t count) {
        if (values.size() != count) throw Error(1, "numeric operation has incorrect value count");
    };
    switch (operation) {
    case 1: case 10: require(1); return {scalar_rational(values[0], allow_underflow)};
    case 2: require(1); return {scalar_algebraic([&](const Rational& q) { return (values[0] - q).sign(); }, allow_underflow)};
    case 3:
        require(1);
        if (values[0].sign() < 0) throw Error(1, "algebraic sqrt: negative radicand");
        return {scalar_algebraic([&](const Rational& q) { return q.sign() < 0 ? 1 : (values[0] - q * q).sign(); }, allow_underflow)};
    case 4: require(2); return {ratio_rational(values[0], values[1], allow_underflow)};
    case 5: return vector_rational(values, allow_underflow);
    case 6: require(1); return {sqrt_rational(values[0], allow_underflow)};
    case 7: return {norm_rational(values, allow_underflow)};
    case 8: return unit_rational(values, allow_underflow);
    case 9: require(3); return {normalized_difference_rational(values[0], values[1], values[2], allow_underflow)};
    case 11:
        require(6);
        return {scalar_rational(Rational(orient2d({values[0], values[1]}, {values[2], values[3]}, {values[4], values[5]})))};
    case 12:
        require(4);
        return {scalar_rational(Rational(cross2_sign({values[0], values[1]}, {values[2], values[3]})))};
    case 13: {
        if (values.empty() || values.size() % 2) throw Error(1, "dot: require two equal nonempty vectors");
        const auto half = values.begin() + values.size() / 2;
        return {scalar_rational(Rational(dot_sign({values.begin(), half}, {half, values.end()})))};
    }
    case 14: {
        if (values.empty() || values.size() % 2) throw Error(1, "AABB: require complete 2D points");
        std::vector<Point2> points;
        for (std::size_t i = 0; i < values.size(); i += 2) points.push_back({values[i], values[i + 1]});
        const auto box = exact_aabb2(points);
        return vector_rational({box.min_x, box.min_y, box.max_x, box.max_y}, allow_underflow);
    }
    default: throw Error(3, "numeric operation is unsupported");
    }
}
} // namespace eab2::numeric
