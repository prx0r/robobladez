# RoboBladez Roadmap

Phase status per the canonical dev guide (`uploads/rmdev`) and subsequent reviews. Status:
`DONE` (implemented + tested), `PARTIAL` (implemented, gaps remain), `NEXT` (priority), `PLANNED`.

## Phase 0 — Constitution & mechanism contract — DONE
- CONSTITUTION, GAMEPLAY, PHYSICS_SCOPE docs; versioned MatchResult; replay digest.
- 29 mechanism specs in `docs/mechanisms/` + implementation index `docs/mechanisms/index.yaml`.

## Phase 1 — Make the game strategic — PARTIAL
- 12 policy archetypes + 8 body archetypes (`zoo.py`) — but the battle path now uses
  **reincarnations**, not zoo picks.
- `scripts/run_matrix.py` + `meta.py` (non-transitivity / dominance / seed sensitivity).
- **NEXT**: run the 100k+ matchup experiment and tune until counters emerge (non-transitive meta).

## Phase 2 — Mechanical baseline — DONE
- `mechanical.py` → `MechanicalMatchupReport`; wired into the battle protocol.

## Phase 3 — Policy SDK — PARTIAL
- `Policy` protocol + `Reincarnation` bounded DSL. Full versioned SDK + sandbox is Phase 4.

## Phase 4 — Sandboxed competitors — NEXT
- Out-of-process execution, Observation JSON → Action JSON, CPU/mem/timeout/fs/net limits.
- Robocode Tank Royale precedent (`docs/ltx` research; mechanism POLICY-RUNTIME).

## Phase 5 — League + persistent agents — PARTIAL
- `league.py` round-robin + `run_season` (transactional evolution). Full league DB + rankings
  (Elo, body-independent policy rating, head-to-head, Alpha-Rank) are PLANNED.

## Phase 6 — Agent learning — PARTIAL
- Opponent models, post-match reflection (deterministic analytics). Evolutionary policy
  search with robustness fitness is PLANNED.

## Phase 7 — PSRO / meta evolution — PLANNED
- payoff matrix, best-response, Alpha-Rank, PSRO population. `meta.py` provides the win-rate
  matrix seed.

## Phase 8 — Daimon emergence — DONE (evidence-bearing)
- `DaimonState` structural life-stages from typed salience + confirmed signatures +
  phenotype stability. Naming at MANIFEST. Daimon-AI persona is downstream/NARRATIVE.

## Phase 9 — Signature moves — DONE
- `SignatureRegistry` (career-level, cross-match/opponent). Only confirmed signatures count.

## Phase 10 — Narrative / canon engine — PARTIAL
- canon store + story beats. CanonGraph / narrative detectors (UPSET, REVENGE, STREAK,
  DYNASTY, META_SHIFT) are PLANNED.

## Phase 11 — Content compiler — DONE
- `story.py` → `shots.py` → canonical ShotSpecs with winner/event/identity constraints.

## Phase 12 — Visual asset bible — PLANNED
- versioned character/blade/daimon/signature assets; camera/lighting/UI grammar.

## Phase 13 — LTX production — PARTIAL
- renderer-agnostic pipeline + production queue + retake/reframe + simulated render (no LTX).
- **NEXT**: rent GPU only when a match is worth an episode; connect real backend.
- LTX-2.3 today; LTX-2.5 target (`docs/ltx-2.5/`).

## Phase 14 — QA system — PARTIAL
- deterministic QA vs replay (winner/event/identity). Vision-model QA is PLANNED.

## Phase 15 — Website — PLANNED
- live league, agent pages, match replay viewer, meta page, episodes.

## Phase 16 — Public entrants — PLANNED
- agent template + `rbz test-agent` / `rbz submit`; frozen genesis.

## Phase 17 — Seasons — PLANNED
- qualifiers → playoffs → finals; controlled evolution in-season, redesign off-season.

## Phase 18 — Broader engine reuse — PLANNED
- prehistoric / deep-sea / etc. only after RoboBladez is proven.

## Next concrete work (in order)

1. **Sandbox competitors** (Phase 4) — the biggest correctness gap; enables untrusted entrants.
2. **100k matchup experiment + tuning** (Phase 1) — prove the game is strategically non-trivial.
3. **League DB + rankings** (Phase 5) — Elo + head-to-head + Alpha-Rank.
4. **CI enforcement** — the workflow exists (`.github/workflows/ci.yml`); ensure it gates merges.
5. **CanonGraph + narrative detectors** (Phase 10).

Do not add RL, quantum mechanics, GNNs, or larger LLMs during these phases. The bottleneck is
constitutional correctness and a strategically real game.
