# Mechanism: OBSERVATION MODEL

## Purpose
Define exactly what information a policy may observe each tick. This determines the game's
information structure (perfect / imperfect / partial observation) and therefore its actual
game theory (rm5 #2). The observation is the full, legal input a policy's `decide()` may read.

## Canonical status
GAMEPLAY (the observation schema is the policy API contract).

## Inputs
Computed by the engine from the current world state at tick `t`, before decisions.

## State
- **Ephemeral**: one `Observation` per blade per tick, derived from the frozen state.

## Transition
```
STATE(t)  →  freeze  →  Observation_A(t), Observation_B(t)  →  (policies decide)
```
Both observations are derived from the SAME pre-step state, so neither sees the other's
action before committing (SIMULTANEOUS-DECISION).

## Outputs
`Observation` (frozen dataclass):
```
tick, round_no
self_pos: Vec2, self_vel: Vec2, self_omega, self_energy, self_integrity
opponent_pos: Vec2, opponent_vel: Vec2, opponent_omega, opponent_energy, opponent_integrity
arena_radius: float
prior_round_winners: tuple[str|None, ...]
```

## Invariants
1. A policy sees only its OWN energy/integrity and the opponent's energy/integrity/spin
   (a design choice — energy/integrity ARE observable).
2. It NEVER sees the opponent's action or internal policy state.
3. `prior_round_winners` is identical for both policies.
4. The observation is deterministic given state — no hidden RNG.

## Information visibility
- **OBSERVABLE_DURING**: positions, velocities, spin, energy, integrity (self and opponent),
  arena_radius, prior_round_winners.
- **NEVER**: opponent's internal policy state, opponent's committed-but-unrevealed policy,
  future actions.

## Determinism
- Observation contains only floats/ints/tuples derived from deterministic state. No time
  of day, no counters the policy can't reproduce.

## Failure modes
- N/A (engine constructs it; no failure path). A malformed policy reading beyond these
  fields is a sandbox concern (POLICY-RUNTIME).

## Edge cases
- First round: `prior_round_winners == ()`.
- `opponent_pos == self_pos` possible at exact overlap → policies must guard zero vector.

## Telemetry
- Observed values are part of each `Frame` (positions/velocities/omega/energy/integrity),
  recorded in the replay for post-hoc analysis.

## Versioning
- Adding/removing an observation field is a policy-API change → bump `api_version`
  (`rbz-policy-1`) and `ENGINE_VERSION` semantics.

## Security
- The observation schema is the sandbox's enforced "legal information" contract (Phase 4).

## Tests
- Structural: `tests/test_engine.py` determinism tests implicitly cover observation equality
  (same state ⇒ same observation ⇒ same actions).

## Examples
**Normal**: `CenterControlPolicy.decide` reads `self_pos.norm()/arena_radius` to steer inward.
**Adversarial**: A policy attempts to access `obs.opponent_*internal*` — such a field does not
exist in the schema; with the sandbox it is unreadable.

## Non-goals
- Does NOT define what is public before the match (see MECHANICAL-BASELINE, MATCH-LIFECYCLE).
- Does NOT define action format (see ACTION-MODEL).
