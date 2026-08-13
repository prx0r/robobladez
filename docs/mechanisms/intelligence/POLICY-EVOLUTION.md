# Mechanism: POLICY EVOLUTION

## Purpose
Define how a persistent agent produces a *new version* of its policy between matches, without
ever rewriting history (Constitution rule 9). Evolution is versioned and append-only; it is
deliberately NOT "make the current policy smarter in place."

## Canonical status
ANALYTICS (projection/lineage) — the resulting new policy, once committed, becomes GAMEPLAY
for subsequent matches.

## Inputs
- `AgentState` (history, opponent models, daimons).
- Accumulated `PostMatchReflection`s.
- (Future) a search/evaluation harness over candidate policies.

## State
- **Persistent**: `AgentState.policy_versions: list[str]` (ids of each version), plus the
  stored reflections and opponent models that justify the next version.

## Transition
```
1. evaluate: use match history + opponent models + reflections
2. produce:  a candidate policy version (mutation / re-param / re-selection)
3. validate: candidate satisfies the Policy contract (Observation->Action, deterministic)
4. version:  append to agent.policy_versions; increment version counter
5. snapshot: store AgentSnapshot(version=N) in canon agent_versions
```
Today the transition is descriptive (the zoo of policies + `ReportAwareStrategist` selection
is the seed of this mechanism). Full parameter/evolutionary search is a later deliverable
(rmdev Phase 6.3 / Phase 7 PSRO).

## Outputs
- A new policy version reference appended to `AgentState.policy_versions`.
- A versioned `AgentSnapshot` in the canon store.

## Invariants
1. Never overwrite an old version — evolution creates a new one (Constitution rule 9).
2. The new policy must remain deterministic and inside the action/observation contract.
3. History is immutable; only the *pointer to the current version* changes.
4. An agent may not change its body/policy mid-match (ROUND-MEMORY + MATCH-LIFECYCLE).

## Information visibility
- **PUBLIC**: the set of policy versions and their manifests (post-reveal).
- **PRIVATE**: internal search/evaluation state of the evolution process.

## Determinism
- The evolution process itself must be deterministic (or fully seeded) so lineage is
  reproducible.

## Failure modes
- Candidate violates the contract → rejected, no version created.
- Evaluation overfits to one opponent → mitigated by robustness/diversity objectives
  (rmdev Phase 6.3 fitness).

## Edge cases
- First version: no history yet → genesis defaults (GENESIS-SEED).
- No good candidate found → keep current version (no new version emitted).

## Telemetry
- `policy_versions` list, per-version `AgentSnapshot` hash, version counters.

## Versioning
- Every evolved policy is a distinct version; `AgentSnapshot.version` increments.
- Canon `agent_versions` table stores each (agent_id, version) once (append-only).

## Security
- Evolved policies are still subject to the POLICY-RUNTIME contract and (Phase 4) sandbox.
  Evolution never grants extra engine privileges.

## Tests
- `tests/test_agent.py::AgentTests::test_agent_snapshot_is_serializable` (versioned snapshot).
- Required: a test that two evolution runs from the same history yield the same version set.

## Examples
**Normal**: After losing to an aggressive opponent, Boris produces a `counter-v2` tuned to
punish contact, appended as version 2; version 1 is unchanged in canon.
**Adversarial**: An agent tries to retroactively edit its version-1 policy after a bad match —
blocked: version 1's snapshot hash is immutable in `agent_versions`.

## Non-goals
- Does NOT run the match itself (MATCH-LIFECYCLE owns that).
- Does NOT do PSRO population/meta search yet (see META-EVOLUTION, rmdev Phase 7).
