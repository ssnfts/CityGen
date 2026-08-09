"""Contracts for the dependency-free CityGen generation core."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from citygen import (  # noqa: E402
    BoundaryError,
    CityBoundary,
    DetailTier,
    GenerationSettings,
    HydrologyFeature,
    RunRegistry,
    Style,
    TransportError,
    TransportFeature,
    estimate_budget,
    infer_transport_profile,
    merge_hydrology,
)


def test_closed_concave_boundary_preserves_hole_and_area():
    boundary = CityBoundary.from_rings(
        [(0, 0), (12, 0), (12, 12), (6, 6), (0, 12)],
        holes=[[(2, 2), (4, 2), (4, 4), (2, 4)]],
    )

    assert boundary.area_m2 == pytest.approx(104.0)
    assert boundary.holes == (((2.0, 2.0), (4.0, 2.0), (4.0, 4.0), (2.0, 4.0)),)


def test_self_intersecting_boundary_is_rejected_before_generation():
    with pytest.raises(BoundaryError, match="self-intersects"):
        CityBoundary.from_rings([(0, 0), (10, 10), (0, 10), (10, 0)])


def test_run_registry_allocates_non_destructive_versions_and_category_names():
    registry = RunRegistry(existing_layer_names={"CG_Dubai_v001_Buildings"})
    run = registry.allocate("Dubai")

    assert run.version == 2
    assert run.layer("Roads") == "CG_Dubai_v002_Roads"
    assert run.selection_set("Review_InferredTransport") == "CG_Dubai_v002_Review_InferredTransport"
    assert run.object_name("Roads", 7) == "CG_Dubai_v002_Roads_007"


def test_presets_are_fixed_and_hero_budget_exceeds_draft():
    settings = GenerationSettings(style=Style.POST_APOCALYPSE, tier=DetailTier.HERO, density=0.8)
    hero = estimate_budget(10_000, settings)
    draft = estimate_budget(10_000, GenerationSettings(style=Style.MODERN, tier=DetailTier.DRAFT))

    assert set(Style) == {
        Style.MODERN,
        Style.MEDIEVAL,
        Style.VICTORIAN,
        Style.STEAMPUNK,
        Style.SCI_FI,
        Style.POST_APOCALYPSE,
    }
    assert hero.estimated_polygons > draft.estimated_polygons
    assert "rubble" in hero.required_asset_kinds


def test_local_hydrology_overrides_global_fallback_inside_its_coverage():
    merged = merge_hydrology(
        [HydrologyFeature("ocean", "gebco", ((0, 0), (10, 0), (10, 10), (0, 10)))],
        [HydrologyFeature("river", "local", ((2, 2), (8, 2), (8, 4), (2, 4)))],
    )

    assert [feature.source for feature in merged] == ["gebco", "local"]
    assert merged[-1].override is True


def test_bridge_profile_follows_a_turn_and_flags_inferred_vertical_geometry():
    feature = TransportFeature(
        osm_id="way/12",
        kind="road",
        points=((0, 0), (20, 0), (20, 30), (40, 30)),
        tags={"bridge": "yes", "highway": "primary"},
    )
    profile = infer_transport_profile(feature, lambda x, y: 0.1 * x + 0.05 * y)

    assert len(profile.points) > len(feature.points)
    assert profile.inferred_vertical is True
    assert profile.reason == "bridge elevation reconstructed from terrain and tags"
    assert min(point[2] for point in profile.points) >= 5.0


def test_tunnel_profile_stays_under_terrain_and_is_flagged_for_review():
    feature = TransportFeature(
        osm_id="way/13",
        kind="road",
        points=((0, 0), (20, 0)),
        tags={"tunnel": "yes", "highway": "residential"},
    )
    profile = infer_transport_profile(feature, lambda _x, _y: 100.0)

    assert profile.inferred_vertical is True
    assert all(point[2] <= 94.0 for point in profile.points)


def test_impossible_grade_reconstruction_fails_before_scene_mutation():
    feature = TransportFeature(
        osm_id="way/14",
        kind="road",
        points=((0, 0), (1, 0)),
        tags={"bridge": "yes", "highway": "residential"},
    )

    with pytest.raises(TransportError, match="grade"):
        infer_transport_profile(feature, lambda x, _y: 100.0 * x)
