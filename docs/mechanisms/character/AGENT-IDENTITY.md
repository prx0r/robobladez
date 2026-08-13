# Mechanism: AGENT IDENTITY

## Purpose
Define what a persistent competitor *is* across matches: a stable identity separate from any
specific body or battle policy. This embodies core idea #2 (persistent character ≠ body ≠ policy)
and is the foundation of the whole character system (rm5 #13).

## Canonical status
ANALYTICS (identity is a projection of history) + the object that GAMEPLAY runs against.

## Inputs
- `agent_id: str` — stable identifier.
- `genesis_seed: str` — the immutable origin.
- Accumulated match history, opponent models, daimon state.

## State
- **Persistent**: `AgentState` (src/robobladez/agent.py):
```
agent_id, genesis_seed,
daimon: DaimonState, opponent_models: dict,
policy_versions: list, body_versions: list, match_history: list
```

## Transition
Identity is constructed from the union of:
1. **GENESIS PRIORS** (seed nudges): a fixed origin/seed.
2. **ACTUAL HISTORY** (determines): every match's `remember_match` updates daimon + opponent
   models + history.
3. **OBSERVED CHARACTER**: the `profile()` projection (see BEHAVIOR-PHENOTYPE).

## Outputs
- `AgentState.profile()` — compact serializable identity snapshot.

## Invariants
1. `agent_id` is immutable.
2. `genesis_seed` is immutable.
3. The agent is distinct from any `BladeSpec` (body) and any `Policy` (battle policy).
4. Identity only ever changes by appending new history/versions — never by rewriting.

## Information visibility
- **PUBLIC**: agent_id, genesis_seed, policy/body version lists, public record.
- **PRIVATE**: internal opponent models, daimon projection until revealed.

## Determinism
- History-driven; no RNG in identity construction.

## Failure modes
- Missing `remember_match` call → stale identity (ensure every match updates).

## Edge cases
- A brand-new agent (no matches) still has a valid identity via genesis defaults.

## Telemetry
- `match_count`, `policy_versions`, `body_versions`, `daimon`, `opponent_models`.

## Versioning
- Versioning is handled by AGENT-VERSIONING (each evolution creates a new `AgentSnapshot`).

## Security
- Identity is analytics; the sealed engine uses only `BladeSpec`+`Policy`. Identity never
  grants engine privileges.

## Tests
- `tests/test_agent.py` (agent remember/model; snapshot serializable).

## Examples
**Normal**: Boris starts with genesis defaults, plays matches, and his `profile()` grows.
**Adversarial**: A body is reused across agents without changing id → would conflate identities;
prevented by requiring unique `agent_id`.

## Non-goals
- Does NOT define body parameters (BLADE-BODY).
- Does NOT define daimon emergence (DAIMON-EMERGENCE).
