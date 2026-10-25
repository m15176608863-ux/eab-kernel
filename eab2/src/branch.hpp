#pragma once
#include "sensitivity.hpp"
#include <map>

namespace eab2::statics::branch_detail {
// Complete finite polynomials, never truncated series. Lexicographic order is
// epsilon first, eta second: 0 < epsilon << eta << 1.
struct Polynomial {
    std::map<std::pair<unsigned, unsigned>, Rational> terms;
    Polynomial() = default;
    Polynomial(const Rational& q) { if (q != Rational(0)) terms[{0, 0}] = q; }
    int sign() const { return terms.empty() ? 0 : terms.begin()->second.sign(); }
    bool zero() const { return terms.empty(); }
};
Polynomial operator+(Polynomial a, const Polynomial& b);
Polynomial operator-(Polynomial a, const Polynomial& b);
Polynomial operator-(const Polynomial& a);
Polynomial operator*(const Polynomial& a, const Polynomial& b);
Polynomial divide_exact(Polynomial a, const Polynomial& b);
SensitivityResult2 certified_threshold(const CriticalParameter2&, const LimitSeed2&,
    const SensitivityOptions2&, const SensitivityResult2& candidates);
} // namespace eab2::statics::branch_detail
