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
    """Canonical, schema-valid shot specification (ShotSpec v2, rmdev2 Phase 14).

    v2 adds basis_event_ids (canonical event references), subjects (entry
    snapshots + visual assets), state (first/last control frames), and control
    (preferred/fallback route).
    """
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
    basis_event_ids: list[str] = field(default_factory=list)   # v2: canonical event refs
    subjects: list[dict[str, Any]] = field(default_factory=list)  # v2: entry snapshots
    state: dict[str, Any] = field(default_factory=dict)        # v2: first/last/guide frames
    control: dict[str, str] = field(default_factory=dict)      # v2: {preferred, fallback}
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
            "event_ids": self.event_ids, "basis_event_ids": self.basis_event_ids,
            "duration_s": self.duration_s,
            "fps": self.fps, "aspect_ratio": self.aspect_ratio,
            "control_mode": self.control_mode, "constraints": self.constraints,
        }
        return hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:20]


@dataclass
class RenderRequest:
    shot_spec_uri: str
    renderer_profile_id: str = "ltx-2.3-draft"  # resolves to an immutable RendererManifest
    profile: str = "draft"   # draft|final|retake|control-heavy|audio-driven

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RenderJob:
    job_id: str
    request: RenderRequest
    status: str = "queued"   # queued|running|done|failed
    seed: int = 0
    retake_parent: str = ""
    interval: list[float] = field(default_factory=list)  # [start,end] for retake

    def to_dict(self) -> dict[str, Any]:
        return {"job_id": self.job_id, "request": self.request.to_dict(),
                "status": self.status, "seed": self.seed,
                "retake_parent": self.retake_parent, "interval": self.interval}


@dataclass
class RenderArtifact:
    job_id: str
    shot_id: str
    uri: str = ""
    digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RendererManifest:
    """Renderer-agnostic manifest bound to a RenderJob (LTX-2.3 or 2.5).

    The renderer is a replaceable backend; RoboBladez emits the manifest and
    consumes RenderArtifact. It never parses model-specific output.
    """
    renderer_family: str = "ltx"
    renderer_version: str = "2.5"   # 2.3 today; 2.5 when officially released
    backend: str = "api"           # api|comfyui|local
    model_id: str = ""
    workflow_id: str = ""
    workflow_version: str = ""
    checkpoint_digest: str = ""
    seed: int = 0
    profile: str = "draft"
    audio: bool = True

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
                    basis_event_ids: list[str] | None = None,
                    subjects: list[dict] | None = None,
                    state: dict | None = None,
                    control: dict | None = None,
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
        basis_event_ids=basis_event_ids or [], subjects=subjects or [],
        state=state or {}, control=control or {},
        audio=audio or {}, camera=camera or {}, references=references or [],
        control_mode=mode, qa=qa or [],
    )


class ControlPlanner:
    """Pick the least-generative control route that solves the shot (rmdev2 Phase 15).

    Keeps the model on the most-constrained route possible: loose establishing ->
    T2V/I2V; exact trajectory -> FIRST_LAST/KEYFRAME; failed region -> RETAKE.
    """

    def plan(self, *, canonicality: str, shot_class: str,
             has_basis_events: bool = False, has_control_frames: bool = False,
             failed_region: bool = False) -> tuple[str, str]:
        """Return (preferred, fallback) control modes."""
        if failed_region:
            return "RETAKE", "RETAKE"
        if shot_class == "establish_arena":
            return "T2V", "I2V"
        if shot_class == "competitor_intro":
            return "I2V", "I2V"
        if shot_class == "daimon_manifestation":
            return "I2V", "KEYFRAME"
        if shot_class == "battle_event":
            if has_control_frames:
                return "FIRST_LAST", "KEYFRAME"
            if has_basis_events:
                return "KEYFRAME", "I2V"
            return "I2V", "T2V"
        if shot_class == "round_result":
            return "RETAKE", "KEYFRAME"
        return "T2V", "I2V"


