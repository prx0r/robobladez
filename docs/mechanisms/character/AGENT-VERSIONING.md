# Mechanism: AGENT VERSIONING

## Purpose
Ensure a competitor's evolution is fully traceable: every change creates a new immutable
snapshot, and no past version is ever overwritten (Constitution rule 9; rm5 #20). This is what
makes "Boris v1 → v2 → v3" real and verifiable.

## Canonical status
INFRA (storage/versioning) with ANALYTICS meaning (lineage).

## Inputs
- `AgentState` and an integer `version`.
- `agent_snapshot(agent, version)` builds the snapshot.

## State
- **Persistent**: canon `agent_versions` table `(agent_id, version, snapshot_json)`.
- `AgentState.policy_versions` / `body_versions` list the version ids.

## Transition
```
snapshot = agent_snapshot(agent, version)
snapshot["snapshot_hash"] = sha256(canonical_json(profile))
canon.save_agent_version(agent_id, version, snapshot)
```
`agent_snapshot` (src/robobladez/agent.py) returns the profile + version + snapshot_hash, with
`status="NARRATIVE_PROJECTION"` to signal it is a projection, not engine truth.

## Outputs
- A versioned, hash-stamped `AgentSnapshot` persisted to `agent_versions`.

## Invariants
1. `(agent_id, version)` is unique in `agent_versions`.
2. The snapshot hash covers the full profile; any edit breaks it.
3. Never `UPDATE`/`DELETE` a prior version — only `INSERT` new ones.
4. The current pointer (version) advances; history stays intact.

## Information visibility
- **PUBLIC**: full lineage (all versions + hashes) for auditability.

## Determinism
- `agent_snapshot` is a pure function of (agent, version).

## Failure modes
- Version collision → `INSERT OR REPLACE` would overwrite; the schema must enforce uniqueness
  (canon uses `PRIMARY KEY(agent_id, version)`).
- Snapshot not serializable → `json.dumps(default=str)` fallback (shouldn't happen for our types).

## Edge cases
- Version 0 vs 1: genesis is version 1 by convention in the current code.
- Multiple agents: version counters are per-agent.

## Telemetry
- `version`, `snapshot_hash`, `created_at` per row.

## Versioning
- This is the versioning mechanism itself; `version` increments per evolution (POLICY-EVOLUTION).

## Security
- Hash-verified snapshots mean tampering is detectable.

## Tests
- `tests/test_agent.py::test_agent_snapshot_is_serializable`.
- Required: a test that re-saving the same (agent, version) does not corrupt or that a
  modified profile yields a different hash.

## Examples
**Normal**: `agent_snapshot(boris, 1)` then `agent_snapshot(boris, 2)` — two rows, two hashes.
**Adversarial**: Editting `agent_versions` row for v1 → hash mismatch detected on verification.

## Non-goals
- Does NOT decide *when* to evolve (POLICY-EVOLUTION).
- Does NOT define canon corrections (CANON-CORRECTIONS).
