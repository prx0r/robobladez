# RoboBladez — Handover & Onboarding

Everything a new agent needs to pick up this project. Read this first.

## What this is

RoboBladez is a deterministic AI-vs-AI spinning-top competition engine plus a
canon-building media pipeline. The defining mechanic (rm7/rmdev2): a persistent
Agent **writes its own sealed executable battle-self (a RBZ-RC-1 reincarnation)**
each match, that self fights deterministically, and the result becomes immutable
canon that changes the Agent — then canonical events/visual assets drive LTX.

It is a **CPU-first modular monolith**. No GPU, no numpy, no pybullet, no external
services required for the core. LTX/LLMs are replaceable backends.

## Quick start

```bash
export PYTHONPATH=src
python -m robobladez.cli mvp --out out/mvp --seed 2026 --rounds 3
# -> one complete vertical slice (competition/canon/visual/story/shots/controls/qa)
python -m robobladez.cli simulate --out out/sim   # 3-agent full stack (no LTX)
python -m unittest discover -s tests -v            # 67 fast tests
```

## Repository map

| Path | Role |
|---|---|
| `src/robobladez/engine.py` `physics.py` `model.py` | deterministic match kernel |
| `src/robobladez/reincarnation/` | RBZ-RC-1 compiler/interpreter (schema/validate/normalize/runtime/lineage) |
| `src/robobladez/reincarnation_author.py` | `ReincarnationContext` + `BaselineReincarnationAuthor` |
| `src/robobladez/battle.py` | two-phase battle protocol (mechanical reveal → sealed → best-of-N) |
| `src/robobladez/competition.py` | `CompetitionEntry`, `EntrySnapshot`, `MatchExecutionManifest` |
| `src/robobladez/challenge.py` | MatchChallenge + seed commit/reveal |
| `src/robobladez/canonical.py` | first-class `CanonicalEvent` (IDs + pre/post state) |
| `src/robobladez/significance.py` | `SignificanceDetector` → story beats |
| `src/robobladez/story.py` | episode compiler (beats reference canonical event IDs) |
| `src/robobladez/agent.py` | AgentState, DaimonState, reincarnation lineage, opponent models |
| `src/robobladez/evolution.py` | PostMatchReflection |
| `src/robobladez/salience.py` `signatures.py` | evidence-bearing emergence |
| `src/robobladez/mechanical.py` | mechanical baseline report |
| `src/robobladez/assets.py` | VisualSpec/AssetLibrary/VisualForge/AssetResolver |
| `src/robobladez/media.py` | ShotSpec v2, RenderQueue, BindingQA/VisualQA, retake/reframe |
| `src/robobladez/control_frames.py` | deterministic first/last control plates |
| `src/robobladez/shots.py` | story → ShotSpec v2 (basis_event_ids, control planning) |
| `src/robobladez/mvp.py` | one-command vertical slice (`robobladez mvp`) |
| `src/robobladez/simulate.py` | full-stack CPU simulation harness |
| `src/robobladez/league.py` | round-robin + season |
| `src/robobladez/canon.py` | SQLite canon store |
| `src/robobladez/meta.py`, `scripts/run_matrix.py` | matchup matrix + non-transitivity (legacy POLICY_ZOO path) |
| `src/robobladez/zoo.py` | body presets + legacy policy archetypes |
| `src/robobladez/demo.py` | single match demo |

## The five actors (never collapse)

```
HUMAN  owner/mentor (no joystick)   AGENT  persistent AI competitor
DAIMON emergent companion (non-causal)   BODY  talisman
REINCARNATION  the compiled battle-self that fights
```

`Agent != Reincarnation != Body != Daimon`.

## Live / legacy / unwired (full audit)

### LIVE (wired, tested, used by mvp/simulate)
- reincarnation compiler + baseline author + battle protocol + lineage
- deterministic kernel, mechanical baseline, commit/reveal, execution manifest
- canonical events, significance, story, shot spec v2, control planner, control frames
- asset library + forge + resolver, media pipeline (mock render), binding QA
- agent/daimon/opponent-model/reflection, salience/signature (evidence-bearing)
- canon store, mvp/simulate/demo/season CLI commands

### LEGACY (still present, superseded — do not build on)
- `zoo.py` `POLICY_ZOO` 12 policy archetypes + `run_matrix.py`/`meta.py`: the
  pre-reincarnation strategy space. Reincarnation supersedes policy zoo. These
  remain useful for *balance research* but are NOT the battle path.
- `docs/archive/` — v1 docs (GAME_RULES, BUILD_ORDER, DATA_MODEL, EVOLUTION,
  EXTERNAL-INFRA, PEER_REVIEW_V1).
- `demo.py` — a simpler single-match demo; `mvp`/`simulate` supersede it.
- `docs/BUILD_NEXT.md`, `docs/SOURCE_COVERAGE.md` — earlier roadmap/coverage notes.

### UNWIRED / NEXT (specified, not fully built)
- `LLMReincarnationAuthor` (Phase 4) — the "AI truly writes itself" backend. The
  interface (`ReincarnationContext`) exists; only `BaselineReincarnationAuthor` is done.
