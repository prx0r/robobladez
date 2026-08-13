# Mechanism: RELATIONSHIPS / RIVALRIES

## Purpose
Derive canonical relationships between competitors (rivalries, upsets, counter-relations) from
measured match history, not LLM storytelling. The relationship score is ANALYTICS; naming and
dramatization are NARRATIVE (rm5 #22).

## Canonical status
ANALYTICS (score) → NARRATIVE (name/dramatize).

## Inputs
- Match history between two agents: frequency, winners, close matches, upsets, counters,
  adaptation targeted at the opponent, history length, stakes.

## State
- **Persistent**: derivable from the agents' `match_history` (no separate table yet; a future
  `rivalries` canon reducer would materialize it).

## Transition
```
FOR each ordered pair (A,B):
    score = f(match_frequency, upsets, close_matches,
              counter_relationship, adaptation_evidence, stakes)
rivalry is canonical when score crosses a threshold
LLM names/dramatizes afterward (NARRATIVE)
```
Exact formula is not yet implemented — this spec fixes the inputs and the principle.

## Outputs
- A `rivalry_score` per pair; canonical `RIVALRY_CHANGED` events once reducers exist.

## Invariants
1. Derived only from measured match outcomes (no invented drama).
2. Asymmetric (A's model of B can differ from B's model of A).
3. Never affects match outcomes (analytics).

## Information visibility
- **POST_MATCH/ANALYSIS**: rivalry revealable.

## Determinism
- Pure function of history.

## Failure modes
- Insufficient data → low-confidence score (no rivalry).

## Edge cases
- One-sided history (A always beats B) → high frequency, low upset → "dominance" not "rivalry".

## Telemetry
- Per-pair: match count, upsets, close matches, counter evidence.

## Versioning
- Relationship state is versioned like other canon-derived projections.

## Security
- Analytics only.

## Tests
- Not yet implemented; required: a test that rivalry score increases with close/upset matches.

## Examples
**Normal**: A and B split 5–5 with 3 upsets → high rivalry score.
**Adversarial**: An LLM claims a rivalry with zero supporting matches — blocked: score must
come from measured history.

## Non-goals
- Does NOT generate prose (NARRATIVE layer downstream).
