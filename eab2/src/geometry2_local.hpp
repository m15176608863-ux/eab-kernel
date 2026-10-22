#pragma once
#include "geometry2.hpp"

namespace eab2::geometry2 {

struct LocalCell {
    std::size_t cell_index, piece_a, piece_b;
    Polygon vertices;
    std::vector<Segment> active_edges;
};
struct RadiusBound {
    std::size_t cell_index, edge_index;
    Segment edge;
    Rational squared_distance;
};
struct CellExclusion {
    std::size_t cell_index;
    Polygon vertices;
    numeric::Aabb2 box;
    bool aabb_contains_zero;
    // Every excluded convex cell supplies one strictly negative edge sign,
    // even when the inclusive AABB has already excluded it.
    std::size_t edge_index;
    Segment edge;
    Rational signed_cross;
};
struct OriginSource {
    Label label;
    Segment translation_segment;
    Point physical_point;
    bool at_start, at_end;
    std::size_t vertex_id;
    std::array<std::size_t, 2> edge_vertex_ids;
};
struct LocalOrigin {
    int body_state, topology_state;
    Rational radius;
    std::vector<LocalCell> cells;
    std::vector<RadiusBound> radius_bounds;
    std::vector<CellExclusion> exclusions;
    // Unfiltered original incidences. These are NOT mechanical constraints.
    std::vector<OriginSource> raw_sources;
};

Rational segment_distance_squared_to_origin(const Segment& segment);
LocalOrigin local_origin(const Entrance& entrance);
int local_directional_state(const LocalOrigin& origin, const Point& direction);

} // namespace eab2::geometry2
