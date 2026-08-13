# Mechanism: DAIMON EMERGENCE

## Purpose
Define how a "daimon" — a persistent AI companion — emerges from measured competitive history.
The daimon is a *second intelligence* associated with a competitor, not a statistical label
(rm6). It does not exist fully at genesis; it coheres from lived history, and once it
MANIFESTs it becomes a distinct perspective the agent can interact with.

## Canonical status
Two layers (rm6):
- **UNDERLYING STATE** — ANALYTICS: grounded, derived from behavior phenotype, signatures,
  career salience, elemental affinities.
- **INTELLIGENCE** — NARRATIVE: once MANIFEST, an external AI persona may be conditioned on
  this state. This module implements the grounded state only.

## Inputs
- Per-match `daimon_projection.affinities` (from `analyze_behavior`).
- `has_signature: bool` — a recurring winning pattern was detected (SIGNATURE-MOVES).
- `salient: bool` — the match was a career-defining event (e.g. an upset/win).
- `DaimonState` (persistent).

## State
- **Persistent** (`DaimonState`, src/robobladez/agent.py):
```
affinities: dict, stage: str, battle_count: int, name: str|None,
visual_version: str, ability_lineage: list,
signature_candidates: int, salient_events: int, contradiction_count: int
```

## Transition
```
FOR each match:
    battle_count += 1
    affinities = EMA(affinities, match_affinities, alpha=0.4); normalize to 1
    if has_signature: signature_candidates += 1
    if salient:       salient_events += 1
    advance_stage(): move through DAIMON_STAGES while all structural reqs met
```
Life-stages (structural achievements, NOT linear XP — rm6):

| Stage | Index | Requirements (battles, signatures, salient) |
|-------|-------|---------------------------------------------|
| latent    | 0 | genesis |
| proto     | 1 | ≥10 battles, stable phenotype emerging |
| emerging  | 2 | ≥25 battles, ≥1 signature candidate, stable affinity |
| manifest  | 3 | ≥40 battles, ≥2 signatures, ≥1 salient event, coherence |
| developed | 4 | ≥60 battles, ≥4 signatures, ≥3 salient, Agent↔Daimon coordination |
| ascended  | 5 | ≥90 battles, ≥6 signatures, ≥6 salient, rare career conditions |

Stage requirements table: `DaimonState.STAGE_REQ`. Naming occurs at MANIFEST (stage ≥3).

## Outputs
- `DaimonState.to_dict()`: affinities, stage, battle_count, name, visual_version,
  ability_lineage, signature_candidates, salient_events, contradiction_count.

## Invariants
1. Affinities always sum to 1.0.
2. Stage is determined ONLY by structural requirements — many battles with no signatures/
   salient events cannot reach MANIFEST (proven by test `test_structural_stages_not_linear_xp`).
3. A daimon is NEVER assigned an element as gameplay truth — element is EMA-projected.
4. Naming happens once, at MANIFEST, and is irreversible.
5. The daimon has NO causal power over the sealed engine (Constitution rule 8).

## Information visibility
- **POST_MATCH/ANALYSIS**: affinities, stage, name revealable.
- **NEVER**: daimon does not influence gameplay.

## Determinism
- EMA + stage advancement are pure functions of inputs; name generation is deterministic.

## Failure modes
- Non-normalized affinities input → normalized internally (`or 1.0` guard).

## Edge cases
- battle_count 0 → stage "latent", unnamed, uniform affinities (baby daimon).
- Two elements nearly tied → `max()` deterministic.

## Telemetry
- `battle_count`, `stage`, `name`, `affinities`, `signature_candidates`, `salient_events`.

## Versioning
- Stage thresholds are NARRATIVE-versioned; changing them changes projections, never canon.

## Security
- Analytics/Narrative only; no engine access.

## Tests
- `tests/test_agent.py` (EMA accumulate/drift).
- `tests/test_protocol.py::DaimonTests` (manifest at structural threshold; not linear XP).

## Examples
**Normal**: 45 battles with periodic signatures + salient wins → `stage="manifest"`, named.
**Adversarial**: 60 battles but zero signatures/salient events → stuck at `"proto"` (no
naming) — structural, not power-creep.

## Non-goals
- Does NOT define the AI persona that talks to the agent (external NARRATIVE layer).
- Does NOT define signature detection (SIGNATURE-MOVES).
- Does NOT define ability acquisition (ABILITY-SYSTEM).
