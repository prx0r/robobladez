"""CompetitionEntry + immutable EntrySnapshot (rmdev2 Phase 3).

Stops passing agent/body/version info around separately. A CompetitionEntry is
the first-class identity of a competitor in a match; at match start an
IMMUTABLE EntrySnapshot is taken and used by everything downstream (engine,
canon, media, assets), so "boris:talisman:v0" can never leak when Boris
actually fought with body R17.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import hashlib, json

from .agent import AgentState
from .model import BladeSpec


@dataclass(frozen=True)
class CompetitionEntry:
    """A competitor's identity + body + daimon + author, as a unit."""
    agent_id: str
    agent_version: str = "v1"
    body_id: str = ""
    body_version: str = "R1"
    body_digest: str = ""
    daimon_stage: str = "latent"
    daimon_id: str = ""
    daimon_version: str = ""
    visual_identity_version: str = "R0"
    reincarnation_author_type: str = "baseline"
    reincarnation_author_version: str = "1.0"
    body: BladeSpec | None = None   # concrete body (not serialized into snapshot)

    def entry_key(self) -> str:
        return f"{self.agent_id}:{self.body_id}:{self.body_version}"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("body", None)  # body is a live object, not serialized
        return d


@dataclass(frozen=True)
class EntrySnapshot:
    """Immutable, hashed snapshot of a CompetitionEntry at match start.

    Everything downstream (engine, media, assets) reads from this snapshot, so
    it can never accidentally reference a different body/daimon/visual version.

    rmdev2 Phase 2 hardening: the snapshot pins the EXACT authored reincarnation
    (id + canonical AST digest + commitment), so `execution_digest` changes if
    the battle-self program changes.
    """
    entry: CompetitionEntry
    agent_version: str = "v1"
    body_version: str = "R1"
    body_digest: str = ""
    daimon_stage: str = "latent"
    daimon_id: str = ""
    daimon_version: str = ""
    visual_identity_version: str = "R0"
    reincarnation_author_type: str = "baseline"
    reincarnation_author_version: str = "1.0"
    reincarnation_id: str = ""
    reincarnation_digest: str = ""      # canonical AST sha256 of the battle-self
    reincarnation_commitment: str = ""

    @classmethod
    def from_entry(cls, entry: CompetitionEntry,
                   reincarnation_id: str = "",
                   reincarnation_digest: str = "",
                   reincarnation_commitment: str = "") -> "EntrySnapshot":
        return cls(
            entry=entry,
            agent_version=entry.agent_version,
            body_version=entry.body_version,
            body_digest=entry.body_digest,
            daimon_stage=entry.daimon_stage,
            daimon_id=entry.daimon_id,
            daimon_version=entry.daimon_version,
            visual_identity_version=entry.visual_identity_version,
            reincarnation_author_type=entry.reincarnation_author_type,
            reincarnation_author_version=entry.reincarnation_author_version,
            reincarnation_id=reincarnation_id,
            reincarnation_digest=reincarnation_digest,
            reincarnation_commitment=reincarnation_commitment,
        )

    def digest(self) -> str:
        body = {
            "agent_id": self.entry.agent_id,
            "agent_version": self.agent_version,
            "body_id": self.entry.body_id,
            "body_version": self.body_version,
            "body_digest": self.body_digest,
            "daimon_stage": self.daimon_stage,
            "daimon_id": self.daimon_id,
            "daimon_version": self.daimon_version,
            "visual_identity_version": self.visual_identity_version,
            "reincarnation_author_type": self.reincarnation_author_type,
            "reincarnation_author_version": self.reincarnation_author_version,
            "reincarnation_id": self.reincarnation_id,
            "reincarnation_digest": self.reincarnation_digest,
            "reincarnation_commitment": self.reincarnation_commitment,
        }
        return hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:20]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["entry"] = self.entry.to_dict()
        d["digest"] = self.digest()
        return d


def make_entry(agent: AgentState, body: BladeSpec, body_version: str = "R1",
               daimon_id: str = "", visual_identity_version: str = "R0") -> CompetitionEntry:
    """Build a CompetitionEntry from an AgentState + a concrete body."""
    daimon = agent.daimon
    stage_names = ("latent", "proto", "emerging", "manifest", "developed", "ascended")
    stage_idx = stage_names.index(daimon.stage) if daimon.stage in stage_names else 0
    return CompetitionEntry(
        agent_id=agent.agent_id,
        agent_version="v1",
        body_id=body.id,
        body_version=body_version,
        body_digest=_body_digest(body),
        daimon_stage=daimon.stage,
        daimon_id=daimon_id or (daimon.name.lower() if daimon.name else ""),
        daimon_version=f"R{stage_idx}",
        visual_identity_version=visual_identity_version,
        body=body,
    )


def _body_digest(body: BladeSpec) -> str:
    import hashlib
    body_params = {
        "mass": body.mass, "radius": body.radius,
        "contact_friction": body.contact_friction, "launch_spin": body.launch_spin,
        "control_force": body.control_force, "inertia_factor": body.inertia_factor,
    }
    return hashlib.sha256(
        json.dumps(body_params, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]


@dataclass(frozen=True)
class MatchExecutionManifest:
    """The exact inputs that define a match (rmdev2 Phase 2).

    EXACT MATCH = MatchExecutionManifest. Its digest (execution_digest) is the
    cryptographic core: pin it in the replay, canon, and episode manifests so a
    frame can always be traced to the exact battle-self programs that fought.
    """
    execution_id: str
    engine_version: str = ""
    physics_version: str = ""
    ruleset_version: str = ""
    arena_id: str = "standard-open-bowl-v1"
    arena_version: str = "R1"
    arena_digest: str = ""
    entry_a: dict[str, Any] = field(default_factory=dict)
    entry_b: dict[str, Any] = field(default_factory=dict)
    challenge_nonce: str = ""
    seed: int = 0
    rounds: int = 3

    def execution_digest(self) -> str:
        body = {
            "engine_version": self.engine_version,
            "physics_version": self.physics_version,
            "ruleset_version": self.ruleset_version,
            "arena_id": self.arena_id, "arena_version": self.arena_version,
            "arena_digest": self.arena_digest,
            "entry_a": self.entry_a, "entry_b": self.entry_b,
            "challenge_nonce": self.challenge_nonce,
            "seed": self.seed, "rounds": self.rounds,
        }
        return hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:32]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["execution_digest"] = self.execution_digest()
        return d


def build_execution_manifest(execution_id: str, entry_a: EntrySnapshot,
                             entry_b: EntrySnapshot, seed: int, rounds: int = 3,
                             engine_version: str = "", ruleset_version: str = "R1",
                             challenge_nonce: str = "") -> MatchExecutionManifest:
    """Construct the execution manifest from two immutable entry snapshots."""
    return MatchExecutionManifest(
        execution_id=execution_id,
        engine_version=engine_version or "rbz-core-0.2.0",
        ruleset_version=ruleset_version,
        entry_a=entry_a.to_dict(),
        entry_b=entry_b.to_dict(),
        challenge_nonce=challenge_nonce,
        seed=seed, rounds=rounds,
    )
