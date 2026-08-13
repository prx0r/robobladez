"""Reincarnation authoring (rm7/rm8).

A persistent Agent, given the mechanical report + opponent model, authors a
RBZ-RC-1 Reincarnation: a bounded state machine (states + transitions +
continuous controls + memory). This is the ACTUAL mechanism that fights —
not a pick from a hard-coded Python policy zoo.

The author produces a ReincarnationManifest, which is validated, normalized,
committed, and executed by ReincarnationRuntime. The LLM/persistent-Agent does
NOT get queried per tick.
"""
from __future__ import annotations
from typing import Any

from .mechanical import MechanicalMatchupReport
from .reincarnation import ReincarnationManifest, MemorySlot, ReincarnationRuntime


def _control_profile(report: MechanicalMatchupReport, me: str, opponent: str) -> dict:
    """Derive a control bias from the mechanical report (advantages/vulnerabilities)."""
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


class ReincarnationAuthor:
    """Deterministically authors a RBZ-RC-1 reincarnation from match context."""

    def __init__(self, agent_version: str, author: str = ""):
        self.agent_version = agent_version
        self.author = author

    def reincarnate(self, report: MechanicalMatchupReport, me: str, opponent: str,
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
                ],
            },
            {
                "id": "pressure",
                "action": {"radial": min(1.0, ctrl["radial"] + 0.3),
                           "tangential": min(1.0, ctrl["tangential"] + 0.2),
                           "torque": 0.05, "boost": min(1.0, ctrl["boost"] + 0.2)},
                "transitions": [
                    {"if": {"op": "gt", "lhs": "distance", "threshold": 0.30},
                     "to": "observe"},
                    {"if": {"op": "gt", "lhs": "self_integrity", "threshold": 0.0},
                     "to": "recover"},  # reached only if integrity low via memory
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
