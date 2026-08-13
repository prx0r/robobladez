from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import hashlib, json

# Constitution rule 10: nothing is called "emergent" unless measured from
# interaction rather than hard-coded as lore. These modules implement the
# BUILD_NEXT stage-5/6 projection layer: persistent identity and opponent
# models are built purely from observed match behavior and are always
# non-causal with respect to the engine (Constitution rule 8).

ELEMENTS = ("earth", "water", "fire", "air", "aether")


# Daimon life-stages (rm6): structural achievements, not linear XP.
# LATENT (0) genesis -> PROTO (1) >=10 matches stable phenotype ->
# EMERGING (2) >=25 matches + signature candidates + stable affinity ->
# MANIFEST (3) stable phenotype + salient career event + behavioral coherence ->
# DEVELOPED (4) successful Agent<->Daimon coordination + multiple signatures ->
# ASCENDED (5) rare major career conditions.
DAIMON_STAGES = ("latent", "proto", "emerging", "manifest", "developed", "ascended")


@dataclass
class DaimonState:
    """Persistent companion identity, projected from measured behavior (rm6).

    Two layers:
      1. UNDERLYING STATE (grounded, ANALYTICS): behavior phenotype, elemental
         affinities, signature patterns, career salience, battle count.
      2. INTELLIGENCE (NARRATIVE, downstream): once MANIFEST, an AI persona may
         be conditioned on this state to "talk to" the agent. This module only
         implements the grounded state; the persona is an external projection.

    The daimon is a persistent AI companion that does NOT exist fully at
    genesis: it coheres from lived competitive history and, upon MANIFEST,
    becomes a second, distinct perspective alongside the agent (rm6). It is
    explicitly non-causal with respect to the engine (Constitution rule 8).
    """
    affinities: dict[str, float] = field(
        default_factory=lambda: {k: 0.2 for k in ELEMENTS}
    )
    stage: str = "latent"          # one of DAIMON_STAGES
    battle_count: int = 0
    name: str | None = None
    visual_version: str = "v0"
    ability_lineage: list[str] = field(default_factory=list)
    signature_candidates: int = 0  # number of distinct measured recurring patterns
    salient_events: int = 0        # career-defining moments (upsets, streaks)
    contradiction_count: int = 0   # times self-concept diverged from measured behavior

    # Structural stage requirements (rm6): all must be met to advance.
    # stage_index: (min_battles, min_signature_candidates, min_salient_events)
    STAGE_REQ = {
        1: (10, 0, 0),    # proto
        2: (25, 1, 0),    # emerging
        3: (40, 2, 1),    # manifest
        4: (60, 4, 3),    # developed
        5: (90, 6, 6),    # ascended
    }

    def update(self, match_affinities: dict[str, float], alpha: float = 0.4,
               has_signature: bool = False, salient: bool = False) -> None:
        self.battle_count += 1
        for k in ELEMENTS:
            v = match_affinities.get(k, 0.0)
            self.affinities[k] = alpha * v + (1 - alpha) * self.affinities.get(k, 0.0)
        total = sum(self.affinities.values()) or 1.0
        self.affinities = {k: v / total for k, v in self.affinities.items()}
        if has_signature:
            self.signature_candidates += 1
        if salient:
            self.salient_events += 1
        self._advance_stage()

    def _advance_stage(self) -> None:
        idx = DAIMON_STAGES.index(self.stage)
        # Advance as far as structural requirements allow.
        while idx < len(DAIMON_STAGES) - 1:
            nb, ns, ne = self.STAGE_REQ.get(idx + 1, (1 << 30,) * 3)
            if (self.battle_count >= nb and self.signature_candidates >= ns
                    and self.salient_events >= ne):
                idx += 1
            else:
                break
        new_stage = DAIMON_STAGES[idx]
        if new_stage != self.stage:
            self.stage = new_stage
            self.visual_version = f"v{idx}"
            # Naming happens at MANIFEST (rm6: daimon becomes a real companion).
            if self.name is None and idx >= 3:
                self.name = self._generate_name()
                self.ability_lineage.append("signature")

    def _generate_name(self) -> str:
        dom = self.dominant()
        root = {"earth": "terra", "water": "penelope", "fire": "magma",
                "air": "zephyr", "aether": "nova"}.get(dom, "daemon")
        return f"{root.capitalize()}-{self.battle_count}"

    def dominant(self) -> str:
        return max(self.affinities, key=self.affinities.get)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OpponentModel:
    agent_id: str
    matches: int = 0
    wins: int = 0
    dominant_elements: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def observe(self, opponent_daimon: "DaimonState", result: str | None,
                self_agent_id: str) -> None:
        self.matches += 1
        if result == self_agent_id:
            self.wins += 1
        dom = opponent_daimon.dominant()
        if not self.dominant_elements or self.dominant_elements[-1] != dom:
            self.dominant_elements.append(dom)
            if len(self.dominant_elements) > 8:
                self.dominant_elements = self.dominant_elements[-8:]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HumanInteractionEvent:
    """A canonical record of human-agent interaction (rm6).

    Human influence is explicit and append-only: genesis, coaching, engineering
    approval, and strategic conversation are all stored as events, never as
    silent mutation of the agent. `adopted` records whether the agent followed
    the advice, which builds shared history and is itself a character signal.
    """
    type: str                      # MENTOR_ADVICE | GENESIS | APPROVAL | CONVERSATION
    human: str
    agent: str
    content: str
    timestamp: str = ""
    agent_response: str = ""
    adopted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentState:
    """Persistent competitor identity and lineage.

    Seed gives an initial bias; history gives the actual character. Matches the
    `AgentSnapshot` schema. Persistence is between-match only; a match policy
    itself remains sealed (Constitution rule 4).

    rm6 five-actors: the Agent is distinct from its Daimon, its Talisman (body),
    and any BattleAvatar. The human is owner/mentor, not joystick operator.
    """
    agent_id: str
    genesis_seed: str = "unseeded"
    daimon: DaimonState = field(default_factory=DaimonState)
    opponent_models: dict[str, OpponentModel] = field(default_factory=dict)
    policy_versions: list[str] = field(default_factory=list)
    body_versions: list[str] = field(default_factory=list)
    match_history: list[dict[str, Any]] = field(default_factory=list)
    interactions: list[dict[str, Any]] = field(default_factory=list)  # HumanInteractionEvent
    goals: list[str] = field(default_factory=list)

    def remember_match(self, opponent_id: str, match_affinities: dict[str, float],
                       opponent_daimon: "DaimonState", result: str | None,
                       reflection: dict[str, Any] | None = None,
                       has_signature: bool = False, salient: bool = False) -> None:
        self.daimon.update(match_affinities, has_signature=has_signature,
                           salient=salient)
        model = self.opponent_models.setdefault(
            opponent_id, OpponentModel(opponent_id))
        model.observe(opponent_daimon, result, self.agent_id)
        self.match_history.append({
            "opponent": opponent_id,
            "result": result,
            "reflection": reflection or {},
        })
        if len(self.match_history) > 200:
            self.match_history = self.match_history[-200:]

    def add_interaction(self, ev: HumanInteractionEvent) -> None:
        """Record a human interaction as a canonical event (rm6)."""
        self.interactions.append(ev.to_dict())

    def profile(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "genesis_seed": self.genesis_seed,
            "daimon": self.daimon.to_dict(),
            "opponent_models": {k: v.to_dict() for k, v in self.opponent_models.items()},
            "policy_versions": self.policy_versions,
            "body_versions": self.body_versions,
            "match_count": len(self.match_history),
            "interaction_count": len(self.interactions),
            "goals": self.goals,
            "status": "NARRATIVE_PROJECTION",
        }


def agent_snapshot(agent: AgentState, version: int) -> dict[str, Any]:
    body = agent.profile()
    body["version"] = version
    body["snapshot_hash"] = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode()
    ).hexdigest()[:16]
    return body
