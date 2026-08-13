"""RBZ-RC-1 canonical normalization + commitment (rm8).

`canonical_ast_bytes` is the object that is hashed and later revealed. It is
byte-stable (JSON, sorted keys, no whitespace) so the same machine always
produces the same commitment hash. Narrative metadata (strategy_thesis, author)
is excluded from the executable hash.
"""
from __future__ import annotations
import hashlib, json
from typing import Any

from .schema import ReincarnationManifest
from .validate import validate


def canonical_bytes(manifest: ReincarnationManifest) -> bytes:
    """Byte-stable serialization of the executable payload (not narrative)."""
    validate(manifest)
    payload = manifest.executable_payload()
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def commitment(manifest: ReincarnationManifest, match_challenge_nonce: str = "") -> str:
    """SHA-256 over canonical AST + challenge nonce."""
    payload = {
        "manifest": manifest.executable_payload(),
        "nonce": match_challenge_nonce,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def normalize_manifest(manifest: ReincarnationManifest) -> ReincarnationManifest:
    """Return a canonical, validated copy with deterministic field ordering."""
    validate(manifest)
    # Rebuild to drop any unknown keys and enforce ordering.
    return ReincarnationManifest(
        format=manifest.format,
        reincarnation_id=manifest.reincarnation_id,
        agent_version=manifest.agent_version,
        target_match=manifest.target_match,
        compute_class=manifest.compute_class,
        author=manifest.author,
        parent_reincarnation_id=manifest.parent_reincarnation_id,
        memory=manifest.memory,
        states=manifest.states,
        initial_state=manifest.initial_state,
        strategy_thesis=manifest.strategy_thesis,
    )