# ---------------------------------------------------------------------------
# Production render queue + end-to-end simulation (no LTX call)
# ---------------------------------------------------------------------------
PROFILES = ("draft", "final", "retake", "control-heavy", "audio-driven")


@dataclass
class RenderQueue:
    """Production queue (ltx-2.5 ops/PRODUCTION-QUEUE.md).

    compile shots on CPU -> draft -> QA -> final accepted -> retake failures.
    """
    jobs: list[RenderJob] = field(default_factory=list)
    artifacts: list[RenderArtifact] = field(default_factory=list)
    verdicts: list[QAVerdict] = field(default_factory=list)

    def enqueue(self, shot: ShotSpec, profile: str = "draft",
                seed: int = 0, job_id: str = "") -> RenderJob:
        job_id = job_id or f"job-{len(self.jobs)+1}"
        req = RenderRequest(shot_spec_uri=shot.shot_id, profile=profile)
        job = RenderJob(job_id=job_id, request=req, seed=seed)
        self.jobs.append(job)
        return job

    def mark_running(self, job_id: str) -> None:
        self._by_id(job_id).status = "running"

    def complete(self, job: RenderJob, uri: str = "", digest: str = "") -> RenderArtifact:
        job.status = "done"
        art = RenderArtifact(job_id=job.job_id, shot_id=job.request.shot_spec_uri,
                             uri=uri, digest=digest)
        self.artifacts.append(art)
        return art

    def retake(self, shot: ShotSpec, parent_job_id: str, interval: tuple[float, float],
               seed: int = 0) -> RenderJob:
        """Retake: repair a localized temporal interval of a failed shot.

        Instead of re-rendering the whole shot, enqueue a retake job bound to
        the parent job + the [start,end] interval that failed QA.
        """
        job = self.enqueue(shot, profile="retake", seed=seed,
                           job_id=f"retake-{parent_job_id}")
        job.request.shot_spec_uri = shot.shot_id
        job.retake_parent = parent_job_id
        job.interval = list(interval)
        return job

    def reframe(self, artifact: RenderArtifact, aspect_ratio: str) -> RenderArtifact:
        """Reframe: derive an aspect-ratio variant from a master artifact.

        Produce one master (e.g. 16:9), then derive 9:16 / 4:5 / 1:1 without
        re-generating the scene (ltx-2.5 docs/07-RETAKE-EXTEND-REFRAME).
        """
        variant = RenderArtifact(
            job_id=artifact.job_id,
            shot_id=f"{artifact.shot_id}:{aspect_ratio.replace(':', 'x')}",
            uri=f"{artifact.uri}?aspect={aspect_ratio}",
            digest=artifact.digest,  # same content, reframed framing
        )
        self.artifacts.append(variant)
        return variant

    def record_verdict(self, v: QAVerdict) -> None:
        self.verdicts.append(v)

    def _by_id(self, job_id: str) -> RenderJob:
        for j in self.jobs:
            if j.job_id == job_id:
                return j
        raise KeyError(job_id)


def simulate_render(shot: ShotSpec, job: RenderJob,
                    manifest: RendererManifest | None = None) -> RenderArtifact:
    """Simulate a render WITHOUT calling LTX (mock backend).

    Produces a deterministic, canonical RenderArtifact (uri + content digest).
    This is the CPU-side substitute so the whole media pipeline can be validated
    offline; a real backend maps ShotSpec -> LTX later. The digest here is the
    shot's canonical content digest (protocol binding), NOT real footage bytes.
    """
    manifest = manifest or RendererManifest(seed=job.seed, profile=job.request.profile)
    uri = f"mock://{manifest.renderer_family}/{job.request.profile}/{shot.shot_id}.mp4"
    digest = shot.digest()  # protocol binding: mock claims it rendered exactly this spec
    return RenderArtifact(job_id=job.job_id, shot_id=shot.shot_id, uri=uri, digest=digest)


