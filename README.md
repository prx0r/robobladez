# RoboBladez

A deterministic AI-vs-AI spinning-top competition engine plus a canon-building media
pipeline. The defining mechanic: a persistent Agent **writes its own sealed executable
battle-self (a RBZ-RC-1 reincarnation)** each match, that self fights deterministically,
and the result becomes immutable canon that changes the Agent — then canonical
events/visual assets drive LTX (replaceable backend).

CPU-first modular monolith. **No numpy, no pybullet, no GPU, no external services** for
the core. Pure Python stdlib.

> The simulation decides what happened. The media layer decides how it is shown.

Also contains a small HTML5 arcade game in `index.html` (spinning-blade arena, no deps).

## Quick start

```bash
export PYTHONPATH=src
python -m robobladez.cli mvp --out out/mvp --seed 2026 --rounds 3   # one vertical slice
python -m robobladez.cli simulate --out out/sim                     # full stack, no LTX
python -m robobladez.cli demo --out ./out                           # single match
python -m robobladez.cli audit --seeds 250                          # fuzz/energy/canon
python -m robobladez.cli season --out ./out                         # 3-agent season
```

Tests (67, all fast, no LTX/network):

```bash
python -m unittest discover -s tests -v
```

View a replay: open `viewer/index.html` and load a `match.json`.

## The one proof of the MVP

```bash
python -m robobladez.cli mvp --out out/mvp --seed 2026 --rounds 3
```

produces a complete, internally-consistent artifact tree (`competition/`, `canon/`,
`visual/`, `story/`, `shots/`, `controls/`, `renders/`, `qa/`, `episode/`, `RUN.json`)
where every artifact links to its parents. If that tree exists, the MVP exists.

## New to the project?

Read **`docs/HANDOVER.md`** — it contains the repository map, the live/legacy/unwired
audit, the doc index, and test discipline.

## Docs

`docs/` — HANDOVER, ARCHITECTURE, MVP, ROADMAP, CONSTITUTION, TESTING, MEDIA_PIPELINE,
MEDIA_STRATEGY, VISUAL_ASSETS, GAMEPLAY_ORIGIN, GAMEPLAY, PHYSICS_SCOPE, plus
`docs/mechanisms/` (29 mechanism specs + `index.yaml` status) and `docs/ltx/`,
`docs/ltx-2.5/` (LTX research packs). v1-era docs live in `docs/archive/`.
