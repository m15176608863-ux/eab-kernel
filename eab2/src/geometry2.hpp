#pragma once
#include "numeric.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace eab2::geometry2 {
using exact::Int;
using exact::Rational;
using Point = numeric::Point2;
using Polygon = std::vector<Point>;
using Segment = std::array<Point, 2>;

struct GeometryLimits {
    std::uint64_t max_work_units = UINT64_C(50000000);
    std::size_t max_elements = 2000000;
    std::size_t max_integer_bits = 65536;
};
// Nested scopes share a deterministic work counter. The ABI opens the outer
// scope around the entire call (including batches); standalone C++ methods
// open their own scope. No wall clock or thread scheduling affects the limit.
class GeometryWorkScope {
    struct State { std::uint64_t used, limit; GeometryLimits options; } owned_;
    static thread_local State* active_;
    State* previous_;
    State* shared_;
    std::uint64_t start_, previous_limit_;
public:
    GeometryLimits limits;
    GeometryWorkScope();
    explicit GeometryWorkScope(const GeometryLimits& limits);
    ~GeometryWorkScope();
    GeometryWorkScope(const GeometryWorkScope&) = delete;
    GeometryWorkScope& operator=(const GeometryWorkScope&) = delete;
    void step(std::uint64_t count = 1);
    void check_size(std::size_t count) const;
    std::uint64_t consumed() const;
};

Point add(const Point& a, const Point& b);
Point sub(const Point& a, const Point& b);
Point mul(const Point& a, const Rational& value);
Rational cross(const Point& a, const Point& b);
Rational dot(const Point& a, const Point& b);
bool on_segment(const Point& p, const Point& a, const Point& b);
std::vector<Segment> edges(const Polygon& polygon);
Rational signed_area2(const Polygon& polygon);
int cell_state(const Polygon& polygon, const Point& point);
std::string convexity_violation(const Polygon& polygon);

// Internal states deliberately match Python: -1 OUTSIDE, 0 CONTACT/BOUNDARY,
// 1 OVERLAP/INTERIOR. The C ABI maps these to two distinct public enum types.
struct Body {
    Polygon vertices;
    std::vector<std::size_t> original_vertex_ids;
    std::vector<std::size_t> original_edge_ids;
    // Original supplied order, including negative-zero provenance.
    std::vector<std::array<std::uint64_t, 2>> input_bits;
    explicit Body(const Polygon& points, const GeometryLimits& limits = {});
    static Body from_bits(const std::vector<std::array<std::uint64_t, 2>>& bits, const GeometryLimits& limits = {});
};

struct Label {
    std::string kind;
    std::size_t a_index = 0;
    std::size_t b_index = 0;
    bool operator==(const Label& other) const;
    bool operator<(const Label& other) const;
};
struct Facet {
    Label label;
    Point start;
    Point direction;
};
struct ExactEntranceBlock {
    Polygon vertices;
    std::vector<Facet> facets;
    std::vector<std::array<std::size_t, 2>> pairs;
};
ExactEntranceBlock entrance_block_exact(const Polygon& a, const Polygon& b);
int membership_exact(const ExactEntranceBlock& entrance, const Point& point);
int vertex_side_exact(const Polygon& polygon, std::size_t index, const Point& edge);
int ve_side_exact(const Polygon& a, std::size_t i, const Polygon& b, std::size_t j);
int ev_side_exact(const Polygon& a, std::size_t i, const Polygon& b, std::size_t j);
int polygons_overlap_exact(const Body& a, const Body& b, const Point& point);
int entrance_membership_exact(const Body& a, const Body& b, const Point& point);

struct Cover {
    Label label;
    // Exact recipes. Normal is an unnormalized direction; gap_squared and
    // gap_sign specify signed gap without storing a rounded sqrt as truth.
    std::optional<Point> normal_direction;
    Rational gap_squared;
    int gap_sign = 0;
    std::optional<Rational> param;
    Point point_a, point_b;
    bool strict = false;
    bool window_active = false;
};
std::optional<Cover> ve_cover(const Polygon& a, std::size_t i, const Polygon& b, std::size_t j,
                            const Rational& tol = Rational(0), const std::optional<Rational>& cone_tol = std::nullopt);
