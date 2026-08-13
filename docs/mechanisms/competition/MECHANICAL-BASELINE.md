# Mechanism: MECHANICAL BASELINE

## Purpose
Reveal the *mechanical* truth of a body-vs-body matchup **before any strategy is
committed**, so a match is about reasoning against known mechanical asymmetry. This is the
defining RoboBladez mechanic (core idea #1) and the first of the two-phase battle protocol.

## Canonical status
ANALYTICS (public evidence). It informs strategy but never feeds back into the match engine
for the strategic fight.

## Inputs
- `sa, sb: BladeSpec` — the two bodies.
- `arena: ArenaSpec`.
- `runs: int` (default 100), `base_seed: int` (default 5000), `rounds: int` (default 3).
- `passive: PassivePolicy` — control is disabled (zero action) to isolate mechanics.

## State
- **Persistent**: none. Report is deterministic given inputs.
- **Ephemeral**: running totals for per-body metrics.

## Transition
```
1. FOR r in 0..runs-1:
     m = run_match(base_seed + r*999983, arena, sa, sb, passive, passive, rounds)
     tally wins/draws; tally termination reasons; tally per-body:
       avg_speed, avg_spin, center_fraction, collisions_per_round
2. win_probability = normalize(wins / runs)
3. advantages/vulnerabilities = classify(per_body_a, per_body_b, win_a)   # heuristic
```
Seed spacing `*999983` (large prime) decorrelates runs. Passive control ⇒ the two bodies
mostly orbit and often time-draw; the report is a *relative* mechanical profile.

## Outputs
`MechanicalMatchupReport`:
- `a,b,arena,neutral_runs`
- `win_probability: {a:…, b:…, draw:…}`
- `avg_duration_s`, `termination_reasons`
- `per_body: {id: {avg_speed, avg_spin, center_fraction, collisions_per_round}}`
- `advantages`, `vulnerabilities` (lists of human-readable strings)

## Invariants
1. Deterministic given (bodies, arena, runs, base_seed, rounds).
2. `sum(win_probability.values()) == 1.0`.
3. Same bodies+params ⇒ identical report (verified by determinism test).
4. Passive control means no strategy bias; differences are purely mechanical.

## Information visibility
- **PUBLIC_BEFORE_MATCH**: the full report is given to BOTH competitors before they commit
  their strategic policies. It is shared, symmetric, public evidence — not a secret.

## Determinism
- Fully deterministic via fixed seeds. No policy involvement, so no RNG source other than
  the fixed launch jitter inside `run_match`.

## Failure modes
- `runs` too low → noisy report (metrics unstable). No correctness failure.
- Non-finite state → propagates `FloatingPointError` from engine (treated as audit failure).

## Edge cases
- All runs draw (pure passive orbit) → `win_probability` is all-draw; advantages derived from
  per-body stats still meaningful.
- Bodies nearly identical → advantages/vulnerabilities lists may be empty.

## Telemetry
- `neutral_runs`, `win_probability`, `avg_duration_s`, `termination_reasons`,
  `per_body.{avg_speed,avg_spin,center_fraction,collisions_per_round}`,
  `advantages`, `vulnerabilities`.

## Versioning
- The classification heuristics in `_classify` are versioned implicitly by report structure.
  Changing thresholds is a ruleset decision → bump `ruleset` field when a formal schema is added.

## Security
- No policy input, no sandbox surface. Purely internal engine calls.

## Tests
- `tests/test_protocol.py::MechanicalTests::test_report_shape` (shape + determinism).
- Required (not yet written): property test that identical inputs → identical report over
  many param combos; a fuzz test over body presets.

## Examples
**Normal**: `mechanical_report(make_body('balanced'), make_body('heavy'), runs=60)` yields a
win probability and per-body profile; `ReportAwareStrategist` reads it to pick a counter.
**Adversarial**: A competitor tries to pass a non-passive policy to get a favorable baseline —
prevented by construction (baseline always uses `PassivePolicy`).

## Non-goals
- Does NOT simulate strategy. It simulates pure mechanics only.
- Does NOT decide who wins the strategic fight; it only informs policy selection.
