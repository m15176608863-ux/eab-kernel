#pragma once
#include "statics.hpp"
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace eab2::statics {
using Polynomial2 = Vector; // Rational coefficients, constant first.
using PolynomialMatrix2 = std::vector<std::vector<Polynomial2>>;

struct CriticalBasis2 {
    std::string kind;
    std::vector<std::size_t> basis;
    std::optional<std::size_t> entering;
    Polynomial2 determinant;
    std::vector<Polynomial2> numerators;
    std::vector<ColumnLabel2> labels;
    Rational sample_parameter;
    Vector sample_values;
};
struct BranchSign2 {
    // No index means the denominator; an index identifies a numerator.
    std::optional<std::size_t> index;
    std::array<std::size_t, 2> endpoint_orders{0, 0};
    Rational value;
};
using BranchSigns2 = std::vector<BranchSign2>;
struct ThresholdProof2 {
    Rational exact_threshold;
    bool attained = false;
    std::optional<CriticalBasis2> lower_basis, upper_basis;
    std::array<Rational, 2> lower_interval, upper_interval;
    std::optional<BranchSigns2> lower_signs, upper_signs;
    std::string reason = "exact_basis_continuation";
};
struct CriticalParameter2 {
    // Original search domain, never a narrowed bisection bracket.
    Rational original_mu_min{0};
    std::optional<Rational> original_mu_max;
    std::optional<std::uint64_t> original_mu_max_bits;
    std::string call_status = "OK", mathematical_status = "UNPROVED";
    // Rational storage, but every populated bracket endpoint is binary64 exact.
    std::optional<Rational> mu_lo, mu_hi;
    std::optional<bool> attained;
    std::optional<LimitResult2> lower_certificate, upper_certificate;
    std::optional<std::string> reason;
    std::optional<Rational> exact_threshold;
    std::vector<CriticalBasis2> critical_polynomials;
    std::size_t queries = 0;
    std::optional<LimitResult2> threshold_certificate;
    std::optional<ThresholdProof2> threshold_proof;
    std::optional<std::string> bisection_termination, threshold_proof_reason;
    std::vector<std::string> validity_conditions;
};

// Only friction is monotone. Exact rational threshold queries are separate
// from the binary64 bracket; width alone never proves attainment.
CriticalParameter2 critical_parameter(const contact::ContactSet2& contacts,
    const Loads2& loads, const Rational& mu_max = Rational(1),
    std::size_t max_steps = 64, const std::string& param = "mu",
    const opt::Options& options = {});
std::string export_exact(const CriticalParameter2& result);
std::string export_search_domain(const CriticalParameter2& result);

// Private proof helpers also exposed to the C++ semantic/adversarial gates.
namespace critical_detail {
bool is_binary64(const Rational& value);
std::optional<Rational> binary_midpoint(const Rational& lower, const Rational& upper);
PolynomialMatrix2 affine_matrix2(const LimitProblem2& zero, const LimitProblem2& one);
std::optional<CriticalBasis2> mechanism_basis2(const LimitResult2& result,
                                             const PolynomialMatrix2& matrix);
std::optional<CriticalBasis2> improving_basis2(const LimitResult2& result,
                                             const PolynomialMatrix2& matrix);
std::optional<BranchSigns2> branch_signs2(const std::optional<CriticalBasis2>& branch,
                                       const Rational& lower, const Rational& upper);
Rational rational_candidate2(const Rational& lower, const Rational& upper);
bool candidate_is_boundary2(const Rational& candidate,
    const std::optional<CriticalBasis2>& lower, const std::optional<CriticalBasis2>& upper);
} // namespace critical_detail
} // namespace eab2::statics
