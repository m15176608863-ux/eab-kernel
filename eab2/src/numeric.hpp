#pragma once
#include "exact.hpp"
#include <array>
#include <cstdint>
#include <functional>
#include <stdexcept>
#include <string>
#include <vector>

namespace eab2::numeric {
using exact::Int;
using exact::Rational;

struct Error : std::runtime_error {
    std::uint32_t code;
    Error(std::uint32_t value, const std::string& message) : std::runtime_error(message), code(value) {}
};

// Values are binary64 bit patterns, not rounded intermediates reusable in exact recipes.
Rational decode_binary64(std::uint64_t bits);
Rational parse_rational(const std::string& text);
std::uint64_t parse_bits(const std::string& text);
std::uint64_t scalar_rational(const Rational& value, bool allow_underflow = false);
std::uint64_t scalar_algebraic(const std::function<int(const Rational&)>& compare, bool allow_underflow = false);
std::uint64_t ratio_rational(const Rational& numerator, const Rational& denominator, bool allow_underflow = false);
std::vector<std::uint64_t> vector_rational(const std::vector<Rational>& values, bool allow_underflow = false);
std::uint64_t sqrt_rational(const Rational& value, bool allow_underflow = false);
std::uint64_t norm_rational(const std::vector<Rational>& values, bool allow_underflow = false);
std::vector<std::uint64_t> unit_rational(const std::vector<Rational>& values, bool allow_underflow = false);
std::uint64_t normalized_difference_rational(const Rational& c, const Rational& nn,
                                           const Rational& offset, bool allow_underflow = false);

using Point2 = std::array<Rational, 2>;
int cross2_sign(const Point2& a, const Point2& b);
int orient2d(const Point2& a, const Point2& b, const Point2& c);
int dot_sign(const std::vector<Rational>& a, const std::vector<Rational>& b);
struct Aabb2 {
    Rational min_x, min_y, max_x, max_y;
    bool contains(const Point2& point) const;
    bool overlaps(const Aabb2& other) const;
};
Aabb2 exact_aabb2(const std::vector<Point2>& points);

// Test-only dispatcher used by the DLL test bridge; no product numeric ABI.
std::vector<std::uint64_t> evaluate(std::uint32_t operation, std::uint32_t encoding,
                                  const std::vector<std::string>& values, bool allow_underflow);
} // namespace eab2::numeric
