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
| `src/robobladez/reincarnation_author.py` | `ReincarnationContext` + `BaselineReincarnationAuthor` (6 strategy profiles) |
| `src/robobladez/llm_author.py` | `LLMReincarnationAuthor` — hermes (deepseek-v4-flash) authors RBZ-RC-1, falls back to baseline |
| `src/robobladez/reincarnation_audit.py` | strategy audit: decisive rate + non-transitivity (`audit-reincarnations`) |
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
- `docs/COMBAT_ENGINE.md` — combat engine state + physics-simulation-quality ambition + LTX translation
- `docs/BLADE.md` — what a blade is (material, editing regime, game theory)
- `docs/MEDIA_PIPELINE.md`, `docs/MEDIA_STRATEGY.md`, `docs/VISUAL_ASSETS.md` — media layer
- `docs/IMAGE_GEN.md` — Cloudflare image-model findings (flux-1-schnell confirmed)
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

Status snapshot: the LLM author and strategy audit are DONE. The active gaps are
balance, physics fidelity, and wiring real media/image backends.

### 1. Balance the strategy archetypes (DONE infrastructure, ACTIVE tuning)
`robobladez audit-reincarnations` exists (6 author archetypes × bodies, seeded).
**Honest result: 73% decisive, NO non-transitive cycles, `pressure` dominates,
`adaptive` loses to everything.** This is the real moat and it's not achieved
yet. Tune the archetypes until counters emerge (A>B, B>C, C>A):
- fix `adaptive` (currently loses everything)
- weaken `pressure` (near-universal winner)
- then scale seeds/audit to 100–1000 and confirm a non-transitive meta.

### 2. Physics fidelity toward simulation quality (DONE 2D kernel, NEXT fidelity)
The combat engine is a planar rigid-disk kernel (no precession/tilt/CoM-offset).
See `docs/COMBAT_ENGINE.md`. The path: add center-of-mass offset + precession
(V1), then tilt/tipping (V2), then validated 3D/2.5D (V3). Each step keeps the
`PhysicsBackendV2` boundary and bumps `engine_version` (history stays
reproducible). Better physics → better LTX control signals.

### 3. Wire a real image-generation backend (DONE provider probe, NEXT wiring)
`flux-1-schnell` on Cloudflare Workers AI is **confirmed working** (1024x1024
JPEG, ~1-2s). See `docs/IMAGE_GEN.md`. `VisualForge` still uses a mock backend
(`mock://`, `qa_score=0.95` hardcoded). Implement `ImageGeneratorBackend` + wire
`flux-1-schnell` to produce the canonical Boris/Morty/Arena packs, then
`LTX25Renderer` (submit/status/fetch/retake/reframe).

Exit: `robobladez mvp --render` produces a real asset pack + real render job;
`visual_qa` no longer returns "not executed: mock renderer."

### 4. CI enforcement
The workflow `.github/workflows/ci.yml` exists but is not branch-enforced. Turn on
required checks on `main`.

### 5. Daimon visual path (Phase 21) + season mini-loop (Phase 22)
- Generate a daimon visual pack only when a Daimon actually MANIFESTs (from canon,
  never hardcoded). Test with a separate later-career fixture.
- 4-agent mini-season, media only for the top 2–3 significant matches.

## What NOT to prioritize
Public entrant SDK, website, spectator frontend, PSRO, Alpha-Rank, 100 bodies,
20 ability families, economy, live streaming, custom LTX LoRAs, complex 3D arena.
All multipliers; none prove the core. Do the five items above first.
