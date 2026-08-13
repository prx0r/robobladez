# Mechanism: MATCH LIFECYCLE

## Purpose
Define the exact ordered sequence from two sealed policies to a canonical, digest-verified
match result. This is the backbone of the deterministic competition: it guarantees that
identical inputs produce identical replays (Constitution rules 1–2).

## Canonical status
GAMEPLAY.

## Inputs
- `seed: int` — match seed.
- `arena: ArenaSpec` — arena + timestep + terminal thresholds.
- `spec_a, spec_b: BladeSpec` — two bodies (ids MUST differ).
- `policy_a, policy_b: Policy` — two sealed policies (fingerprinted + committed).
- `rounds: int` — positive odd number (best-of-N). Default 5.

## State
- **Persistent**: none (matches are pure functions of inputs). Canon persistence is a
  separate mechanism (`canon`).
- **Ephemeral**: `wins: dict[str,int]`, `priors: tuple[str|None,...]`, per-round state.

## Transition
```
1. VALIDATE  rounds odd && >=1; spec ids differ; specs valid (mass/radius/inertia>0)
2. match_id = sha256(ENGINE_VERSION|seed|a|b|arena.id)[:20]
3. nonce    = f"{match_id}|{seed}|{ENGINE_VERSION}"
4. manifests = {a: manifest(pa), b: manifest(pb)}      # code sha256 + config
5. commits   = {a: commitment(pa,nonce), b: commitment(pb,nonce)}
6. FOR n in 1..rounds:
     rr = run_round(n, seed + n*1000003, arena, sa,sb,pa,pb, priors)
     results.append(rr); priors += (rr.winner,)
     if rr.winner: wins[rr.winner] += 1
     if max(wins) >= rounds//2 + 1: BREAK            # early majority win
7. winner = a if wins[a]>wins[b] else b if wins[b]>wins[a] else None (draw)
8. replay_digest = sha256(canonical_json(result_to_dict_with_empty_digest))
```
Engine version: `rbz-core-0.2.0` (`ENGINE_VERSION`).

## Outputs
- `MatchResult`: match_id, engine_version, seed, arena, blades, policy_manifests,
  policy_commitments, rounds, wins, winner, replay_digest.
- Canon `Event("round_end", ...)` per round (in each `RoundResult`).

## Invariants
1. Same (seed, arena, body versions, policy manifests, engine version) ⇒ identical `to_dict()`.
2. `verify_replay_digest(m)` returns True iff `m` is unmodified.
3. `rounds` must be odd; even values raise `ValueError`.
4. `sa.id != sb.id` or `ValueError` is raised.
5. A match that reaches the round limit with equal round-wins is a draw (`winner=None`);
   no judge score is fabricated.

## Information visibility
- Policies receive only their own `Observation` each tick (see OBSERVATION-MODEL).
- `prior_round_winners` is passed into each round's Observation (PUBLIC within match).
- Policy manifests/commitments are PUBLIC_BEFORE_MATCH (committed, not revealed).

## Determinism
- `random.Random(seed)` is used ONLY for launch jitter at round start.
- Round seeds derive deterministically: `seed + n*1000003`.
- Policies must use only the seeded `policy_rng` (see POLICY-RUNTIME). No wall clock.

## Failure modes
- Non-finite state during a tick → `FloatingPointError` raised (audit treats as failure).
- Policy timeout/invalid action → handled by POLICY-RUNTIME (idle action / forfeit).
- Even `rounds` → `ValueError`.

## Edge cases
- All rounds draw → `winner=None`.
- Double ring-out in a round → `reason="double_*"`, round winner `None`.
- Majority reached early → match stops before `rounds` rounds; result is still canonical.

## Telemetry
- Per round: `reason`, winner, frames (tick%4), events.
- Per match: `wins`, `winner`, `replay_digest`.

## Versioning
- `ENGINE_VERSION` increments on ANY ruleset/physics change (see BLADE-BODY, STADIUM).
- Historical matches stay reproducible because engine version is embedded in match_id
  and digest (Constitution rule 2; see CANON-VERSIONING).

## Security
- Policies never touch engine state directly; they only return `Action` (see POLICY-RUNTIME).

## Tests
- `tests/test_engine.py::test_exact_determinism`, `test_seed_changes_canon`,
  `test_tie_is_not_awarded`, `test_replay_digest_detects_tamper`, `test_invalid_specs_rejected`.

## Examples
**Normal**: `run_match(5, arena, a, b, CounterPolicy(), AggressivePolicy(), 3)` returns a
MatchResult with ≤3 rounds, a winner or None, and a valid digest.
**Adversarial**: tamper `winner` in `to_dict()` → `verify_replay_digest` returns False.

## Non-goals
- Does NOT define mechanical baseline (see MECHANICAL-BASELINE).
- Does NOT define policy selection/adaptation (see POLICY-COMMIT-REVEAL, ROUND-MEMORY).
