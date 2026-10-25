#pragma once
#include "critical.hpp"
#include <optional>
#include <memory>
#include <string>
#include <utility>
#include <variant>
#include <vector>

// Private exact directional sensitivity. No finite differences, rounded duals,
// or floating active-set decisions enter this layer.
namespace eab2::statics {
struct GeometrySeed2;
struct LimitSeed2 {
    Matrix dA;
    Vector db, dc;
    std::string parameter = "mu";
    // Raw affine primitive path, retained only internally. Matrix jets cannot
    // reconstruct the quadratic/cubic terms required by a branch certificate.
    std::shared_ptr<const GeometrySeed2> geometry_path;
};
using SensitivityLabel2 = std::variant<std::string, ColumnLabel2>;
using SensitivityPieceLabel2 = std::variant<std::string, ColumnLabel2, std::vector<std::size_t>>;
struct SensitivityOptions2 {
    std::string parameter = "mu";
    std::vector<SensitivityLabel2> tied_labels;
    std::vector<std::string> validity_conditions;
    bool positive_direction_valid = true, negative_direction_valid = true;
    opt::Options lp_options;
    // Test seam only (never set by the C ABI): makes the branch certifier
    // report a slope without ordered-field witnesses, so the certified-shape
    // invariant in certified_threshold() has a named gate of its own.
    bool test_witnessless_slope = false;
};
struct SensitivitySelectedPiece2 {
    std::vector<std::size_t> basis;
    // Absent kind means a stable-basis list. Present kind means the critical
    // certificate tuple (kind, basis, entering-or-null).
    std::optional<std::string> kind;
    std::optional<std::size_t> entering;
};
struct SensitivityPieceJacobian2 {
    SensitivityPieceLabel2 label;
    Rational derivative;
};
struct ImplicitComponent2 {
    SensitivityLabel2 label;
    Rational slope, partial_mu, partial_parameter;
    std::size_t index = 0;
};
struct SensitivityResult2 {
    std::string call_status = "OK";
    std::optional<std::string> mathematical_status;
    std::string differentiability = "unresolved";
    // Frozen Python wire semantics: exact arithmetic path, NOT evidence that
    // a non-null slope exists. Every non-null slope is separately certified.
    std::string quality = "exact_jet";
    std::optional<SensitivitySelectedPiece2> selected_piece;
    std::vector<SensitivityLabel2> tied_labels, near_labels;
    std::vector<SensitivityPieceJacobian2> piece_jacobians;
    std::optional<Rational> directional_derivative, left_derivative, right_derivative;
    std::optional<std::string> reason;
    std::vector<std::string> validity_conditions;
    std::string sensitivity_model = "ideal_exact_2d", parameter = "mu";
    std::optional<std::string> method;
    std::optional<Vector> primal_recession_ray, dual_recession_ray;
    std::optional<std::pair<Vector, Vector>> forward_certificate, reverse_certificate;
    std::string display_status = "NOT_APPLICABLE";
    std::vector<ImplicitComponent2> implicit_components;
    std::string branch_certificate = "null";
};

// The original maximization result supplies anchor-coordinate exact_y.
// With no explicit seed, only the unit friction direction is supported.
SensitivityResult2 evaluate_sensitivity2(const LimitResult2& result,
    const std::optional<LimitSeed2>& seed = std::nullopt,
    const SensitivityOptions2& options = {});
// Parameter seeds are formed at threshold_certificate.problem, including its
// exact rational mu. A bracket midpoint is never a replacement for that point.
SensitivityResult2 evaluate_sensitivity2(const CriticalParameter2& critical,
    const std::optional<LimitSeed2>& seed,
    const std::optional<LimitSeed2>& threshold_mu_seed = std::nullopt,
    const SensitivityOptions2& options = {});
std::string export_exact(const SensitivityResult2& result);
} // namespace eab2::statics
