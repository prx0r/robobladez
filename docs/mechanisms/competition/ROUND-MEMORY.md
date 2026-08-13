# Mechanism: ROUND MEMORY (Round-Boundary Adaptation)

## Purpose
Define what a policy may and may not carry across round boundaries within a single match.
This is what makes a 5-round match test "how good a learning machine did you submit?" rather
than "who has a better external decision loop" (rm5 #4).

## Canonical status
GAMEPLAY (governs legality of between-round state).

## Inputs
- The submitted `Policy` object (same object reused across all rounds of a match).
- `prior_round_winners: tuple[str|None,...]` — public, passed into each round's Observation.

## State
- **Persistent**: none (a fresh Policy instance is used per match by convention).
- **Ephemeral (legal)**: any attribute the policy mutates on `self` during `decide()`
  (its private match memory). This is the ONLY mutable state that survives between rounds.

## Transition
The three allowed models, and which RoboBladez uses:

| Model | Policy code | Match memory | Between rounds | Policy rewrite |
|-------|------------|--------------|----------------|----------------|
| A. fully sealed static | locked | none | n/a | not allowed |
| B. **sealed code + mutable state (CHOSEN)** | locked | mutable via code | allowed | NOT allowed until next match |
| C. recommit between rounds | may change | n/a | — | allowed each round (REJECTED) |

RoboBladez uses **Model B**: the policy object's code is locked, but its instance attributes
may be updated by its own committed logic during `decide()`. The engine never edits the
policy; it only calls `decide(obs)`. Any state the policy keeps is its own responsibility
and must be deterministic (no wall clock / unseeded RNG).

## Outputs
- No direct output; the effect is that later rounds' decisions may depend on earlier
  rounds' observations and winners.

## Invariants
1. The engine does not mutate the policy between rounds; only the policy mutates itself.
2. `prior_round_winners` is identical for both policies (symmetric public info).
3. A policy may not access the opponent's internal state (only public observations).
4. Round-boundary memory must be reproducible: replaying the match with the same policy
  state-start yields the same outcome.

## Information visibility
- `prior_round_winners` is **PUBLIC** (both see the same tuple).
- A policy's own memory is **PRIVATE** (opponent cannot read it).
- **NEVER**: opponent internal state.

## Determinism
- Allowed only via deterministic code + seeded `policy_rng`. A policy that uses
  `time.time()`/`os.urandom()` would break determinism and is a sandbox violation
  (see POLICY-RUNTIME).

## Failure modes
- Policy relies on uncommitted external state → nondeterministic replay (detected by digest).
- Policy mutates shared/global state affecting the opponent → sandbox violation (Phase 4).

## Edge cases
- First round has empty `prior_round_winners` (policies must handle `()`).
- A draw round appends `None` to `prior_round_winners` (policy must handle `None`).

## Telemetry
- None direct; analysis may infer adaptation by comparing action distributions across rounds.

## Versioning
- Round-memory semantics are part of `ENGINE_VERSION` semantics; changing them requires a
  version bump (they affect determinism contract).

## Security
- Because policies are trusted in-process today, round-memory misuse is possible but
  detectable via replay-digest mismatch. The sandbox (Phase 4) enforces isolation.

## Tests
- `tests/test_agent.py::AgentTests::test_daimon_drifts_toward_behavior` (state accumulates
  across calls — demonstrates legal mutable memory pattern).

## Examples
**Normal**: `ProberPolicy` uses `obs.round_no` to probe early and commit later; its config is
fixed, its decisions vary by round — all deterministic.
**Adversarial**: A policy tries to count wall-clock time between rounds to bias play —
violates determinism; replay digest diverges on re-run.

## Non-goals
- Does NOT allow policy code to change mid-match (that is model C, rejected).
- Does NOT define between-MATCH evolution (see POLICY-EVOLUTION).
