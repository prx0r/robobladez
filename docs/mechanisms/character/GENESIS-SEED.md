# Mechanism: GENESIS SEED

## Purpose
Define the immutable origin of a competitor. A seed gives an initial bias; history determines
the actual character (rm5 #13). The genesis seed is fixed forever and anchors all subsequent
versioning (core idea #2).

## Canonical status
ANALYTICS (identity origin) + INFRA (unique, immutable key).

## Inputs
- `agent_id: str`
- `genesis_seed: str` — typically `f"{season_seed}:{agent_id}"`.

## State
- **Persistent**: stored on `AgentState.genesis_seed`. Immutable after creation.

## Transition
```
agent = AgentState(agent_id=aid, genesis_seed=f"{seed}:{aid}")
```
The seed is set once at creation and never modified. It may seed initial daimon priors,
initial policy/body choices, or the agent's initial opponent-model prior.

## Outputs
- The immutable `genesis_seed` string; basis for `agent_snapshot` versioning.

## Invariants
1. `genesis_seed` never changes after creation (Constitution rule 9: append-only).
2. Two different agents have distinct (agent_id, genesis_seed) pairs.
3. Same genesis seed + same history ⇒ same identity.

## Information visibility
- **PUBLIC** (part of the public dossier).

## Determinism
- Seeds are fixed strings; reproducibility of lineage depends on determinism of all downstream
  mechanisms (matches, reflections, evolution).

## Failure modes
- None structural. A collision of (agent_id, genesis_seed) would conflate lineages — must be
  prevented at creation.

## Edge cases
- Default genesis seed `"unseeded"` for ad-hoc agents; production agents always set a real seed.

## Telemetry
- `genesis_seed` in `AgentSnapshot`.

## Versioning
- The seed is the root of the version lineage; every `AgentSnapshot.version` descends from it.

## Security
- Immutable; cannot be tampered after canon write (hash-verified snapshots).

## Tests
- `tests/test_agent.py::test_agent_snapshot_is_serializable` (seed in snapshot).

## Examples
**Normal**: `AgentState("boris", genesis_seed="2026:boris")`.
**Adversarial**: Attempting to change `genesis_seed` post-hoc — blocked because it is set at
construction and snapshots hash the profile.

## Non-goals
- Does NOT define daimon initial element (that is DAIMON-EMERGENCE).
- Does NOT define body (BLADE-BODY).
