"""RBZ-RC-1 reincarnation lineage (rm7).

Every reincarnation an agent authors is stored append-only and hash-verified:
R001..R027 become historical sports artifacts. This is the lineage store.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

from .schema import ReincarnationManifest
from .normalize import canonical_bytes, commitment


@dataclass
class ReincarnationRecord:
    reincarnation_id: str
    agent_version: str
    target_match: str
    compute_class: str
    commitment_hash: str
    ast_bytes: bytes
    parent_id: str = ""
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "reincarnation_id": self.reincarnation_id,
            "agent_version": self.agent_version,
            "target_match": self.target_match,
            "compute_class": self.compute_class,
            "commitment_hash": self.commitment_hash,
            "ast_bytes_hex": self.ast_bytes.hex(),
            "parent_id": self.parent_id,
            "created_at": self.created_at,
        }


class ReincarnationLineage:
    """Append-only, hash-verified per-agent reincarnation history."""

    def __init__(self):
        self._records: dict[str, list[ReincarnationRecord]] = {}

    def add(self, manifest: ReincarnationManifest, nonce: str = "") -> ReincarnationRecord:
        ast_bytes = canonical_bytes(manifest)
        rec = ReincarnationRecord(
            reincarnation_id=manifest.reincarnation_id,
            agent_version=manifest.agent_version,
            target_match=manifest.target_match,
            compute_class=manifest.compute_class,
            commitment_hash=commitment(manifest, nonce),
            ast_bytes=ast_bytes,
            parent_id=manifest.parent_reincarnation_id,
        )
        self._records.setdefault(manifest.agent_version, []).append(rec)
        return rec

    def history(self, agent_version: str) -> list[ReincarnationRecord]:
        return list(self._records.get(agent_version, []))

    def verify(self, record: ReincarnationRecord, nonce: str = "") -> bool:
        return commitment_hash_from_bytes(record.ast_bytes, nonce) == record.commitment_hash


def commitment_hash_from_bytes(ast_bytes: bytes, nonce: str = "") -> str:
    import hashlib, json
    payload = {"manifest": json.loads(ast_bytes.decode()), "nonce": nonce}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