- Real `LTX25Renderer` / image-gen backend (Phase 10/16) — currently mock.
- `VisualQA`/`EventQA` on real footage (Phase 17) — currently BindingQA only;
  `retake_loop` + `EpisodeAssembler` exist but drive mock render/QA.
- Daimon visual packs tied to actual manifestation (Phase 21).
- Autonomous season mini-loop (Phase 22), then 100k meta audit (Phase 6).
- CI workflow exists (`.github/workflows/ci.yml`) but not yet branch-enforced.

Provenance is now verified: `execution_digest` changes when the battle-self AST
changes, and the episode manifest carries real `shot_spec_digests` +
`final_master_digest` (tests/test_provenance.py).

## What NOT to build yet (defer)
Public entrant SDK, website, spectator frontend, PSRO, Alpha-Rank, 100 bodies,
20 ability families, economy, live streaming, custom LTX LoRAs, complex 3D arena.

## Doc index

- `docs/HANDOVER.md` — this file
- `docs/ARCHITECTURE.md` — current architecture + boundaries
- `docs/MVP.md` — the one vertical slice (what "working" means)
- `docs/ROADMAP.md` — phase status
- `docs/CONSTITUTION.md` — hard contract (incl. visual-asset rules)
- `docs/MEDIA_PIPELINE.md`, `docs/MEDIA_STRATEGY.md`, `docs/VISUAL_ASSETS.md` — media layer
- `docs/BLADE.md` — what a blade is (material, editing regime, game theory)
- `docs/TESTING.md` — strict test notes
- `docs/mechanisms/` — 29 mechanism specs + `index.yaml` implementation status
- `docs/ltx/`, `docs/ltx-2.5/` — LTX production research packs

## Test discipline
- All 67 tests are fast (<2s each), no LTX/network/hanging.
- Renders are mocked (`mock://`); real footage QA never auto-passes.
- Determinism: `robobladez mvp` with the same seed must reproduce the same
  execution_digest and replay_digest.

## The one test that proves the MVP
`robobladez mvp --out out/mvp --seed 2026 --rounds 3` produces a directory where
every artifact links to its parents (RUN.json → execution_digest → entries →
reincarnations → match → events → shots → controls → qa). If that tree exists
and is internally consistent, the MVP exists.

---

## Next agent: high-urgency priorities (in order)

These are what block "the AI truly writes itself" and real footage. Do them in
this order. Each is a discrete commit.

### 1. LLMReincarnationAuthor — THE core unmet promise (highest priority)
The defining RoboBladez mechanic is "the persistent AI writes its own battle-self."
Today only `BaselineReincarnationAuthor` (a deterministic heuristic over the
mechanical report) exists. The `ReincarnationContext` + `ReincarnationAuthor`
protocol are ready; implement a real author that:
- takes a `ReincarnationContext` (agent snapshot, mechanical report, opponent
  model, lineage, reflections, daimon advice, human messages)
- calls an LLM that returns **RBZ-RC-1 JSON** (not Python)
- parses → validate → normalize → commit; invalid output falls back to baseline
- produces **materially different** machines than baseline (prove with a test)

Exit test: two agents author different RBZ-RC-1 machines from the same report,
and they fight differently. Until this exists, "the reincarnation fights" is
true but "the AI writes itself" is not.

### 2. Prove non-trivial strategy (rmdev Phase 1.4 / rmdev2 Phase 6)
Run a real seeded audit (100–1000 matches) across reincarnations and bodies.
Catch: stuck state machines, unreachable states, degenerate orbiting, controller
oscillation, energy exploits, ring-out pathologies. Then check for
**non-transitivity** (A beats B, B beats C, C beats A). The game is not proven
strategically real until this passes. The balance-matrix tooling
(`robobladez matrix`, `scripts/run_matrix.py`) exists but targets the legacy
policy zoo — adapt it to reincarnations.

### 3. Wire a real image-generation backend (Phase 10/16)
`VisualForge` and the media pipeline use a **mock** backend (`mock://` artifacts,
`mock-auto-approved` assets, hardcoded `qa_score=0.95`). Implement:
- `ImageGeneratorBackend` (generate candidates → VisualQA → approve)
- one real provider to produce the canonical Boris/Morty/Arena packs
- `LTX25Renderer` with `submit/status/fetch/retake/reframe` against the LTX API

Exit: `robobladez mvp --render` produces a real asset pack + a real render job,
and `visual_qa` no longer returns "not executed: mock renderer."

### 4. CI enforcement
The workflow `.github/workflows/ci.yml` exists but is not branch-enforced. Turn on
required checks on `main` (unit + deterministic replay + contract smoke). This is
cheap and protects everything else.

### 5. Daimon visual path (Phase 21) + season mini-loop (Phase 22)
- Generate a daimon visual pack only when a Daimon actually MANIFESTs (from canon,
  never hardcoded). Test with a separate later-career fixture.
- 4-agent mini-season, media only for the top 2–3 significant matches.

## What NOT to prioritize
Public entrant SDK, website, spectator frontend, PSRO, Alpha-Rank, 100 bodies,
20 ability families, economy, live streaming, custom LTX LoRAs, complex 3D arena.
All multipliers; none prove the core. Do the five items above first.
