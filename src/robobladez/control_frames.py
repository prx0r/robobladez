"""Deterministic control-frame builder (rmdev2 Phase 13).

For each canonical battle event, produce FIRST/LAST control plates from the
event's pre_state / post_state + canonical assets. These are control plates,
not final art: they give LTX a concrete before/after to interpolate instead of
relying entirely on text. Camera is simple: top-down / high three-quarter /
low three-quarter.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

from .canonical import CanonicalEvent

CAMERAS = ("top_down", "high_three_quarter", "low_three_quarter")


@dataclass
class ControlFrame:
    frame_uri: str
    kind: str            # first | last | guide
    camera: str
    composition: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ControlFrames:
    shot_id: str
    basis_event_id: str
    first: ControlFrame | None = None
    last: ControlFrame | None = None
    guide: ControlFrame | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "shot_id": self.shot_id,
            "basis_event_id": self.basis_event_id,
            "first": self.first.to_dict() if self.first else None,
            "last": self.last.to_dict() if self.last else None,
            "guide": self.guide.to_dict() if self.guide else None,
        }


class ControlFrameBuilder:
    """Builds first/last control plates from canonical event state.

    Pure deterministic metadata: maps blade state (pos/orientation/scale) into a
    compositor command. No image is actually rasterized here (that needs the
    canonical talisman PNGs + an image lib); this produces the composition the
    real compositor will render.
    """

    def __init__(self, camera: str = "high_three_quarter"):
        self.camera = camera if camera in CAMERAS else "high_three_quarter"

    def build(self, event: CanonicalEvent, shot_id: str) -> ControlFrames:
        first_comp = self._compose(event.pre_state)
        last_comp = self._compose(event.post_state)
        return ControlFrames(
            shot_id=shot_id,
            basis_event_id=event.event_id,
            first=ControlFrame(frame_uri=f"controls/{shot_id}-first.png",
                               kind="first", camera=self.camera,
                               composition=first_comp),
            last=ControlFrame(frame_uri=f"controls/{shot_id}-last.png",
                              kind="last", camera=self.camera,
                              composition=last_comp),
        )

    def _compose(self, state: dict | None) -> dict[str, Any]:
        """Map engine pre/post state into a compositor command (positions/scales)."""
        placements = {}
        if state and isinstance(state, dict):
            states = state.get("states") or {}
            for blade_id, s in states.items():
                pos = s.get("pos", {})
                placements[blade_id] = {
                    "x": pos.get("x", 0.0),
                    "y": pos.get("y", 0.0),
                    # orientation from velocity direction (planar proxy).
                    "angle": _velocity_angle(s.get("vel", {})),
                    "scale": _spin_scale(s.get("omega", 0.0)),
                }
        return {"camera": self.camera, "placements": placements}


def _velocity_angle(vel: dict) -> float:
    import math
    vx, vy = vel.get("x", 0.0), vel.get("y", 0.0)
    if vx == 0 and vy == 0:
        return 0.0
    return round(math.degrees(math.atan2(vy, vx)), 2)


def _spin_scale(omega: float) -> float:
    return round(0.9 + min(0.2, abs(omega) / 5000.0), 3)
