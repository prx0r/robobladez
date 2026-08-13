# Mechanism: RING-OUT / SPIN-OUT (Terminal Conditions)

## Purpose
Define the non-KO ways a round ends, alongside burst (INTEGRITY-BURST). These produce a healthy
mix of termination reasons, which is an exit condition for game balance (rmdev Phase 1.4).

## Canonical status
GAMEPLAY.

## Inputs
- `BladeState` (pos, omega, integrity), `BladeSpec`, `ArenaSpec` (`radius`, `min_spin`,
  `spinout_grace_s`), current time `t`.

## State
- **Ephemeral**: evaluated each tick after integration.

## Transition
```
_terminal(state, spec, arena, t):
  if |pos| - spec.radius > arena.radius:  return "ring_out"
  if state.integrity <= 0:                return "burst"          # (see INTEGRITY-BURST)
  if t >= spinout_grace_s and |omega| < min_spin: return "spin_out"
  return None

round end:
  ta, tb = terminal(a), terminal(b)
  if ta and not tb: winner = b; reason = ta
  if tb and not ta: winner = a; reason = tb
  if ta and tb:     winner = None; reason = f"double_{ta}"
  if neither and time limit: winner=None; reason="time_draw"
```
`min_spin=24.0`, `spinout_grace_s=1.0` (defaults).

## Outputs
- Round winner (or None) + `reason` string.

## Invariants
1. Ring-out checked as center-to-rim distance minus blade radius vs arena radius.
2. Spin-out requires `t >= spinout_grace_s` (blades have a launch grace period).
3. At the time limit, a tie is a draw — NO judge score is fabricated (Constitution).
4. If both terminal simultaneously → `winner=None` (double).

## Information visibility
- Terminal events are public (POST_MATCH); policies can't react within the tick that ends it.

## Determinism
- Pure function of state + time.

## Failure modes
- None structural.

## Edge cases
- Both ring out same tick → `double_ring_out`, round draw.
- Omega below min at t=0 → grace period prevents instant spin-out.
- Ring-out + burst same tick → both terminal; first `if` returns ring_out for that blade.

## Telemetry
- `round_end` event with `reason`; per-round `reason` recorded in `RoundResult`.

## Versioning
- Terminal rules are `ENGINE_VERSION`-relevant.

## Security
- None (numeric).

## Tests
- `tests/test_engine.py` termination + determinism over many seeds; `tests/test_physics.py`.

## Examples
**Normal**: A blade pushed past the rim → `ring_out`, opponent wins the round.
**Adversarial**: A blade stops spinning just after grace → `spin_out`.

## Non-goals
- Does NOT define burst (INTEGRITY-BURST).
- Does NOT define the bowl force (STADIUM).
