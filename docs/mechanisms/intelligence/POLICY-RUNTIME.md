# Mechanism: POLICY RUNTIME

## Purpose
Define how a `Policy` object is executed by the engine, what resources it may use, and how
violations are handled. This is the correctness layer that must later become the out-of-process
sandbox (rm3, rm4, rmdev Phase 4).

## Canonical status
GAMEPLAY + INFRA (execution contract).

## Inputs
- `policy: Policy` with `decide(obs) -> Action`.
- `observation: Observation`.

## State
- **Ephemeral**: any instance state the policy maintains (ROUND-MEMORY); the engine keeps
  none about the policy except its manifest/commitment.

## Transition
```
1. observe(tick, round_no, me, opp, arena, priors)   # engine builds Observation
2. act = policy.decide(obs)                          # policy runs
3. act = act.clamped()                               # engine validates
4. (Phase 4 sandbox) enforce CPU/mem/timeout/fs/net isolation here
```
Today policies run **in-process** (trusted Python objects). The runtime contract is defined now
so the sandbox (Phase 4) can be dropped in without changing the engine.

## Outputs
- A validated, clamped `Action`.

## Invariants
1. Policy cannot touch engine internals; it only receives `Observation` and returns `Action`.
2. Policy must be deterministic: no wall clock, no `os.urandom`, no unseeded `random`.
3. Engine, not policy, owns physics/collision/energy/win conditions.
4. A policy may keep its own state (ROUND-MEMORY) but must not touch shared global state.

## Information visibility
- Policy sees only its `Observation` (OBSERVATION-MODEL). Its internal state is PRIVATE.

## Determinism
- The critical contract: for the same observation, a policy must produce the same action.
- Policies should draw RNG from a `policy_rng` seeded by the engine (not yet exposed; a
  policy that needs randomness must derive it deterministically from observations/seeds).
- Unseeded `random.random()` is forbidden — it breaks replay digest (rm5 #5).

## Failure modes
| Failure | Detection | Response |
|---|---|---|
| Timeout (Phase 4) | wall-clock budget | idle action; repeated → forfeit |
| Out-of-range action | `clamped()` | clamp (already the rule) |
| Non-finite action | audit check | raise `FloatingPointError` |
| Nondeterminism | replay-digest mismatch on re-run | canonical flag |
| Filesystem/network (Phase 4) | sandbox | reject execution |

## Edge cases
- Energy = 0 → action zeroed (ACTION-MODEL).
- Policy raises an exception → engine must catch (future sandbox: forfeit round).
- Empty `prior_round_winners` on round 1 → policy must handle.

## Telemetry
- Policy id, manifest, commitment per match; per-tick actions in frames.

## Versioning
- `api_version = "rbz-policy-1"` in manifest. Sandbox policy execution, when added, keeps
  this API version for compatibility.

## Security
- This is THE security surface. The sandbox (Phase 4) will execute each policy in its own
  subprocess with Observation JSON → Action JSON, CPU/memory/wall-clock budgets, no network,
  no arbitrary filesystem (rm3 Tank Royale precedent).

## Tests
- `tests/test_engine.py` determinism; `tests/test_protocol.py` commits.
- Required (Phase 4): sandbox isolation, timeout→idle, nondeterminism detection.

## Examples
**Normal**: `CounterPolicy.decide` reads observations and returns an Action each tick.
**Adversarial**: A policy calls `random.random()` unseeded → two runs of the same match
produce different digests → the match is flagged non-reproducible (sandbox would reject).

## Non-goals
- Does NOT run the policy in a sandbox yet (Phase 4 deliverable).
- Does NOT define policy selection (PREMATCH-PLANNING) or evolution (POLICY-EVOLUTION).
