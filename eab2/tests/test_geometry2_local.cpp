#include "geometry2_local.hpp"
#include <algorithm>
#include <iostream>
#include <stdexcept>

using namespace eab2::geometry2;
namespace exact = eab2::exact;
namespace {
int checks = 0;
void require(bool condition, const char* message) {
    ++checks;
    if (!condition) throw std::runtime_error(message);
}
Polygon square(Rational x = Rational(0)) {
    return {{x, 0}, {x + Rational(1), 0}, {x + Rational(1), 1}, {x, 1}};
}
void verify(const Entrance& entrance, const LocalOrigin& local) {
    require(!entrance.subdivision_is_materialized(), "local query must remain lazy");
    require(local.radius > Rational(0), "strict positive radius");
    require(local.cells.size() + local.exclusions.size() == entrance.cells.size(), "cell partition complete");
    for (const auto& bound : local.radius_bounds) {
        require(local.radius * local.radius < bound.squared_distance, "strict radius bound");
        require(bound.squared_distance == segment_distance_squared_to_origin(bound.edge), "exact distance bound");
    }
    for (const auto& excluded : local.exclusions) {
        require(excluded.signed_cross < Rational(0), "outside cell strict separator");
        require(excluded.signed_cross == cross(sub(excluded.edge[1], excluded.edge[0]), mul(excluded.edge[0], -1)), "separator exact value");
    }
    for (const auto& source : local.raw_sources)
        require(on_segment({0, 0}, source.translation_segment[0], source.translation_segment[1]), "raw association contains zero");
    for (const Point direction : Polygon{{1, 0}, {0, 1}, {-1, 0}, {0, -1}, {2, 3}, {-3, 2}}) {
        const Rational size = exact::abs(direction[0]) + exact::abs(direction[1]);
        const Point probe = mul(direction, local.radius / (Rational(2) * size));
        require(local_directional_state(local, direction) == entrance.membership(probe), "certified local cone classification");
    }
}
void boundary_and_original_ids() {
    Entrance entrance{Body(square()), Body(square(1))};
    const auto local = local_origin(entrance);
    verify(entrance, local);
    require(local.body_state == 0 && local.topology_state == 0, "touching squares states");
    require(local.cells.size() == 1 && local.cells[0].active_edges.size() == 1, "inclusive AABB keeps boundary cell");
    require(local.raw_sources.size() == 8, "all eight endpoint incidences retained");
    require(local.radius == Rational(exact::Int(1), exact::Int(2)), "known radius half");
    require(local_directional_state(local, {1, 0}) == 1, "right enters overlap");
    require(local_directional_state(local, {-1, 0}) == -1, "left separates");
    auto reversed = square();
    std::reverse(reversed.begin(), reversed.end());
    Entrance clockwise{Body(reversed), Body(square(1))};
    const auto cw = local_origin(clockwise);
    verify(clockwise, cw);
    require(cw.raw_sources.size() == 8, "CW endpoint associations complete");
    for (const auto& source : cw.raw_sources) {
        if (source.label.kind == "VE") require(reversed[source.vertex_id] == source.physical_point, "original vertex identity");
    }
    const auto json = entrance.local_origin_exact();
    require(json.find("\"global_subdivision_materialized\":false") != std::string::npos, "export remains lazy");
}
void seam_isolated_outside_overlap() {
    const Polygon pin{{0, Rational(exact::Int(1), exact::Int(2))}, {1, Rational(exact::Int(1), exact::Int(2))},
                      {1, Rational(exact::Int(3), exact::Int(2))}, {0, Rational(exact::Int(3), exact::Int(2))}};
    const Polygon channel{{-1, -1}, {2, -1}, {2, 2}, {1, 2}, {1, 0}, {0, 0}, {0, 2}, {-1, 2}};
    Entrance seam{Body(pin), Body(channel)};
    const auto seam_local = local_origin(seam);
    verify(seam, seam_local);
    require(seam_local.body_state == 0 && seam_local.topology_state == 1, "seam is contact in interior E");
    require(local_directional_state(seam_local, {0, 1}) == 0, "seam sliding geometry only");
    const Polygon pocket{{0, 0}, {6, 0}, {6, 2}, {5, 2}, {5, 1}, {1, 1}, {1, 5}, {5, 5}, {5, 4}, {6, 4}, {6, 6}, {0, 6}};
    Entrance isolated{Body(Polygon{{1, 1}, {5, 1}, {5, 5}, {1, 5}}), Body(pocket)};
    const auto point_local = local_origin(isolated);
    verify(isolated, point_local);
    require(point_local.body_state == 0 && point_local.topology_state == 1, "isolated point states");
    require(local_directional_state(point_local, {0, 1}) == 1, "isolated point is not seam");
    Entrance outside{Body(square()), Body(square(10))};
    const auto outside_local = local_origin(outside);
    verify(outside, outside_local);
    require(outside_local.cells.empty() && outside_local.raw_sources.empty(), "outside no zero associations");
    require(!outside_local.exclusions.front().aabb_contains_zero, "strict AABB exclusion");
    Entrance overlap{Body(square()), Body(square())};
    const auto overlap_local = local_origin(overlap);
    verify(overlap, overlap_local);
    require(overlap_local.body_state == 1, "overlap remains separate mathematical state");
}
} // namespace
int main() {
    try {
        boundary_and_original_ids();
        seam_isolated_outside_overlap();
        std::cout << "EAB2_LOCAL_TESTS checks=" << checks << " failed=0\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "EAB2_LOCAL_TESTS checks=" << checks << " failed=1 detail=" << error.what() << '\n';
        return 1;
    }
}
