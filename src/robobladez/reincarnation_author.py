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


# Distinct machine shapes per strategy profile. These are the "author
# archetypes" that make non-transitivity possible: each has a different opening,
# engagement, and recovery bias, so A beats B, B beats C, C beats A can emerge.
def _build_profile_states(profile: str, ctrl: dict) -> list[dict]:
    low_integrity = ("self_integrity_fraction", "lt", 0.30)
    if profile == "pressure":
        return _states(observe=(ctrl["radial"] * 0.8, ctrl["tangential"] * 0.3,
                                0.0, min(1.0, ctrl["boost"] + 0.4),
                                ("distance", "lt", 0.30)),
                       engage=(1.0, ctrl["tangential"] * 0.6, 0.1, 1.0,
                               low_integrity))
    if profile == "orbit":
        return _states(observe=(0.05, 0.9, 0.0, 0.2,
                                ("distance", "lt", 0.20)),
                       engage=(0.3, 0.9, 0.0, 0.3, low_integrity))
    if profile == "bait":
        return _states(observe=(0.0, 0.7, 0.0, 0.25,
                                ("closing_speed", "gt", 0.5)),
                       engage=(-0.4, 1.0, 0.0, 0.5, low_integrity))  # wait, cut across
    if profile == "counter":
        return _states(observe=(0.4, 0.3, 0.0, 0.35,
                                ("closing_speed", "gt", 0.6)),
                       engage=(0.5, -0.8, 0.05, 0.9, low_integrity))  # punish overshoot
    if profile == "endure":
        return _states(observe=(0.1, 0.2, 0.0, 0.08,
                                ("distance", "lt", 0.15)),
                       engage=(0.6, 0.2, 0.0, 0.2, low_integrity))
    # adaptive / default
    return _states(observe=(ctrl["radial"], ctrl["tangential"],
                            0.0, ctrl["boost"],
                            ("distance", "lt", 0.20)),
                   engage=(min(1.0, ctrl["radial"] + 0.3),
                           min(1.0, ctrl["tangential"] + 0.2),
                           0.05, min(1.0, ctrl["boost"] + 0.2),
                           low_integrity))


def _states(observe, engage):
    """Standard 4-state machine: observe -> pressure -> orbit -> recover.

    observe = (radial, tangential, torque, boost, (lhs, op, threshold) to engage)
    engage  = (radial, tangential, torque, boost, (lhs, op, threshold) to recover)
    """
    obs_cond, eng_cond = observe[4], engage[4]
    states = [
        {
            "id": "observe",
            "action": {"radial": observe[0], "tangential": observe[1],
                       "torque": observe[2], "boost": observe[3]},
            "transitions": [
                {"if": {"op": obs_cond[1], "lhs": obs_cond[0],
                        "threshold": obs_cond[2]}, "to": "pressure"},
                {"if": {"op": "lt", "lhs": "distance", "threshold": 0.35},
                 "to": "orbit"},
            ],
        },
        {
            "id": "pressure",
            "action": {"radial": engage[0], "tangential": engage[1],
                       "torque": engage[2], "boost": engage[3],
                       "memory": [{"name": "pressure_seen", "op": "add", "value": 1}]},
            "transitions": [
                {"if": {"op": "gt", "lhs": "distance", "threshold": 0.30},
                 "to": "observe"},
                {"if": {"op": eng_cond[1], "lhs": eng_cond[0],
                        "threshold": eng_cond[2]}, "to": "recover"},
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
    return states


class BaselineReincarnationAuthor:
    """Deterministic MVP heuristic compiler (rmdev2 Phase 4).

    Reads the mechanical report and authors a fixed-shape RBZ-RC-1 state machine.
    This is NOT yet "the AI rewrites itself" — it is the reference MVP author.
    """

    def __init__(self, agent_version: str, author: str = "",
                 strategy_profile: str = "adaptive"):
        self.agent_version = agent_version
        self.author = author
        self.strategy_profile = strategy_profile  # pressure|orbit|bait|counter|endure|adaptive

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
        profile = self.strategy_profile
        if profile == "adaptive":
            ctrl = ctrl  # baseline heuristic
        states = _build_profile_states(profile, ctrl)
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
