# MVP — One Vertical Slice (rmdev2)

RoboBladez is "working" when one command produces a complete, traceable vertical
slice — not when every subsystem is finished.

```bash
robobladez mvp \
  --agent boris \
  --agent morty \
  --seed 2026 \
  --render \
  --out out/mvp
```

produces:

```text
out/mvp/
├── competition/   entries.json, mechanical-report.json, match-execution-manifest.json,
│                  reincarnations/{boris,morty}-r001.json, match.json, replay.json
├── canon/         events.jsonl, agent-snapshots/, daimon-snapshots/, canon-manifest.json
├── visual/        visual-manifest.json (canonical Boris/Morty/Arena asset packs)
├── story/         episode.json, beats.json (beats reference canonical event IDs)
├── shots/         shot-*.json (ShotSpec v2: basis_event_ids, control, references)
├── controls/      shot-*-first.json, shot-*-last.json (deterministic control plates)
├── renders/       finals/ (mock artifacts; real LTX-2.5 backend replaces)
├── qa/            verdicts.json (BindingQA)
├── episode/       episode-manifest.json
└── RUN.json       provenance root (execution_digest, replay_digest, refs)
```

If that directory exists and every artifact links to its parents, **the MVP exists**.

## The milestone that matters

```
Boris and Morty exist before the match.
They inspect the same mechanical truth.
Each authors a different executable self (RBZ-RC-1).
Those exact selves are committed (canonical AST digest).
Those selves fight (deterministic).
The result becomes immutable history (execution_digest + replay_digest).
That history changes the Agents (transactional evolution, reincarnation lineage).
The exact bodies/world resolve to canonical visual assets.
The exact important events generate constrained shots.
LTX renders those shots. (mock today; LTX-2.5 replaces)
QA rejects contradictions. (BindingQA; VisualQA for real footage)
A final video is assembled. (EpisodeAssembler)
Every frame can be traced to canon.
```

## What Phase 1–26 of rmdev2 delivered in code

| Phase | Mechanism | Module |
|---|---|---|
| 1A | RC-1 telemetry: closing_speed, relative_tangential_speed, *_fraction, spins, time | `reincarnation/runtime.py` |
| 1B | low-integrity recovery (not `>0`) | `reincarnation_author.py` |
| 1C | bounded memory READ (memory.*) + SET/ADD | `reincarnation/runtime.py` |
| 2 | MatchExecutionManifest + execution_digest | `competition.py` |
| 3 | CompetitionEntry + immutable EntrySnapshot | `competition.py` |
| 4 | BaselineReincarnationAuthor + ReincarnationContext interface | `reincarnation_author.py` |
| 5 | Reincarnation lineage (boris-r001, r002, ...) | `agent.py` |
| 7 | First-class CanonicalEvent IDs + pre/post states | `canonical.py` |
| 8 | SignificanceDetector -> beats reference event IDs | `significance.py`, `story.py` |
| 13 | Deterministic first/last control-frame builder | `control_frames.py` |
| 14-15 | ShotSpec v2 + ControlPlanner (least-generative route) | `media.py`, `shots.py` |
| 26 | One-command `mvp` vertical slice | `mvp.py` |

## Target separation of responsibilities

```text
src/robobladez/
├── competition/   entry, challenge, execution, battle
├── reincarnation/ schema, validate, normalize, runtime, context, baseline_author, llm_author
├── canon/         events, store, reducers
├── agents/        state, memory, daimon, reflection
├── assets/        spec, library, resolver, forge, image_backend, evolution
├── story/         significance, compiler, beats
├── media/         shot_spec, control_planner, control_frames, renderer, ltx25, qa, assembler
└── mvp.py
```

Current files map onto this target; not every file is physically moved yet.

## MVP scope (frozen)

- 2 Agents, 2 bodies, 1 arena, 1 ruleset, 1 reincarnation compute class
- ability-free battle format, 3 strategic rounds, 1 episode, 5–8 shots
- No manifested Daimon required for MVP-1; the media system respects a latent Daimon.
  (Daimon visual path is tested via a separate later-career fixture, not the first match.)

## Post-MVP (deferred)

Public entrant SDK, website, spectator frontend, PSRO, Alpha-Rank, 100 bodies, 20 ability
families, economy, live streaming, huge evolutionary population, custom LTX LoRAs, complex
3D arena renderer. Those are multipliers; they don't prove the core.
