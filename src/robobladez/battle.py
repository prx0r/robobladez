"""Two-phase BattleProtocol (rmdev Phase 1 core + gameplay origin, rm8-hardened).

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
temporary battle avatar (and, later, from a Reincarnation).

rm8 fixes in this module:
  - P0 salience: uses SalienceDetector (typed evidence), NOT `bool(match.winner)`.
  - P0 signature: uses a persistent SignatureRegistry (cross-match/opponent),
    never a fresh min_occurrences=1 detector per match.
  - P1 transactionality: both AgentStates are snapshotted before derivation;
    both reflections derive from the SAME pre-match epoch; updates applied after.
  - P1 typed IDs: avatars/reflections key by agent_id, body_id stored explicitly.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Protocol

from .agent import AgentState, agent_snapshot
from .analysis import analyze_behavior
from .canon import CanonStore
from .engine import run_match
from .mechanical import MechanicalMatchupReport, mechanical_report
from .model import ArenaSpec, BladeSpec
from .reincarnation.normalize import commitment as reincarnation_commitment
from .reincarnation.normalize import canonical_bytes
from .reincarnation_author import BaselineReincarnationAuthor
from .replay import save_match
from .salience import SalienceDetector
from .signatures import SignatureRegistry


def _reincarnation_binding(manifest, commitment_hash: str) -> dict:
    """Canonical binding of a battle-self program (rmreview P0.2).

    Pins the exact AST bytes hash + commitment into the MatchResult so two
    different reincarnation programs can never collide on the same match record.
    """
    import hashlib
    ast_sha = hashlib.sha256(canonical_bytes(manifest)).hexdigest()
    return {
        "reincarnation_id": manifest.reincarnation_id,
        "canonical_ast_sha256": ast_sha,
        "commitment": commitment_hash,
        "compute_class": manifest.compute_class,
        "compiler_version": "RBZ-RC-1",
    }


@dataclass
class BattleAvatar:
    """A locked, match-specific reincarnation (rm7/rm8).

    This is the compiled, sealed battle-self: a ReincarnationManifest + its
    commitment hash. It is NOT a pick from a policy zoo; it is the executable
    incarnation the Agent authored for this contest.
    """
    agent_id: str
    body_id: str
    manifest: Any          # ReincarnationManifest
    commitment: str
    runtime: Any = None    # ReincarnationRuntime (set at compile)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "body_id": self.body_id,
            "reincarnation_id": self.manifest.reincarnation_id,
            "compute_class": self.manifest.compute_class,
            "commitment": self.commitment,
        }


@dataclass
class BattleOutcome:
    match: Any
    mechanical: MechanicalMatchupReport
    avatars: dict[str, BattleAvatar]   # keyed by agent_id
    analysis: dict[str, Any]
    reflections: dict[str, Any]        # keyed by agent_id
    salience: dict[str, Any]           # keyed by agent_id -> list of evidence dicts

    def to_dict(self) -> dict[str, Any]:
        return {
            "mechanical": self.mechanical.to_dict(),
            "avatars": {k: v.to_dict() for k, v in self.avatars.items()},
            "winner": self.match.winner,
            "winner_agent_id": self.winner_agent_id(),
            "match_id": self.match.match_id,
            "replay_digest": self.match.replay_digest,
            "analysis": self.analysis,
            "reflections": self.reflections,
            "salience": self.salience,
        }

    def winner_agent_id(self) -> str | None:
        """Resolve the winning competitor by agent_id, not blade id."""
        for aid, av in self.avatars.items():
            if av.body_id == self.match.winner:
                return aid
        return None


def _evolve_transactional(agent_a: AgentState, agent_b: AgentState,
                          match: Any, analysis: dict,
                          registry: SignatureRegistry,
                          salience_detector: SalienceDetector,
                          report: MechanicalMatchupReport,
                          a_body: str, b_body: str,
                          a_opp_body: str, b_opp_body: str) -> tuple[dict, dict, dict, dict]:
    """Transactional post-match evolution (rm8 P1).

    Both agents are snapshotted at the START. Both reflections and evidence are
    derived from the same pre-match epoch. Only then are the deltas committed.
    This makes evolution deterministic regardless of A/B call order.
    """
    # Pre-match snapshots (immutable epoch).
    pre_a = agent_snapshot(agent_a, 0)
    pre_b = agent_snapshot(agent_b, 0)
    # The opponent's daimon that the OTHER agent observes must be the PRE-MATCH
    # daimon object (unmutated). Keep references before any update.
    daimon_a_pre = _daimon_copy(agent_a)
    daimon_b_pre = _daimon_copy(agent_b)

    # Signature evidence: register into a career registry, ask for confirmed IDs.
    registry.register(match, a_body, agent_a.agent_id, agent_b.agent_id)
    registry.register(match, b_body, agent_b.agent_id, agent_a.agent_id)
    conf_a = registry.confirmed_signature_ids(agent_a.agent_id)
    conf_b = registry.confirmed_signature_ids(agent_b.agent_id)

    # Salience evidence: typed per-agent (upsets, comebacks, streaks).
    sal_a = salience_detector.detect(match, agent_a.agent_id, agent_b.agent_id,
                                     win_probability=report.win_probability)
    sal_b = salience_detector.detect(match, agent_b.agent_id, agent_a.agent_id,
                                     win_probability=report.win_probability)

    # Derive reflections from the SAME pre-match daimons (opponent observes pre-state).
    refl_a = _derive_reflection(agent_a, agent_b, pre_a, pre_b, match,
                                analysis[a_body]["daimon_projection"]["affinities"],
                                agent_a.agent_id, agent_b.agent_id, a_body, b_body)
    refl_b = _derive_reflection(agent_b, agent_a, pre_b, pre_a, match,
                                analysis[b_body]["daimon_projection"]["affinities"],
                                agent_b.agent_id, agent_a.agent_id, b_body, a_body)

    # Commit both deltas atomically (append to each agent).
    agent_a.remember_match(
        opponent_id=agent_b.agent_id, match_id=match.match_id,
        match_affinities=analysis[a_body]["daimon_projection"]["affinities"],
        opponent_daimon=daimon_b_pre,
        result=match.winner, reflection=refl_a.to_dict(),
        confirmed_signature_ids=conf_a,
        salience_evidence_ids=[e.evidence_id() for e in sal_a])
    agent_b.remember_match(
        opponent_id=agent_a.agent_id, match_id=match.match_id,
        match_affinities=analysis[b_body]["daimon_projection"]["affinities"],
        opponent_daimon=daimon_a_pre,
        result=match.winner, reflection=refl_b.to_dict(),
        confirmed_signature_ids=conf_b,
        salience_evidence_ids=[e.evidence_id() for e in sal_b])

    return (refl_a.to_dict(), refl_b.to_dict(),
            {agent_a.agent_id: [e.to_dict() for e in sal_a],
             agent_b.agent_id: [e.to_dict() for e in sal_b]},
            {agent_a.agent_id: conf_a, agent_b.agent_id: conf_b})


def _derive_reflection(agent, opponent, pre_agent, pre_opponent, match,
                       affinities, agent_id, opponent_id, body_id, opp_body_id):
    """Deterministic reflection derived from the pre-match epoch + match facts."""
    from .evolution import PostMatchReflection, _count_events
    won = match.winner == body_id
    self_col = _count_events(match, body_id, "collision")
    opp_col = _count_events(match, opp_body_id, "collision")
    what_worked, what_failed = [], []
    if won:
        what_worked.append("won the match across the sealed-policy rounds")
    else:
        what_failed.append("failed to convert play into a match win")
    if self_col > opp_col:
        what_worked.append("won the contact/impulse trade")
    else:
        what_failed.append("lost the contact/impulse trade")
    return PostMatchReflection(
        agent_id=agent_id, opponent_id=opponent_id, result=match.winner,
        what_worked=what_worked, what_failed=what_failed,
        beliefs=[f"opponent triggered {opp_col} collisions (contact-aggression model)"],
        proposed_experiments=(["test a counter that punishes opponent contact"]
                              if (not won and opp_col > self_col) else []),
    )


def _last_lineage_id(agent: AgentState) -> str:
    """Previous reincarnation id, or '' if this is the first."""
    if agent.reincarnation_history:
        return agent.reincarnation_history[-1]["reincarnation_id"]
    return ""


def _daimon_copy(agent: AgentState):
    """Deep-copy the agent's DaimonState so the opponent observes a pre-match epoch."""
    from .agent import DaimonState
    d = agent.daimon
    return DaimonState(
        affinities=dict(d.affinities),
        stage=d.stage,
        battle_count=d.battle_count,
        name=d.name,
        visual_version=d.visual_version,
        ability_lineage=list(d.ability_lineage),
        confirmed_signature_ids=list(d.confirmed_signature_ids),
        salient_event_ids=list(d.salient_event_ids),
        recent_affinities=[dict(a) for a in d.recent_affinities],
    )


