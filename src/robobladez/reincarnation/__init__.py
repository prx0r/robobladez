"""RBZ-RC-1 reincarnation compiler (rm7/rm8).

Persistent Agent -> authored Reincarnation AST -> validate -> normalize ->
commit canonical manifest -> interpreter BattleExecutable.
"""
from .schema import ReincarnationManifest, MemorySlot, parse_memory, FORMAT, COMPUTE_CLASSES
from .validate import validate, ValidationError
from .normalize import canonical_bytes, commitment, normalize_manifest
from .runtime import ReincarnationRuntime
from .lineage import ReincarnationLineage, ReincarnationRecord

__all__ = [
    "ReincarnationManifest", "MemorySlot", "parse_memory",
    "FORMAT", "COMPUTE_CLASSES",
    "validate", "ValidationError",
    "canonical_bytes", "commitment", "normalize_manifest",
    "ReincarnationRuntime", "ReincarnationLineage", "ReincarnationRecord",
]
