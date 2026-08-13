"""RBZ-RC-1 reincarnation schema (rm7/rm8).

A Reincarnation is the executable machine a persistent Agent authors for a
specific contest. It is a bounded state machine: continuous controls, discrete
states, transitions with conditions, timers, and bounded internal memory.
This module defines the AST schema (plain dicts, JSON-serializable) and the
canonical manifest wrapper that gets hashed and revealed.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

FORMAT = "RBZ-RC-1"

# Compute classes (rm7): regulated computational budget.
COMPUTE_CLASSES = {
    "C1": {"max_states": 32, "max_transitions": 256, "max_memory_bytes": 4096},
    "C2": {"max_states": 128, "max_transitions": 1024, "max_memory_bytes": 32768},
    "C3": {"max_states": 512, "max_transitions": 4096, "max_memory_bytes": 262144},
}

# Legal continuous control names (must match Action model).
CONTROLS = ("radial", "tangential", "torque", "boost")


@dataclass(frozen=True)
class MemorySlot:
    name: str
    type: str = "u8"      # u8|i16|f32
    initial: float = 0
    max_abs: float = 255  # bound on |value|

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReincarnationManifest:
    """Canonical, hash-addressed reincarnation (RBZ-RC-1)."""
    format: str = FORMAT
    reincarnation_id: str = ""
    agent_version: str = ""
    target_match: str = ""
    compute_class: str = "C1"
    author: str = ""            # human_id / agent_id / daimon_id provenance
    parent_reincarnation_id: str = ""
    memory: tuple[MemorySlot, ...] = ()
    states: tuple[dict[str, Any], ...] = ()   # ordered state specs
    initial_state: str = ""
    strategy_thesis: str = ""   # narrative (excluded from executable hash)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "reincarnation_id": self.reincarnation_id,
            "agent_version": self.agent_version,
            "target_match": self.target_match,
            "compute_class": self.compute_class,
            "author": self.author,
            "parent_reincarnation_id": self.parent_reincarnation_id,
            "memory": [m.to_dict() for m in self.memory],
            "states": list(self.states),
            "initial_state": self.initial_state,
        }

    def executable_payload(self) -> dict[str, Any]:
        """The canonical object that is hashed and revealed (rm8: commit exact AST).

        Excludes narrative-only fields (strategy_thesis, author).
        """
        return {
            "format": self.format,
            "agent_version": self.agent_version,
            "target_match": self.target_match,
            "compute_class": self.compute_class,
            "memory": [m.to_dict() for m in self.memory],
            "states": list(self.states),
            "initial_state": self.initial_state,
        }


def parse_memory(specs: list[dict]) -> tuple[MemorySlot, ...]:
    return tuple(MemorySlot(
        name=s.get("name", ""),
        type=s.get("type", "u8"),
        initial=float(s.get("initial", 0)),
        max_abs=float(s.get("max_abs", 255)),
    ) for s in specs)
