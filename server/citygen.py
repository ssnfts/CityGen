"""Dependency-free planning primitives for the native CityGen tool.

The 3ds Max package consumes this module, but it deliberately does not import
``pymxs``.  That boundary keeps geometry validation, version allocation,
budgeting, hydrology precedence and vertical-road reconstruction testable from a
normal Python interpreter.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Iterable, Mapping


Point2 = tuple[float, float]
Point3 = tuple[float, float, float]


class BoundaryError(ValueError):
    """The selected Max shape cannot safely be used as a city boundary."""


class TransportError(ValueError):
    """A road, bridge or tunnel cannot satisfy its physical constraints."""


class DetailTier(str, Enum):
    DRAFT = "Draft"
    PRODUCTION = "Production"
    HERO = "Hero"


class Style(str, Enum):
    MODERN = "Modern"
    MEDIEVAL = "Medieval"
    VICTORIAN = "Victorian"
    STEAMPUNK = "Steampunk"
    SCI_FI = "Sci-Fi"
    POST_APOCALYPSE = "Post-Apocalypse"


@dataclass(frozen=True)
class CityBoundary:
    outer: tuple[Point2, ...]
    holes: tuple[tuple[Point2, ...], ...] = ()

    @classmethod
    def from_rings(cls, outer: Iterable[Point2], *, holes: Iterable[Iterable[Point2]] = ()) -> "CityBoundary":
        clean_outer = _clean_ring(outer, "outer boundary")
        clean_holes = tuple(_clean_ring(ring, "hole") for ring in holes)
        return cls(clean_outer, clean_holes)

    @property
    def area_m2(self) -> float:
        return abs(_signed_area(self.outer)) - sum(abs(_signed_area(hole)) for hole in self.holes)


def _clean_ring(points: Iterable[Point2], label: str) -> tuple[Point2, ...]:
    ring = tuple((float(x), float(y)) for x, y in points)
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring = ring[:-1]
    if len(ring) < 3:
        raise BoundaryError(f"{label} needs at least three distinct points")
    if len(set(ring)) != len(ring):
        raise BoundaryError(f"{label} contains duplicate points")
    if _self_intersects(ring):
        raise BoundaryError(f"{label} self-intersects")
    if abs(_signed_area(ring)) < 1e-6:
        raise BoundaryError(f"{label} has zero area")
    return ring


def _signed_area(ring: tuple[Point2, ...]) -> float:
    return 0.5 * sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]))


def _self_intersects(ring: tuple[Point2, ...]) -> bool:
    count = len(ring)
    for i in range(count):
        a, b = ring[i], ring[(i + 1) % count]
        for j in range(i + 1, count):
            if i == j or (i + 1) % count == j or (j + 1) % count == i:
                continue
            c, d = ring[j], ring[(j + 1) % count]
            if _segments_intersect(a, b, c, d):
                return True
    return False


def _segments_intersect(a: Point2, b: Point2, c: Point2, d: Point2) -> bool:
    def orientation(p: Point2, q: Point2, r: Point2) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    one, two, three, four = orientation(a, b, c), orientation(a, b, d), orientation(c, d, a), orientation(c, d, b)
    return (one > 0) != (two > 0) and (three > 0) != (four > 0)


@dataclass(frozen=True)
class GenerationSettings:
    style: Style = Style.MODERN
    tier: DetailTier = DetailTier.PRODUCTION
    density: float = 0.5
    damage: float = 0.0
    seed: int = 1

    def __post_init__(self) -> None:
        if not 0.0 <= self.density <= 1.0:
            raise ValueError("density must be between 0 and 1")
        if not 0.0 <= self.damage <= 1.0:
            raise ValueError("damage must be between 0 and 1")


@dataclass(frozen=True)
class BudgetEstimate:
    estimated_objects: int
    estimated_polygons: int
    required_asset_kinds: tuple[str, ...]


def estimate_budget(area_m2: float, settings: GenerationSettings) -> BudgetEstimate:
    if area_m2 <= 0:
        raise ValueError("area_m2 must be positive")
    tier_multiplier = {DetailTier.DRAFT: 1, DetailTier.PRODUCTION: 3, DetailTier.HERO: 8}[settings.tier]
    base_objects = max(1, round(area_m2 / 200 * (0.25 + settings.density)))
    assets = ["facade", "roof", "road", "water"]
    if settings.tier is not DetailTier.DRAFT:
        assets.extend(("street_furniture", "vegetation"))
    if settings.style is Style.POST_APOCALYPSE or settings.damage > 0:
        assets.append("rubble")
    return BudgetEstimate(base_objects, base_objects * 750 * tier_multiplier, tuple(assets))


@dataclass(frozen=True)
class CityRun:
    site: str
    version: int

    @property
    def prefix(self) -> str:
        return f"CG_{self.site}_v{self.version:03d}"

    def layer(self, category: str) -> str:
        return f"{self.prefix}_{category}"

    def selection_set(self, category: str) -> str:
        return f"{self.prefix}_{category}"

    def object_name(self, category: str, index: int) -> str:
        return f"{self.prefix}_{category}_{index:03d}"


@dataclass(frozen=True)
class RunRegistry:
    existing_layer_names: set[str]

    def allocate(self, site: str) -> CityRun:
        safe_site = re.sub(r"[^A-Za-z0-9]+", "_", site).strip("_") or "Site"
        prefix = f"CG_{safe_site}_v"
        versions = [int(name[len(prefix):len(prefix) + 3]) for name in self.existing_layer_names if name.startswith(prefix) and name[len(prefix):len(prefix) + 3].isdigit()]
        return CityRun(safe_site, max(versions, default=0) + 1)


@dataclass(frozen=True)
class HydrologyFeature:
    kind: str
    source: str
    outline: tuple[Point2, ...]
    override: bool = False


def merge_hydrology(global_features: Iterable[HydrologyFeature], local_features: Iterable[HydrologyFeature]) -> tuple[HydrologyFeature, ...]:
    return tuple(global_features) + tuple(replace(feature, override=True) for feature in local_features)


@dataclass(frozen=True)
class TransportFeature:
    osm_id: str
    kind: str
    points: tuple[Point2, ...]
    tags: Mapping[str, str]


@dataclass(frozen=True)
class TransportProfile:
    points: tuple[Point3, ...]
    inferred_vertical: bool
    reason: str | None = None


def infer_transport_profile(feature: TransportFeature, ground: Callable[[float, float], float], *, sample_spacing_m: float = 10.0) -> TransportProfile:
    if len(feature.points) < 2:
        raise TransportError(f"{feature.osm_id} needs at least two centerline points")
    points = _resample(feature.points, sample_spacing_m)
    bridge = _tag_true(feature.tags.get("bridge"))
    tunnel = _tag_true(feature.tags.get("tunnel")) or feature.tags.get("location") == "underground"
    if bridge and tunnel:
        raise TransportError(f"{feature.osm_id} cannot be both a bridge and a tunnel")
    clearance = 5.0 if bridge else 6.0 if tunnel else 0.0
    profile = tuple((x, y, ground(x, y) + clearance if bridge else ground(x, y) - clearance if tunnel else ground(x, y)) for x, y in points)
    max_grade = 0.15 if feature.tags.get("highway") in {"residential", "service", "unclassified"} else 0.10
    for first, second in zip(profile, profile[1:]):
        horizontal = math.dist(first[:2], second[:2])
        if horizontal and abs(second[2] - first[2]) / horizontal > max_grade + 1e-9:
            raise TransportError(f"{feature.osm_id} reconstruction exceeds allowed grade")
    if bridge:
        return TransportProfile(profile, True, "bridge elevation reconstructed from terrain and tags")
    if tunnel:
        return TransportProfile(profile, True, "tunnel depth reconstructed from terrain and tags")
    return TransportProfile(profile, False)


def _tag_true(value: str | None) -> bool:
    return value not in {None, "", "no", "false", "0"}


def _resample(points: tuple[Point2, ...], spacing: float) -> tuple[Point2, ...]:
    result = [points[0]]
    for start, end in zip(points, points[1:]):
        length = math.dist(start, end)
        steps = max(1, math.ceil(length / spacing))
        result.extend((start[0] + (end[0] - start[0]) * part / steps, start[1] + (end[1] - start[1]) * part / steps) for part in range(1, steps + 1))
    return tuple(result)
