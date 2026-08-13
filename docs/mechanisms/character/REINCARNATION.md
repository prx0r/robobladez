# Mechanism: REINCARNATION

> **Scope note (rm7):** This doc covers the STORAGE LAYER — persistent identity across model/
> runtime resets. The DEFINING mechanic — where the Agent *writes its own next executable
> incarnation* that fights — is specified in **REINCARNATION-COMPILER.md**, which sits near the
> top of the technical doc stack. Read that first.

## Purpose
Define how a competitor "remains itself" when the LLM/session/model that instantiated it dies
(rm6). Reincarnation is a real engineering problem: identity lives OUTSIDE the model. Boris is
not the LLM process; the LLM is merely the cognitive runtime that instantiates Boris from
versioned state.

The **full** reincarnation concept (rm7) has two layers:
1. **Storage** (this doc): identity persists in versioned snapshots; runtimes are swappable.
2. **Compilation** (REINCARNATION-COMPILER.md): the Agent writes a new executable battle-self
   per match, compiles + seals it, and that incarnation fights. "Battle Avatar" is the
   presentation term; Reincarnation is the actual executable mechanism.

## Canonical status
INFRA (identity persistence) + ANALYTICS (continuity fidelity).

## Inputs
- `AgentSnapshot` (the serialized identity — see AGENT-VERSIONING).
- A model runtime (GPT / Claude / Gemini / local / future).

## State
- **Persistent**: `AgentSnapshot` in canon `agent_versions`. It contains identity, canonical
  memories, beliefs, opponent models, relationships, strategic style, unresolved goals, policy
  lineage, daimon state.

## Transition
```
AgentSnapshot vN
      │
      ├── identity, memories, beliefs, opponent models, relationships,
      ├── strategic style, goals, policy lineage, daimon state
      │
      ▼
 MODEL RUNTIME (interchangeable)
      │
      ▼
   BORIS (the instantiated competitor)
```
The runtime can be swapped (GPT→Claude→Gemini→local) without replacing Boris.

## Outputs
- A restored, instantiated competitor whose continuity can be audited.

## Invariants
1. Identity is serialized OUTSIDE the model; the model is replaceable.
2. `AgentSnapshot.snapshot_hash` verifies the identity was not tampered.
3. Reincarnation restores the same identity, not a new agent.

## Information visibility
- **PUBLIC**: full versioned lineage for auditability.

## Determinism
- Identity restoration is deterministic given the snapshot; the *runtime's responses* are
  NARRATIVE and not required to be deterministic.

## Failure modes
- Missing snapshot → cannot restore (agent must be re-created from genesis).
- Hash mismatch → tampered/corrupt snapshot; continuity cannot be verified.

## Edge cases
- Runtime change mid-career → same snapshot, new runtime (expected and supported).
- Version gap (v1 → v5) → restore from the requested version's snapshot.

## Telemetry
- `version`, `snapshot_hash`, `created_at`; restoration event.

## Versioning
- This mechanism IS the versioning continuity; each evolution writes a new snapshot
  (AGENT-VERSIONING / POLICY-EVOLUTION).

## Security
- Hash-verified snapshots make impersonation/corruption detectable.
- Reincarnation must never grant the restored agent engine privileges beyond a normal agent.

## Tests
- `tests/test_agent.py::test_agent_snapshot_is_serializable`.
- Required: a REINCARNATION AUDIT — ask the new runtime structured questions (who are you,
  last five matches, who is Morty, current weakness, what does the daimon disagree about,
  current body, strongest unresolved prediction) and compare against canonical state to verify
  continuity fidelity (rm6).

## Examples
**Normal**: Boris's snapshot v27 is loaded into a new model; the runtime re-instantiation answers
the audit consistently with v27.
**Adversarial**: A snapshot with an edited `genesis_seed` fails hash verification.

## Non-goals
- Does NOT prove metaphysical identity (only continuity fidelity).
- Does NOT define memory-tier retrieval (that is the Agent AI layer; see rm6 tiers 0–3).