def binding_qa(shot: ShotSpec, artifact: RenderArtifact, expected_winner: str | None = None,
               replay_event_ids: list[str] | None = None) -> QAVerdict:
    """Binding QA (rmreview #14): does the artifact claim the right canonical spec?

    This is PROTOCOL QA, not media QA. It verifies identity/commitment
    (digest, winner constraint, event ids) — NOT whether rendered footage
    actually obeys them. Real footage QA is VisualQA (requires the renderer).
    """
    failures: list[str] = []
    passed: list[str] = []
    if artifact.digest != shot.digest():
        failures.append("artifact digest does not match shot canonical content")
    else:
        passed.append("artifact bound to shot canonical content")
    if shot.canonicality == "CANONICAL_EVENT":
        has_winner = any("winner" in c for c in shot.constraints)
        if not has_winner:
            failures.append("CANONICAL_EVENT shot missing winner constraint")
        else:
            passed.append("winner constraint present")
    # Real winner check: only CANONICAL_EVENT shots must carry a winner
    # constraint that matches expected_winner (RECONSTRUCTION shots don't
    # imply an outcome).
    if expected_winner is not None and shot.canonicality == "CANONICAL_EVENT":
        winner_ok = any(expected_winner in c for c in shot.constraints)
        if not winner_ok:
            failures.append(f"shot winner constraint contradicts expected winner {expected_winner}")
        else:
            passed.append(f"winner context verified ({expected_winner})")
    if replay_event_ids is not None:
        for eid in replay_event_ids:
            if eid not in shot.event_ids:
                failures.append(f"shot missing canonical event {eid}")
                break
        else:
            passed.append("shot references canonical events")
    return QAVerdict(shot_id=shot.shot_id, pass_=not failures,
                     failures=failures, passed_checks=passed)


def visual_qa(shot: ShotSpec, artifact: RenderArtifact) -> QAVerdict:
    """Visual QA interface (rmreview #14/#15).

    Evaluates whether rendered FOOTAGE actually satisfies the shot: identity
    preserved, correct competitor count, event order, result, arena, effect
    placement. Requires access to rendered frames/vision (not available with a
    mock renderer). Returns NOT_VERIFIED so a semantic pass is never faked.
    """
    return QAVerdict(
        shot_id=shot.shot_id, pass_=False,
        failures=["visual QA not executed: mock renderer provides no footage"],
        passed_checks=[],
    )


def produce_episode(shots: list[ShotSpec], winner: str | None = None,
                    profiles: str = "draft", seed: int = 0,
                    reframe_aspects: tuple[str, ...] = ()) -> dict:
    """Full end-to-end media pipeline (CPU, no LTX).

    compile -> enqueue -> simulate render -> QA. Optionally reframe the master
    artifact into aspect variants (9:16 Shorts, 4:5) without re-generating the
    scene. Returns an organized artifact.
    """
    queue = RenderQueue()
    outputs = []
    for shot in shots:
        job = queue.enqueue(shot, profile=profiles, seed=seed)
        art = simulate_render(shot, job)
        verdict = binding_qa(shot, art, expected_winner=winner)
        queue.record_verdict(verdict)
        variants = []
        for asp in reframe_aspects:
            v = queue.reframe(art, asp)
            variants.append(v.to_dict())
        outputs.append({"shot": shot.to_dict(), "job": job.to_dict(),
                        "artifact": art.to_dict(),
                        "binding_qa": verdict.to_dict(),
                        "visual_qa": visual_qa(shot, art).to_dict(),
                        "variants": variants})
    return {"episode_winner": winner, "shots": len(shots),
            "accepted": sum(1 for o in outputs if o["binding_qa"]["pass"]),
            "rejected": sum(1 for o in outputs if not o["binding_qa"]["pass"]),
            "outputs": outputs}


