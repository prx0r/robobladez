"""Reincarnation authoring (rm7/rm8/rmdev2 Phase 4).

A persistent Agent, given match context, authors a RBZ-RC-1 Reincarnation: a
bounded state machine (states + transitions + continuous controls + memory).
This is the ACTUAL mechanism that fights — not a pick from a policy zoo.

The author interface is `ReincarnationAuthor.author(context) -> Manifest`.
`BaselineReincarnationAuthor` is the deterministic MVP heuristic compiler over
the mechanical report. Later `LLMReincarnationAuthor` / `EvolutionaryAuthor`
implement the same contract. The LLM/persistent-Agent is NEVER queried per tick.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Protocol

from .mechanical import MechanicalMatchupReport
from .reincarnation import ReincarnationManifest, MemorySlot, ReincarnationRuntime


@dataclass
class ReincarnationContext:
    """Everything a persistent Agent may use to author its battle-self (rmdev2 Phase 4)."""
    agent_id: str
    mechanical_report: MechanicalMatchupReport | None = None
    opponent_public_record: dict = field(default_factory=dict)
    opponent_model: dict = field(default_factory=dict)
    previous_reincarnations: list[dict] = field(default_factory=list)
    reflections: list[dict] = field(default_factory=list)
    daimon_advice: str = ""
    human_mentor_messages: list[str] = field(default_factory=list)
    ruleset: str = "R1"
    body_capabilities: dict = field(default_factory=dict)
    compute_class: str = "C1"


class ReincarnationAuthor(Protocol):
    def author(self, context: ReincarnationContext) -> ReincarnationManifest: ...


def _control_profile(report: MechanicalMatchupReport | None, me: str, opponent: str) -> dict:
    """Derive a control bias from the mechanical report (advantages/vulnerabilities)."""
    if report is None:
        return {"radial": 0.3, "tangential": 0.2, "torque": 0.0, "boost": 0.3}
    my = report.per_body.get(me, {})
    opp = report.per_body.get(opponent, {})
    profile = {
        "radial": 0.3, "tangential": 0.2, "torque": 0.0, "boost": 0.3,
    }
    # If the opponent is slow, pressure harder (aggressive).
    if opp.get("avg_speed", 0.5) < 0.5:
        profile["boost"] = 0.7
        profile["radial"] = 0.5
    # If the opponent has weak spin endurance, counter via contact.
    elif opp.get("avg_spin", 500) < 540:
        profile["tangential"] = 0.6
        profile["boost"] = 0.55
    # If the opponent holds center, orbit instead of pressing.
    elif opp.get("center_fraction", 0.0) > 0.4:
        profile["tangential"] = 0.8
        profile["radial"] = 0.1
        profile["boost"] = 0.25
    # If I have high spin, lean on endurance (conservative).
    elif my.get("avg_spin", 500) > 600:
        profile["boost"] = 0.15
        profile["radial"] = 0.2
    return profile


class BaselineReincarnationAuthor:
    """Deterministic MVP heuristic compiler (rmdev2 Phase 4).

    Reads the mechanical report and authors a fixed-shape RBZ-RC-1 state machine.
    This is NOT yet "the AI rewrites itself" — it is the reference MVP author.
    """

    def __init__(self, agent_version: str, author: str = ""):
        self.agent_version = agent_version
        self.author = author

    def author(self, context: ReincarnationContext,
               target_match: str = "", reincarnation_id: str = "",
               parent_id: str = "") -> ReincarnationManifest:
        report = context.mechanical_report
        me = context.agent_id
        opponent = list(context.opponent_public_record.get("_opponent", [""]))[0] if \
            context.opponent_public_record.get("_opponent") else ""
        return self.reincarnate(report, me, opponent,
                                target_match=target_match,
                                reincarnation_id=reincarnation_id,
                                parent_id=parent_id)

    def reincarnate(self, report: MechanicalMatchupReport | None, me: str, opponent: str,
                    target_match: str = "", reincarnation_id: str = "",
                    parent_id: str = "") -> ReincarnationManifest:
        ctrl = _control_profile(report, me, opponent)
        # Build a small, deterministic, bounded state machine (C1 class).
        # States:
        #   observe: hold a steady control, react to proximity.
        #   pressure: push inward / engage when opponent closes.
        #   orbit: keep tangential separation (avoid their strength).
        #   recover: retreat to center after engagement.
        states = [
            {
                "id": "observe",
                "action": {"radial": ctrl["radial"], "tangential": ctrl["tangential"],
                           "torque": ctrl["torque"], "boost": ctrl["boost"]},
                "transitions": [
                    {"if": {"op": "lt", "lhs": "distance", "threshold": 0.16},
                     "to": "pressure"},
                    {"if": {"op": "lt", "lhs": "distance", "threshold": 0.35},
                     "to": "orbit"},
                    # Memory-driven adaptation: once pressure has been seen
                    # enough, prefer a more evasive opening next time.
                    {"if": {"op": "gte", "lhs": "memory.pressure_seen",
                            "threshold": 3.0}, "to": "orbit"},
                ],
            },
            {
                "id": "pressure",
                "action": {"radial": min(1.0, ctrl["radial"] + 0.3),
                           "tangential": min(1.0, ctrl["tangential"] + 0.2),
                           "torque": 0.05, "boost": min(1.0, ctrl["boost"] + 0.2),
                           "memory": [{"name": "pressure_seen", "op": "add", "value": 1}]},
                "transitions": [
                    {"if": {"op": "gt", "lhs": "distance", "threshold": 0.30},
                     "to": "observe"},
                    {"if": {"op": "lt", "lhs": "self_integrity", "threshold": 30.0},
                     "to": "recover"},
                ],
            },
            {
                "id": "orbit",
                "action": {"radial": 0.1, "tangential": 0.8,
                           "torque": 0.0, "boost": 0.2},
                "transitions": [
                    {"if": {"op": "lt", "lhs": "distance", "threshold": 0.15},
                     "to": "pressure"},
                ],
            },
            {
                "id": "recover",
                "action": {"radial": 0.8, "tangential": 0.0,
                           "torque": 0.0, "boost": 0.15},
                "transitions": [
                    {"if": {"op": "lt", "lhs": "distance", "threshold": 0.3},
                     "to": "observe"},
                ],
            },
        ]
        return ReincarnationManifest(
            reincarnation_id=reincarnation_id or f"{me}-r1",
            agent_version=self.agent_version,
            target_match=target_match,
            compute_class="C1",
            author=self.author,
            parent_reincarnation_id=parent_id,
            memory=[MemorySlot("pressure_seen", "u8", 0, 255)],
            states=states,
            initial_state="observe",
            strategy_thesis=(f"counter the opponent's mechanical profile "
                             f"(report vs {opponent})"),
        )

    def compile(self, manifest: ReincarnationManifest) -> ReincarnationRuntime:
        """Compile (interpret) a validated manifest into an executable."""
        from .reincarnation import validate
        validate(manifest)
        return ReincarnationRuntime(manifest)
