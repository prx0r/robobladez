"""Renderer-agnostic media pipeline (rmdev Phase 13 / LTX production pack).

Canonical software objects (RENDERER-AGNOSTIC-ARCHITECTURE.md):
    ShotSpec, RenderRequest, RenderJob, RenderArtifact, QAVerdict

The world/game projects emit ShotSpecs and consume RenderArtifacts. A backend
(LTX API / ComfyUI / local pipeline / future 2.5) maps ShotSpec -> its own
workflow. RoboBladez never parses model-specific output beyond RenderArtifact.

LTX is a REPLACEABLE RENDERER downstream of canonical simulation state:
    MATCH REPLAY -> EVENT SELECTION -> SHOT SPEC -> CONTROL ASSETS -> LTX -> QA -> EPISODE
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import hashlib, json

# Control hierarchy (06-CONTROL-HIERARCHY.md): least-generative route that solves the shot.
# Loose -> constrained.
CONTROL_MODES = ("T2V", "I2V", "FIRST_LAST", "KEYFRAME", "ICLORA", "RETAKE", "EXTEND")

# Control mode per shot class (examples/robobladez/WORKFLOW.md).
SHOT_CLASS_CONTROL = {
    "establish_arena": "T2V",          # loose establishing -> T2V fine
    "competitor_intro": "I2V",         # recognizable competitor -> I2V w/ ref
    "battle_event": "KEYFRAME",        # exact transition -> keyframe interp
    "daimon_manifestation": "I2V",     # canonical refs; generative styling acceptable
    "replay_analysis": "ICLORA",       # deterministic overlay, dramatization only
    "round_result": "RETAKE",
}

CANONICALITY = ("CANONICAL_EVENT", "RECONSTRUCTION", "NARRATIVE_PROJECTION", "COUNTERFACTUAL")
ASPECT_RATIOS = ("16:9", "9:16", "1:1", "4:5", "5:4")


@dataclass
class ShotSpec:
    """Canonical, schema-valid shot specification (templates/shot-spec.schema.json)."""
    shot_id: str
    project: str = "robobladez"
    canonicality: str = "CANONICAL_EVENT"
    prompt: str = ""
    duration_s: float = 5.0
    aspect_ratio: str = "16:9"
    constraints: list[str] = field(default_factory=list)
    negative_prompt: str = ""
    fps: int = 24
    entity_versions: list[str] = field(default_factory=list)
    environment_version: str | None = None
    event_ids: list[str] = field(default_factory=list)
    audio: dict[str, Any] = field(default_factory=dict)
    camera: dict[str, Any] = field(default_factory=dict)
    references: list[dict[str, Any]] = field(default_factory=list)
    control_mode: str = "T2V"
    qa: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        """Content hash of the executable shot fields."""
        body = {
            "project": self.project, "canonicality": self.canonicality,
            "entity_versions": self.entity_versions,
            "environment_version": self.environment_version,
            "event_ids": self.event_ids, "duration_s": self.duration_s,
            "fps": self.fps, "aspect_ratio": self.aspect_ratio,
            "control_mode": self.control_mode, "constraints": self.constraints,
        }
        return hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:20]


@dataclass
class RenderRequest:
    shot_spec_uri: str
    renderer_family: str = "ltx"
    renderer_version: str = "2.3"
    profile: str = "draft"   # draft|final|retake|control-heavy|audio-driven

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RenderJob:
    job_id: str
    request: RenderRequest
    status: str = "queued"   # queued|running|done|failed
    seed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"job_id": self.job_id, "request": self.request.to_dict(),
                "status": self.status, "seed": self.seed}


@dataclass
class RenderArtifact:
    job_id: str
    shot_id: str
    uri: str = ""
    digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QAVerdict:
    shot_id: str
    pass_: bool = False
    failures: list[str] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["pass"] = d.pop("pass_")
        return d


def _pick_control(shot_class: str) -> str:
    """Control hierarchy: least generative route that solves the shot class."""
    return SHOT_CLASS_CONTROL.get(shot_class, "T2V")


def shot_class_for(beat_type: str) -> str:
    """Map a canonical beat/event type to a shot class (WORKFLOW.md)."""
    if beat_type == "establish":
        return "establish_arena"
    if beat_type == "round_result":
        return "round_result"
    if beat_type in ("collision", "ring_out", "spin_out", "burst", "round_end"):
        return "battle_event"
    return "battle_event"


def build_shot_spec(*, shot_id: str, project: str = "robobladez",
                    canonicality: str = "CANONICAL_EVENT", prompt: str = "",
                    duration_s: float = 5.0, aspect_ratio: str = "16:9",
                    constraints: list[str] | None = None,
                    entity_versions: list[str] | None = None,
                    environment_version: str | None = None,
                    event_ids: list[str] | None = None,
                    audio: dict[str, Any] | None = None,
                    camera: dict[str, Any] | None = None,
                    references: list[dict[str, Any]] | None = None,
                    control_mode: str | None = None,
                    shot_class: str | None = None,
                    qa: list[str] | None = None) -> ShotSpec:
    """Construct a ShotSpec, defaulting control_mode from the shot class."""
    effective_class = shot_class or "battle_event"
    mode = control_mode or _pick_control(effective_class)
    return ShotSpec(
        shot_id=shot_id, project=project, canonicality=canonicality,
        prompt=prompt, duration_s=duration_s, aspect_ratio=aspect_ratio,
        constraints=constraints or [], entity_versions=entity_versions or [],
        environment_version=environment_version, event_ids=event_ids or [],
        audio=audio or {}, camera=camera or {}, references=references or [],
        control_mode=mode, qa=qa or [],
    )
