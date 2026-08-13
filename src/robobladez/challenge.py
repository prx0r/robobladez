"""Match challenge + seed commit/reveal protocol (rm8 Commit D).

A deterministic sport needs uncertainty about initial conditions AND replayability.
Protocol:
  1. League publishes a MatchChallenge (arena, bodies, opponents, ruleset,
     seed_commitment_scheme) — WITHOUT the exact simulation seed.
  2. Agents author + commit their reincarnations (or policies).
  3. League closes the strategy phase.
  4. The match seed is derived deterministically from committed inputs.
  5. Engine executes; post-match reveal verifies commitments.

This prevents agents pre-solving the exact launch while preventing the organizer
from changing the seed after seeing policies.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any

from .reincarnation.normalize import commitment as reincarnation_commitment
from .reincarnation.schema import ReincarnationManifest


@dataclass
class MatchChallenge:
    challenge_id: str
    arena_version: str = ""
    ruleset_version: str = ""
    body_versions: dict[str, str] = field(default_factory=dict)  # agent_id -> body_version
    opponent_versions: dict[str, str] = field(default_factory=dict)
    seed_commitment_scheme: str = "H(server_nonce || commitA || commitB || challenge_id)"
    server_nonce: str = ""   # committed before strategy submission, revealed after

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def derive_match_seed(challenge_id: str, commitment_a: str, commitment_b: str,
                      server_nonce: str) -> int:
    """Deterministic, commitment-bound match seed (rm8 detailed review §3)."""
    raw = f"{server_nonce}|{commitment_a}|{commitment_b}|{challenge_id}"
    return int(hashlib.sha256(raw.encode()).hexdigest()[:16], 16)


def build_match_seed(challenge: MatchChallenge, commit_a: str, commit_b: str) -> int:
    return derive_match_seed(challenge.challenge_id, commit_a, commit_b,
                             challenge.server_nonce)


def commit_reincarnation(manifest: ReincarnationManifest, challenge_id: str) -> str:
    """Commit a reincarnation against a challenge (bound to agent/body/opponent)."""
    return reincarnation_commitment(manifest, challenge_id)
