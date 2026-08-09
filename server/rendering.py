"""Renderer-neutral camera exposure helpers for CityGen previews."""

from __future__ import annotations

import math

__all__ = ["exposure_for_altitude", "exposure_value"]


def exposure_value(iso: float, f_number: float, shutter_seconds: float) -> float:
    """Return EV100-adjusted exposure value for a physical camera setting."""
    return math.log2((f_number**2) / shutter_seconds) - math.log2(iso / 100.0)


def exposure_for_altitude(altitude_deg: float) -> dict:
    """Return a renderer-neutral, sunny-16-derived exposure starting point."""
    if altitude_deg <= 0.0:
        return {
            "iso": 800.0,
            "f_number": 4.0,
            "shutter_speed": 30.0,
            "note": "sun below horizon — sky-only lighting, exposure is a guess",
        }
    iso = 100.0
    f_number = 8.0
    stops_down = -math.log2(max(math.sin(math.radians(altitude_deg)), 1e-3))
    shutter_denom = max(30.0, min(4000.0, 400.0 / (2.0**stops_down)))
    return {
        "iso": iso,
        "f_number": f_number,
        "shutter_speed": round(shutter_denom, 1),
        "exposure_value": round(exposure_value(iso, f_number, 1.0 / shutter_denom), 2),
        "note": f"sunny-16 derived, {stops_down:.1f} stops below midday reference",
    }
