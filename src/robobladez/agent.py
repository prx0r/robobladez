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


@dataclass
class DaimonState:
    """Persistent EMA elemental identity, projected from measured behavior.

    Every match contributes its `daimon_projection` affinities; an exponential
    moving average makes identity drift toward how the agent actually plays.
    This is a projection, not a game rule: it never feeds back into the engine.

    Daimon lifecycle (gameplay origin): a baby daimon starts unnamed and
    elemental; once affinities stabilize past a stage threshold it "names
    itself" and may develop ability lineage. Naming is a consequence of
    measured specialization, never an assigned label.
    """
    affinities: dict[str, float] = field(
        default_factory=lambda: {k: 0.2 for k in ELEMENTS}
    )
    manifestation_stage: int = 0
    battle_count: int = 0
    name: str | None = None
    visual_version: str = "v0"
    ability_lineage: list[str] = field(default_factory=list)

    # Stage thresholds by battle count.
    STAGES = ((1, 1), (5, 2), (15, 3), (40, 4))

    def update(self, match_affinities: dict[str, float], alpha: float = 0.4) -> None:
        self.battle_count += 1
        for k in ELEMENTS:
            v = match_affinities.get(k, 0.0)
            self.affinities[k] = alpha * v + (1 - alpha) * self.affinities.get(k, 0.0)
        total = sum(self.affinities.values()) or 1.0
        self.affinities = {k: v / total for k, v in self.affinities.items()}
        self._advance_stage()

    def _advance_stage(self) -> None:
        prev = self.manifestation_stage
        for threshold, stage in self.STAGES:
            if self.battle_count >= threshold:
                self.manifestation_stage = max(self.manifestation_stage, stage)
        if self.manifestation_stage != prev:
            self.visual_version = f"v{self.manifestation_stage}"
        # Naming: the first time the daimon is sufficiently specialized.
        if self.name is None and self.manifestation_stage >= 2:
            self.name = self._generate_name()
            self.ability_lineage.append("signature")  # placeholder for later detection

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
class AgentState:
    """Persistent competitor identity and lineage.

    Seed gives an initial bias; history gives the actual character. Matches the
    `AgentSnapshot` schema. Persistence is between-match only; a match policy
    itself remains sealed (Constitution rule 4).
    """
    agent_id: str
    genesis_seed: str = "unseeded"
    daimon: DaimonState = field(default_factory=DaimonState)
    opponent_models: dict[str, OpponentModel] = field(default_factory=dict)
    policy_versions: list[str] = field(default_factory=list)
    body_versions: list[str] = field(default_factory=list)
    match_history: list[dict[str, Any]] = field(default_factory=list)

    def remember_match(self, opponent_id: str, match_affinities: dict[str, float],
                       opponent_daimon: "DaimonState", result: str | None,
                       reflection: dict[str, Any] | None = None) -> None:
        self.daimon.update(match_affinities)
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

    def profile(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "genesis_seed": self.genesis_seed,
            "daimon": self.daimon.to_dict(),
            "opponent_models": {k: v.to_dict() for k, v in self.opponent_models.items()},
            "policy_versions": self.policy_versions,
            "body_versions": self.body_versions,
            "match_count": len(self.match_history),
            "status": "NARRATIVE_PROJECTION",
        }


def agent_snapshot(agent: AgentState, version: int) -> dict[str, Any]:
    body = agent.profile()
    body["version"] = version
    body["snapshot_hash"] = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode()
    ).hexdigest()[:16]
    return body
