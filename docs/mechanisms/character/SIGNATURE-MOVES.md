# Mechanism: SIGNATURE MOVES

## Purpose
Detect, from measured replay data, the recurring decisive patterns that constitute a
competitor's "signature move" — the emergent Slipstream mechanic (rm5 #10, rm4). A signature is
only real once it has repeated statistical support across wins and opponents; it is never
preauthored as lore.

## Canonical status
ANALYTICS (detection) → NARRATIVE (naming/visualization).

## Inputs
- `MatchResult` per match (frames with actions + states).
- `blade_id` for the competitor being analyzed.

## State
- **Ephemeral (detector)**: `_counts` — a dict of windowed action/state sequences →
  `{occurrences, wins, match_ids}`.

## Transition
```
FOR each match:
    seq = discretize(frames)   # each frame -> {radial,tangential,torque,boost,speed,spin} in {-1,0,1}/{0,1}
    won = match.winner == blade_id
    FOR each window of length `window` in seq:
        key = tuple(window)
        counts[key].occurrences += 1
        if won: counts[key].wins += 1; add match_id

signatures = [ s for s in counts if s.occurrences >= min_occurrences and s.wins >= 1 ]
sort by (win_count, hit_count) desc; cap at 12
```
`SignatureDetector` in `src/robobladez/signatures.py`. Window default 5, `min_occurrences` 2.

## Outputs
- `Signature`: `{name, pattern, hit_count, win_count, match_ids}`.

## Invariants
1. A signature is measured from replay; never invented.
2. Requires recurrence (`occurrences >= min_occurrences`) AND a winning outcome.
3. Deterministic given the match set.
4. Signature detection never affects the match outcome (analytics).

## Information visibility
- **POST_MATCH/ANALYSIS**: detected signatures revealable; naming is NARRATIVE.

## Determinism
- Pure function of replay frames. Discretization buckets make patterns comparable across
  matches.

## Failure modes
- `window` larger than the sequence → no windows, no signatures.
- Too few matches → no signature meets `min_occurrences` (correctly conservative).

## Edge cases
- A pattern that wins once but recurs rarely → not promoted (false-discovery guard).
- Empty sequence → no signatures.

## Telemetry
- `hit_count`, `win_count`, `match_ids` per signature.

## Versioning
- The discretization + thresholds define signature identity; changing them is a ruleset/
  analytics version change. Naming (Slipstream) is NARRATIVE and stored separately.

## Security
- Analytics only; no engine influence.

## Tests
- `tests/test_agent.py::SignatureTests::test_detector_registers_and_reports`.

## Examples
**Normal**: Boris repeatedly wins using a specific orbit-then-counter window; it accumulates
support and appears as `sig-N`.
**Adversarial**: A random one-off combo wins once — without `min_occurrences` support it is
NOT promoted to a signature (prevents "every random combo becomes a signature").

## Non-goals
- Does NOT name the signature (NARRATIVE layer).
- Does NOT promote a signature into a legal ability (ABILITY-SYSTEM — candidate path D in
  rm5 #9).
