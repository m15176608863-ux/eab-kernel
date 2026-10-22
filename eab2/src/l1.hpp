#pragma once
#include "geometry2.hpp"
#include "opt.hpp"
#include <array>
#include <optional>
#include <string>
#include <utility>
#include <vector>

// Private exact implementation types. No Boost type enters the public C ABI.
namespace eab2::contact {
using Rational = exact::Rational;
using Point = geometry2::Point;
using Polygon = geometry2::Polygon;
using Segment = geometry2::Segment;
using Vector = opt::Vector;
using Matrix = opt::Matrix;
using Dof = std::array<std::size_t, 2>;
using Dofs = std::vector<Dof>;

struct Body2 {
    std::string body_id;
    geometry2::Body geometry;
    Point reference_point{0, 0};
    std::string boundary_type;
    std::array<int, 3> dof_mask{1, 1, 1};
    Point dof_anchor{0, 0};
    Body2(std::string id, geometry2::Body shape, Point reference = {0, 0},
          std::string boundary = {}, std::array<int, 3> mask = {1, 1, 1},
          std::optional<Point> anchor = std::nullopt);
};
struct Assembly2 {
    std::vector<Body2> bodies;
    std::optional<std::vector<std::array<std::size_t, 2>>> pairs;
    std::string completeness = "completeness_unknown";
    std::string profile = "profile1";
    geometry2::GeometryLimits limits;
};
struct Source2 {
    std::string kind, a, b;
    std::vector<std::size_t> feature_a, feature_b;
    bool operator<(const Source2& other) const;
    bool operator==(const Source2& other) const = default;
};
struct ContactLabel2 {
    std::string a, b;
    Point point;
    std::string edge_body;
    std::array<std::size_t, 2> edge;
};
struct ExactContact2 {
    std::size_t a, b;
    Point point, tangent;
    std::vector<Source2> sources;
    ContactLabel2 label;
    Point normal() const;
};
struct ContactPoint2 {
    std::size_t a, b;
    Point point;
    std::string fp_type;
    std::vector<Point> boundaries;
    std::vector<Source2> sources;
    std::vector<std::vector<Point>> forbidden;
    bool retained = false;
};
struct ContactSegment2 {
    std::size_t a, b;
    Point start, end, tangent;
    std::vector<Source2> sources;
};
struct ConeReachability2 {
    ContactPoint2 point;
    Dofs dofs;
    Matrix matrix;
    Vector rhs;
    bool unreachable = false;
    std::optional<Vector> multipliers, twist;
};
struct ContactSet2 {
    Assembly2 assembly;
    std::vector<ExactContact2> constraints;
    std::vector<ContactPoint2> points;
    std::vector<Source2> raw_sources;
    std::vector<ContactPoint2> unresolved;
    std::vector<ConeReachability2> redundancy_certificates;
    std::optional<std::string> status;
    std::string call_status = "OK", mathematical_status = "UNPROVED";
    std::string completeness;
    std::optional<std::string> reason;
    std::vector<ContactSegment2> segments;
    std::vector<std::array<int, 3>> pair_states;
    std::vector<ConeReachability2> reachable_witnesses;
};
struct LocalCell2 {
    std::size_t neighbor_index, cell_index, piece_a, piece_b;
    Polygon vertices;
    std::vector<Segment> active_edges;
};
struct RadiusBound2 {
    std::size_t neighbor_index, cell_index, edge_index;
    Point start, end;
    Rational squared_distance;
};
struct ContactSource2 {
    std::size_t neighbor_index;
    geometry2::Label label;
    Point point;
};
struct LockArc2 {
    std::string kind;
    Point start, end, sample;
    std::string state;
    std::vector<std::array<std::size_t, 2>> blockers;
};
struct LockCertificate {
    std::optional<std::string> status, refinement, reason;
    std::vector<LocalCell2> local_cells;
    std::vector<LockArc2> arcs;
    std::optional<Rational> radius;
    std::optional<Point> separation_ray, seam_ray;
    std::string call_status = "OK";
    std::optional<std::string> mathematical_status;
    std::string display_status = "EXACT";
    std::vector<RadiusBound2> radius_bounds;
    std::vector<int> pair_states;
    std::vector<ContactSource2> contact_sources;
};
struct NormalizedConeLP2 {
    Matrix matrix;
    Vector rhs, objective, exact_x, exact_y;
};
struct ZeroConeCombination2 {
    std::size_t coordinate;
    int sign;
    Vector multipliers;
};
struct FirstOrderResult2 {
    std::string call_status = "OK";
    std::optional<std::string> mathematical_status;
    std::optional<bool> cone_is_zero;
    std::string display_status = "NOT_APPLICABLE";
    Dofs dofs;
    std::optional<Matrix> matrix;
    std::optional<std::size_t> exact_rank;
    std::optional<Rational> normalized_value;
    std::optional<NormalizedConeLP2> normalization_certificate;
    std::optional<Matrix> rays, lineality, generators;
    std::optional<std::vector<ZeroConeCombination2>> zero_certificates;
    std::optional<std::string> reason;
};

ContactSet2 assemble_contact_set2(const Assembly2& assembly);
std::pair<Matrix, Dofs> constraint_matrix(const Assembly2& assembly,
                                        const std::vector<ExactContact2>& constraints);
LockCertificate query_lock(const geometry2::Body& moving,
                           const std::vector<geometry2::Body>& fixed,
                           const geometry2::GeometryLimits& limits = {});
FirstOrderResult2 first_order_mobility(const ContactSet2& contacts);
FirstOrderResult2 first_order_mobility(const Assembly2& assembly);
// Exposed only to private C++ semantic gates, never to the production C ABI.
std::pair<Matrix, Matrix> double_description(const Matrix& rows, std::size_t size);
std::string export_exact(const ContactSet2& result);
std::string export_exact(const LockCertificate& result);
std::string export_exact(const FirstOrderResult2& result);
} // namespace eab2::contact