def run_battle(agent_a: AgentState, spec_a: BladeSpec,
               agent_b: AgentState, spec_b: BladeSpec,
               arena: ArenaSpec | None = None,
               mechanical_runs: int = 60, strategic_rounds: int = 5,
               base_seed: int = 9000,
               author_a: BaselineReincarnationAuthor | None = None,
               author_b: BaselineReincarnationAuthor | None = None,
               registry: SignatureRegistry | None = None,
               salience_detector: SalienceDetector | None = None,
               out_dir: str | None = None) -> BattleOutcome:
    arena = arena or ArenaSpec()
    author_a = author_a or BaselineReincarnationAuthor(agent_version=f"{agent_a.agent_id}@1",
                                               author=agent_a.agent_id)
    author_b = author_b or BaselineReincarnationAuthor(agent_version=f"{agent_b.agent_id}@1",
                                               author=agent_b.agent_id)
    registry = registry or SignatureRegistry()
    salience_detector = salience_detector or SalienceDetector()

    # ---- Phase 1: mechanical reveal (public) ----
    report = mechanical_report(spec_a, spec_b, arena,
                               runs=mechanical_runs, base_seed=base_seed, rounds=3)

    # ---- Phase 2: sealed strategic response (reincarnation) ----
    # Agents author a Reincarnation from the public mechanical report. Commit
    # before the exact simulation seed is used (seed timing handled by caller).
    # Each authored machine is part of the agent's reincarnation lineage (r001...).
    nonce = f"{base_seed}|{spec_a.id}|{spec_b.id}"
    rc_id_a = agent_a.next_reincarnation_id()
    rc_id_b = agent_b.next_reincarnation_id()
    parent_a = _last_lineage_id(agent_a)
    parent_b = _last_lineage_id(agent_b)
    man_a = author_a.reincarnate(report, spec_a.id, spec_b.id,
                                 reincarnation_id=rc_id_a, parent_id=parent_a)
    man_b = author_b.reincarnate(report, spec_b.id, spec_a.id,
                                 reincarnation_id=rc_id_b, parent_id=parent_b)
    rt_a = author_a.compile(man_a)
    rt_b = author_b.compile(man_b)
    # The runtime is Policy-compatible (decide(obs) -> Action).
    rt_a.id = man_a.reincarnation_id
    rt_b.id = man_b.reincarnation_id
    avatars = {
        agent_a.agent_id: BattleAvatar(agent_a.agent_id, spec_a.id, man_a,
                                       reincarnation_commitment(man_a, nonce), rt_a),
        agent_b.agent_id: BattleAvatar(agent_b.agent_id, spec_b.id, man_b,
                                       reincarnation_commitment(man_b, nonce), rt_b),
    }

    # ---- Phase 3: best-of-N with locked reincarnation runtimes ----
    # Pin the exact battle-self program (canonical AST digest) into the match.
    bindings = {
        spec_a.id: _reincarnation_binding(man_a, reincarnation_commitment(man_a, nonce)),
        spec_b.id: _reincarnation_binding(man_b, reincarnation_commitment(man_b, nonce)),
    }
    match = run_match(base_seed + 5000, arena, spec_a, spec_b,
                      rt_a, rt_b, strategic_rounds,
                      reincarnation_bindings=bindings)

    analysis = analyze_behavior(match)

    refl_a, refl_b, salience, confirmed = _evolve_transactional(
        agent_a, agent_b, match, analysis, registry, salience_detector, report,
        spec_a.id, spec_b.id, spec_b.id, spec_a.id)

    # Record reincarnation lineage on each persistent agent (rmdev2 Phase 5).
    agent_a.record_reincarnation(
        reincarnation_id=rc_id_a, parent=parent_a,
        target_opponent=agent_b.agent_id,
        strategy_thesis=man_a.strategy_thesis,
        manifest_digest=bindings[spec_a.id]["canonical_ast_sha256"],
        match_result=match.winner, reflection=refl_a)
    agent_b.record_reincarnation(
        reincarnation_id=rc_id_b, parent=parent_b,
        target_opponent=agent_a.agent_id,
        strategy_thesis=man_b.strategy_thesis,
        manifest_digest=bindings[spec_b.id]["canonical_ast_sha256"],
        match_result=match.winner, reflection=refl_b)

    if out_dir:
        from pathlib import Path
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        save_match(match, out / f"battle_{spec_a.id}_vs_{spec_b.id}.json")

    return BattleOutcome(
        match=match, mechanical=report, avatars=avatars,
        analysis=analysis,
        reflections={agent_a.agent_id: refl_a, agent_b.agent_id: refl_b},
        salience=salience,
    )
