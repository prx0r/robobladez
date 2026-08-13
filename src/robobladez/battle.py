"""Two-phase BattleProtocol (rmdev Phase 1 core + gameplay origin).

The defining RoboBladez mechanic, encoded:

    PHASE 1 — MECHANICAL REVEAL
        bodies fight passively (no policy)
        -> both competitors receive the MechanicalMatchupReport

    PHASE 2 — SEALED STRATEGIC RESPONSE
        each agent inspects the report, predicts the opponent, and privately
        selects a specialized "battle avatar" policy
        -> policy is sealed (fingerprinted + committed)

    PHASE 3 — BEST-OF-N
        locked avatars control the nodes; outcome is deterministic given seed.

The persistent character (AgentState) is deliberately distinct from the
temporary battle avatar. This embodies: persistent character != body != policy.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Protocol

from .agent import AgentState
from .analysis import analyze_behavior
from .canon import CanonStore
from .engine import run_match
from .mechanical import MechanicalMatchupReport, mechanical_report
from .model import ArenaSpec, BladeSpec
from .policy import Policy, commitment
from .replay import save_match
from .evolution import evolve_agent
from .zoo import POLICY_ZOO


class Strategist(Protocol):
    """Given the mechanical report, choose a battle-avatar policy."""
    def choose(self, report: MechanicalMatchupReport, me: str, opponent: str) -> Policy: ...


@dataclass
class ReportAwareStrategist:
    """A simple, deterministic strategist that reads the report.

    Chooses a policy countering the opponent's mechanical weakness:
    if the opponent is slow -> rush/pressure;
    if the opponent has weak spin endurance -> pressure/counter;
    if the opponent is strong at center -> orbit/ghost (avoid their strength);
    default -> counter.
    """
    id: str = "report-aware-v1"

    def choose(self, report: MechanicalMatchupReport, me: str, opponent: str) -> Policy:
        opp = report.per_body.get(opponent, {})
        my = report.per_body.get(me, {})
        choice = "counter"
        if opp.get("avg_speed", 0.5) < 0.5:
            choice = "pressure"          # they can't escape pressure
        elif opp.get("avg_spin", 500) < 540:
            choice = "counter"           # punish their contact attempts
        elif opp.get("center_fraction", 0.0) > 0.4:
            choice = "orbit"             # avoid their center strength
        elif my.get("avg_spin", 500) > 600:
            choice = "spin-saver"        # lean on endurance
        for name, fact in POLICY_ZOO:
            if name == choice:
                return fact()
        return POLICY_ZOO[3][1]()  # fallback counter


@dataclass
class StaticStrategist:
    """Always picks the same policy — for comparison / baseline."""
    name: str = "counter"
    id: str = "static"

    def choose(self, report: MechanicalMatchupReport, me: str, opponent: str) -> Policy:
        for n, f in POLICY_ZOO:
            if n == self.name:
                return f()
        return POLICY_ZOO[3][1]()


@dataclass
class BattleAvatar:
    """A locked, specialized match policy for one competitor."""
    agent_id: str
    policy: Policy
    commitment: str

    def to_dict(self) -> dict[str, Any]:
        return {"agent_id": self.agent_id, "policy_id": self.policy.id,
                "commitment": self.commitment}


@dataclass
class BattleOutcome:
    match: Any
    mechanical: MechanicalMatchupReport
    avatars: dict[str, BattleAvatar]
    analysis: dict[str, Any]
    reflections: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mechanical": self.mechanical.to_dict(),
            "avatars": {k: v.to_dict() for k, v in self.avatars.items()},
            "winner": self.match.winner,
            "match_id": self.match.match_id,
            "replay_digest": self.match.replay_digest,
            "analysis": self.analysis,
            "reflections": self.reflections,
        }


def run_battle(agent_a: AgentState, spec_a: BladeSpec,
               agent_b: AgentState, spec_b: BladeSpec,
               arena: ArenaSpec | None = None,
               mechanical_runs: int = 60, strategic_rounds: int = 5,
               base_seed: int = 9000,
               strategist_a: Strategist | None = None,
               strategist_b: Strategist | None = None,
               out_dir: str | None = None) -> BattleOutcome:
    arena = arena or ArenaSpec()
    strat_a = strategist_a or ReportAwareStrategist()
    strat_b = strategist_b or ReportAwareStrategist()

    # ---- Phase 1: mechanical reveal (public) ----
    report = mechanical_report(spec_a, spec_b, arena,
                               runs=mechanical_runs, base_seed=base_seed, rounds=3)

    # ---- Phase 2: sealed strategic response ----
    nonce = f"{base_seed}|{spec_a.id}|{spec_b.id}"
    pa = strat_a.choose(report, spec_a.id, spec_b.id)
    pb = strat_b.choose(report, spec_b.id, spec_a.id)
    avatars = {
        spec_a.id: BattleAvatar(agent_a.agent_id, pa, commitment(pa, nonce)),
        spec_b.id: BattleAvatar(agent_b.agent_id, pb, commitment(pb, nonce)),
    }

    # ---- Phase 3: best-of-N with locked avatars ----
    match = run_match(base_seed + 5000, arena, spec_a, spec_b,
                      pa, pb, strategic_rounds)

    analysis = analyze_behavior(match)
    refl_a = evolve_agent(agent_a, match, spec_a.id, spec_b.id, agent_b,
                          analysis[spec_a.id]["daimon_projection"]["affinities"])
    refl_b = evolve_agent(agent_b, match, spec_b.id, spec_a.id, agent_a,
                          analysis[spec_b.id]["daimon_projection"]["affinities"])

    if out_dir:
        from pathlib import Path
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        save_match(match, out / f"battle_{spec_a.id}_vs_{spec_b.id}.json")

    return BattleOutcome(
        match=match, mechanical=report, avatars=avatars,
        analysis=analysis,
        reflections={spec_a.id: refl_a.to_dict(), spec_b.id: refl_b.to_dict()},
    )