std::optional<Cover> ev_cover(const Polygon& a, std::size_t i, const Polygon& b, std::size_t j,
                            const Rational& tol = Rational(0), const std::optional<Rational>& cone_tol = std::nullopt);
std::optional<Cover> vv_cover(const Polygon& a, std::size_t i, const Polygon& b, std::size_t j,
                            const Rational& tol = Rational(0), const std::optional<Rational>& cone_tol = std::nullopt);
std::vector<Cover> enumerate_covers(const Polygon& a, const Polygon& b,
                                  const std::optional<Rational>& window, bool require_in_segment = true,
                                  const Rational& tol = Rational(0), const std::optional<Rational>& cone_tol = std::nullopt,
                                  const std::optional<Rational>& seg_tol = std::nullopt);
std::string covers_exact_json(const Polygon& a, const Polygon& b,
                             const std::optional<Rational>& window, bool require_in_segment = true,
                             const Rational& tol = Rational(0), const std::optional<Rational>& cone_tol = std::nullopt,
                             const std::optional<Rational>& seg_tol = std::nullopt);

struct RawSegment {
    Label label;
    Point start, end;
};
struct ContactSegment {
    Point start, end;
    std::vector<Label> labels;
    std::array<int, 2> side_states;
    bool boundary = false;
};
struct ContactPoint {
    Point point;
    std::vector<Label> labels;
};
struct CoverPiece {
    Label label;
    Point start, end;
    int body_state = -1;
    std::array<int, 2> side_states;
    bool exposed = false;
};
struct Cell {
    Polygon vertices;
    Point sample;
    int body_state = -1;
    int topology_state = -1;
};
struct Subdivision {
    std::vector<Cell> vertices, edges, faces;
    int exterior_state = -1;
};
struct Statistics {
    std::size_t raw_segments = 0;
    std::size_t arranged_segments = 0;
    std::size_t intersection_points = 0;
    std::size_t max_integer_bits = 0;
    std::uint64_t exact_work_units = 0;
};

class Entrance {
    class CacheTransaction;
    bool compact_;
    GeometryLimits limits_;
    std::vector<numeric::Aabb2> boxes_;
    mutable bool skeleton_ready_ = false;
    mutable bool subdivision_ready_ = false;
    mutable bool clipped_ready_ = false;
    mutable std::vector<RawSegment> raw_;
    mutable std::vector<ContactSegment> contacts_;
    mutable std::vector<ContactPoint> points_;
    mutable std::vector<Segment> boundary_;
    mutable std::vector<CoverPiece> clipped_;
    mutable Subdivision subdivision_;
    mutable Statistics statistics_;
    void build_skeleton() const;

public:
    Body a, b;
    std::vector<Polygon> parts_a, parts_b, cells;
    std::vector<Segment> cell_edges;
    Entrance(const Body& first, const Body& second, bool merge_convex = true,
             bool compact_subdivision = true, const GeometryLimits& limits = {});
    const GeometryLimits& limits() const { return limits_; }
    int membership(const Point& point) const;
    int topology(const Point& point) const;
    // Exact infinitesimal classification, with no finite probe displacement.
    int directional_state(const Point& point, const Point& direction) const;
    const std::vector<RawSegment>& raw_segments() const;
    const std::vector<ContactSegment>& contact_segments() const;
    const std::vector<ContactPoint>& contact_points() const;
    const std::vector<Segment>& boundary() const;
    const std::vector<CoverPiece>& clipped_covers() const;
    const Subdivision& subdivision() const;
    bool subdivision_is_materialized() const { return subdivision_ready_; }
    const Statistics& statistics() const;
    std::string export_exact() const;
    // Implemented separately in geometry2_local.cpp; never builds subdivision.
    std::string local_origin_exact() const;
};

// Serialization helpers shared with the separately implemented local query.
std::string point_json(const Point& point);
std::string polygon_json(const Polygon& polygon);
std::string label_json(const Label& label);
} // namespace eab2::geometry2