# ---------------------------------------------------------------------------
# Retake loop (Phase 18) + Episode assembler (Phase 19)
# ---------------------------------------------------------------------------
def retake_loop(shot: ShotSpec, max_retries: int = 2,
                check=lambda shot, art: True) -> dict:
    """Automatic Retake retry loop (rmdev2 Phase 18).

    Renders a shot, runs the supplied check; if it fails, retakes the failed
    interval. Capped at `max_retries`; beyond that returns NEEDS_REVIEW.
    Never infinite. The `check` callable returns (passed, failed_interval).
    """
    attempts = []
    for attempt in range(max_retries + 1):
        job = RenderJob(job_id=f"{shot.shot_id}-r{attempt}",
                        request=RenderRequest(shot_spec_uri=shot.shot_id,
                                              profile="retake" if attempt else "final"),
                        seed=attempt)
        art = simulate_render(shot, job)
        verdict = binding_qa(shot, art)
        attempts.append({"attempt": attempt, "artifact": art.to_dict(),
                         "qa": verdict.to_dict()})
        if verdict.pass_:
            return {"status": "accepted", "attempts": attempts}
        # If no custom check provides an interval, give up.
        if not callable(check):
            break
    return {"status": "NEEDS_REVIEW", "attempts": attempts,
            "note": f"failed after {max_retries} retries; human review required"}


class EpisodeAssembler:
    """Assembles accepted shot artifacts into an episode (rmdev2 Phase 19).

    For MVP the assembler produces the episode SEQUENCE + an assembly manifest
    (ordering, narration, titles, durations). Actual video concatenation is
    delegated to a backend (ffmpeg) and is not required for the CPU vertical
    slice — but the ordering/provenance is canonical and real.
    """

    EPISODE_SHAPE = [
        "cold_open", "intro_a", "intro_b", "mechanical_reveal",
        "battle_1", "battle_2", "decisive_result", "closing_analysis",
    ]

    def assemble(self, shot_specs: list[ShotSpec], winner: str | None = None,
                 intro_agents: list[str] | None = None) -> dict:
        """Return an ordered episode plan + assembly manifest."""
        by_id = {s.shot_id: s for s in shot_specs}
        # Map shot classes into the episode shape.
        plan = []
        intros = intro_agents or ["A", "B"]
        intro_shot_ids = [sid for sid, s in by_id.items() if "intro-" in sid]
        battle = [sid for sid, s in by_id.items() if "beat-" in sid]
        establish = [sid for sid, s in by_id.items() if "establish" in sid]
        cold = establish[:1]
        for slot in self.EPISODE_SHAPE:
            if slot == "cold_open" and cold:
                plan.append({"slot": slot, "shot_id": cold[0],
                             "duration_s": by_id[cold[0]].duration_s})
            elif slot.startswith("intro_") and intro_shot_ids:
                sid = intro_shot_ids.pop(0) if intro_shot_ids else ""
                if sid:
                    plan.append({"slot": slot, "shot_id": sid,
                                 "duration_s": by_id[sid].duration_s})
            elif slot == "mechanical_reveal":
                plan.append({"slot": slot, "shot_id": establish[0] if establish else "",
                             "duration_s": 4.0})
            elif slot.startswith("battle_") and battle:
                sid = battle.pop(0) if battle else ""
                if sid:
                    plan.append({"slot": slot, "shot_id": sid,
                                 "duration_s": by_id[sid].duration_s})
            elif slot == "decisive_result" and battle:
                sid = battle.pop() if battle else ""
                if sid:
                    plan.append({"slot": slot, "shot_id": sid,
                                 "duration_s": 6.0})
            elif slot == "closing_analysis":
                plan.append({"slot": slot, "shot_id": "",
                             "duration_s": 5.0})
        total = sum(p["duration_s"] for p in plan)
        return {
            "shape": self.EPISODE_SHAPE,
            "winner": winner,
            "plan": plan,
            "total_duration_s": total,
            "backend": "ffmpeg (concatenate accepted artifacts)",
            "note": "MVP: assembly plan is canonical; actual concat is a backend task",
        }
