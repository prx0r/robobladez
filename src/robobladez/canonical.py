"""First-class CanonicalEvent (rmdev2 Phase 7).

The engine already produces events, but media used story-derived identifiers.
A CanonicalEvent is an immutable, addressable event with a stable id:

    rbz://match/<id>/round/2/event/17

carrying pre_state / post_state so the renderer can reconstruct the event
visually. Event types are fixed vocabulary. Story beats reference these IDs;
they do not substitute for them.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

EVENT_TYPES = (
    "ROUND_STARTED", "COLLISION", "ABILITY_STARTED", "ABILITY_ENDED",
    "RING_OUT", "SPIN_OUT", "BURST", "ROUND_ENDED", "MATCH_ENDED",
)


@dataclass(frozen=True)
class CanonicalEvent:
    event_id: str
    match_id: str
    round: int
    tick: int
    time: float
    type: str
    actor: str = ""
    target: str = ""
    pre_state: dict[str, Any] = field(default_factory=dict)
    post_state: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    execution_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_canonical_event(*, match_id: str, execution_digest: str = "",
                          round_no: int, tick: int, time: float,
                          type: str, actor: str = "", target: str = "",
                          pre_state: dict | None = None,
                          post_state: dict | None = None,
                          payload: dict | None = None) -> CanonicalEvent:
    """Build a CanonicalEvent with a stable, addressable id."""
    event_id = f"rbz://match/{match_id}/round/{round_no}/event/{tick}"
    return CanonicalEvent(
        event_id=event_id, match_id=match_id, round=round_no, tick=tick,
        time=time, type=type, actor=actor, target=target,
        pre_state=pre_state or {}, post_state=post_state or {},
        payload=payload or {}, execution_digest=execution_digest,
    )


def extract_canonical_events(match, execution_digest: str = "") -> list[CanonicalEvent]:
    """Extract engine events into first-class CanonicalEvents with pre/post state.

    For each engine Event we reconstruct the pre/post blade states from the
    surrounding frames (best-effort), giving the renderer visual grounding.
    """
    events: list[CanonicalEvent] = []
    for rnd in match.rounds:
        # Index frames by tick for state lookup.
        frames_by_tick = {f.tick: f for f in rnd.frames}
        for ev in rnd.events:
            pre = _state_at(frames_by_tick, ev.tick - 1) or _state_at(frames_by_tick, ev.tick)
            post = _state_at(frames_by_tick, ev.tick) or pre
            etype = _map_event_type(ev.type)
            events.append(build_canonical_event(
                match_id=match.match_id, execution_digest=execution_digest,
                round_no=rnd.round_no, tick=ev.tick, time=ev.t,
                type=etype, actor=ev.actor, target=ev.target,
                pre_state=pre, post_state=post, payload=ev.data,
            ))
    return events


def _map_event_type(engine_type: str) -> str:
    mapping = {
        "collision": "COLLISION",
        "boundary_contact": "COLLISION",
        "round_end": "ROUND_ENDED",
        "ring_out": "RING_OUT",
        "spin_out": "SPIN_OUT",
        "burst": "BURST",
    }
    return mapping.get(engine_type, engine_type.upper())


def _state_at(frames_by_tick: dict, tick: int) -> dict | None:
    f = frames_by_tick.get(tick)
    if f is None:
        return None
    return {"states": f.states, "actions": f.actions}
