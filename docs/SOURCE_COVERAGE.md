# RoboBladez Source-Coverage Audit

Status of every rm file's technical requirements against the current codebase.
Legend: ✅ implemented · 🟡 partial/planned · ❌ not yet

## rm — Prehistoric World architecture (world-to-content engine)

| Requirement | Status | Where |
|---|---|---|
| Animal/entity graph as canonical object | 🟡 | Generalized to `AgentState`; world pack generalized later |
| Postgres canonical storage | 🟡 | `sql/postgres.sql`; runtime uses SQLite (`canon.py`) |
| Evidence/claim layer, provenance | ❌ | Out of scope for RoboBladez core |
| PBDB / Macrostrat / GBIF / OpenAlex ingestion | ❌ | rm2 domain packs, not RoboBladez |
| Deterministic simulation → event log → story → shots → LTX | ✅ | engine → story → shots → (external LTX) |
| Versioned assets (never overwrite) | ✅ | canon append-only + `agent_versions` |
| Mechanical baseline before strategy | ✅ | `mechanical.py` → `battle.py` |
| PettingZoo-style env interface | 🟡 | `Policy` protocol; not full PettingZoo |

**rm is a different product vision** (prehistoric content). Only the *engine architecture* is shared and it is
integrated. The animal/domain-specific parts are deliberately not built (per "don't generalize prematurely").

## rm1 — World-to-content compiler / DomainPacks

| Requirement | Status | Where |
|---|---|---|
| Four engines (Knowledge / World / Story / Media) | 🟡 | Story+Media exist; Knowledge/World generalized into agent+engine |
| DomainPack concept | 🟡 | `zoo.py` policies/bodies are the first "pack"; no `/domains` yet |
| ScenarioKinds (combat/survival/tournament/etc.) | 🟡 | combat only; enum not yet |
| CardProjection / Top-Trumps | ❌ | Not built (Phase 9+ in rmdev) |
| Tournament engine | 🟡 | `round_robin`; no bracket/playoff yet |

**rm1 is architecture guidance.** Core separation is integrated (simulation≠story≠media); the generic
pack/engine abstraction is a later-phase concern.

## rm2 — Life Graph / general entity model

| Requirement | Status | Where |
|---|---|---|
| WorldEntity abstraction | 🟡 | `AgentState` covers RoboBladez; not generic entity |
| EOL TraitBank / GBIF / GloBI / Open Tree | ❌ | External data domains, not RoboBladez core |
| Deep sea / space / mythology packs | ❌ | Out of scope |
| Behavior-derived identity | ✅ | `DaimonState` EMA (adopted directly) |
| Automated discovery loop (graph → content) | 🟡 | `meta.py` non-transitivity discovery |

**rm2's core *transferable* insight** (behavior → identity, discovery loop) is integrated. The world packs are
rm's domain, not this engine.

## rm3 — Game-theory / competition architecture (HIGH INTEGRATION)

| Requirement | Status | Where |
|---|---|---|
| Deterministic given seed | ✅ | `engine.py` + digest verification |
| Sealed/committed policies | ✅ | `manifest()` + `commitment()` |
| Simultaneous actions (not turn-based) | ✅ | both decide before physics step |
| Engine/competitor separation | 🟡 | in-process `Policy`; out-of-process sandbox is Phase 4 |
| Robocode-style constrained API | 🟡 | `Policy` protocol; sandbox later |
| OpenSpiel-style interface | 🟡 | `Policy`/`Action`/`Observation`; not full OpenSpiel |
| Oshi-Zumo simultaneous-commit game theory | ✅ | sealed simultaneous decisions |
| PSRO / Alpha-Rank / payoff matrix | 🟡 | `meta.py` win-rate matrix; PSRO/Alpha-Rank not yet |
| Match replay (.rbz) + projections | ✅ | canonical replay + digest + viewer |
| Best-of-N (BO1/BO5/BO10) | ✅ | `strategic_rounds` param |
| Non-transitive meta as design goal | 🟡 | `meta.py` detects cycles; tuning pending |
| Exploitability | ❌ | Not yet |

**rm3 is the closest to our build.** Determinism, commitments, simultaneous play, replay, best-of-N all
integrated. Sandbox, PSRO, Alpha-Rank, exploitability are the remaining gaps.

## rm4 — Design principles / convergence

| Requirement | Status | Where |
|---|---|---|
| Don't start with RL | ✅ | hand-designed policies only |
| Headless sim first, cinematic later | ✅ | engine headless; LTX external |
| Replay as single source of truth | ✅ | canonical replay + digest |
| Behavior-derived elemental affinities | ✅ | `DaimonState` EMA |
| Signature moves from repeated patterns | ✅ | `signatures.py` |
| Sandboxed policies behind validator | 🟡 | in-process; sandbox Phase 4 |
| Constrained action space | ✅ | `Action` (radial/tangential/torque/boost) |
| Character identity inferred from behavior | ✅ | daimon from EMA, not lore |
| Post-match learning | ✅ | `PostMatchReflection` + opponent models |

**rm4 is fully converged with the build** — it's the design law the code already follows.

## rmaudit — Archive audit / canonical structure

| Requirement | Status | Where |
|---|---|---|
| AgentSnapshot schema | ✅ | `agent_snapshot()` |
| Blade schema | ✅ | `BladeSpec` |
| MatchPolicy schema | ✅ | `Policy` + `manifest` |
| Match schema | ✅ | `MatchResult` |
| Replay schema | ✅ | `Frame`/`RoundResult` |
| BehaviorProfile | ✅ | `analysis.analyze_behavior` phenotype |
| Daimon schema | ✅ | `DaimonState` |
| Episode schema | ✅ | `story.compile_story` |
| `/docs` six canonical docs | ✅ | CONSTITUTION, GAMEPLAY, GAME_RULES, EVOLUTION, SIMULATION→PHYSICS, MEDIA_PIPELINE |
| League / canon / evolution dirs | ✅ | league.py, canon.py, evolution.py |
| Drop quantum/consciousness/IPFS from core | ✅ | none imported in core |

**rmaudit is essentially satisfied** — it prescribed the exact schema/architecture we now have.

## rmdev — The canonical roadmap

| Phase | Status |
|---|---|
| 0 Lock constitution | ✅ CONSTITUTION.md + digest |
| 1.1 12 policy archetypes | ✅ `zoo.py` (12) |
| 1.2 8 body archetypes | ✅ `zoo.py` (8) |
| 1.3 run matrix | ✅ `scripts/run_matrix.py` (heavy run, safe defaults) |
| 1.4 non-transitivity diagnosis | ✅ `meta.py` |
| 2 Mechanical baseline report | ✅ `mechanical.py` |
| 3 Policy SDK | 🟡 `Policy` protocol; formal SDK/versioning later |
| 4 Sandboxed competitors | ❌ out-of-process sandbox (next) |
| 5 League + persistent agents | 🟡 `league.py`/`agent.py`; full DB schema pending |
| 6 Agent learning (opponent models, evolution) | ✅ `evolution.py` + opponent models |
| 7 PSRO / meta evolution | 🟡 payoff matrix only |
| 8 Daimon emergence | ✅ `DaimonState` (naming, stages) |
| 9 Signature move discovery | ✅ `signatures.py` |
| 10 Narrative/canon engine | 🟡 canon store + story; CanonGraph later |
| 11 Content compiler | ✅ `story.py` → `shots.py` |
| 12 Visual asset bible | ❌ |
| 13 LTX production | ❌ external (needs GPU) |
| 14 QA system | 🟡 replay digest; visual QA later |
| 15 Website | ❌ |
| 16 Public entrants | ❌ |
| 17 Seasons | 🟡 `round_robin`/`run_season`; playoffs later |
| 18 Broader reuse | ❌ later |

**rmdev is the roadmap.** Phases 0–2 and the core of 5–11 are built. Remaining: 3 (SDK), 4 (sandbox),
7 (PSRO), 12–18 (media/web/seasons/public).

## The four genuinely-special ideas

1. Mechanical reveal → sealed strategic response — ✅ `battle.py`
2. Persistent character ≠ body ≠ battle policy — ✅ `agent.py` + `battle.py`
3. Behavior creates identity — ✅ `DaimonState` + `signatures.py`
4. Simulation creates canon; media dramatizes — ✅ engine → canon → story → shots

## What's NOT yet integrated (real gaps)

- **Out-of-process policy sandbox** (rm3/rm4/rmdev Phase 4) — biggest gap
- **Formal policy SDK + versioning** (rmdev Phase 3)
- **PSRO / Alpha-Rank / exploitability / payoff-matrix refinement** (rm3, rmdev 7)
- **Tournament brackets / seasons** (rm1, rmdev 17)
- **Visual asset bible, QA, website, public entrants, LTX** (rmdev 12–16, 18)
- rm/rm1/rm2 **world-domain packs** (prehistoric, life graph, etc.) — intentionally out of scope per "don't generalize prematurely"
