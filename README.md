# RoboBladez

Two things live here:

## 1. Arcade game (`index.html`)

A tiny 2D arena game: pilot a spinning-blade robot and slice incoming drone waves. Pure HTML5 Canvas — no dependencies, no build step.

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

**Controls:** WASD/Arrows move · mouse aims blades · Space/Shift dash.

## 2. Deterministic AI-competition engine — **MVP v2** (`src/robobladez`)

A deterministic, physically motivated 2D spinning-top competition engine whose canonical match history can later be rendered as a serialized LTX show. Pure Python stdlib — **no numpy, no pybullet, no GPU, ~50MB RAM**. The only GPU step (LTX rendering) is an external, optional adapter.

> The simulation decides what happened. The media layer decides how it is shown.

### v2 what's implemented

- deterministic seeded simulation + replay-digest verification
- real rigid-disk planar physics: mass, radius, moment of inertia, angular spin, spin drag, bowl restoring force, disk-disk contact impulses with tangential friction + spin coupling, ring-out / spin-out / burst / time-draw terminals
- simultaneous sealed policy decisions with code/config fingerprinting (`manifest`)
- **mechanical baseline mode** (passive bodies) separate from strategic matches
- best-of-N with honest draw/tie handling
- SQLite canon store (digest-verified, append-only semantics)
- raw behavioral phenotype + *separate, non-causal* daimon projection
- round-robin league
- deterministic story + LTX shot specs
- **audit harness** (`robobladez audit`)
- **mechanical baseline** system: neutral passive runs produce a `MechanicalMatchupReport` (win probability, advantages, vulnerabilities) before strategy
- **two-phase `battle` protocol**: mechanical reveal → sealed strategic avatar → best-of-N (the core RoboBladez mechanic)
- **projection/evolution layer**: persistent `AgentState` (EMA daimon identity with naming + manifestation stages), `SignatureDetector` (measured signature moves), `PostMatchReflection` + opponent models — all non-causal, per the Constitution
- policy zoo (12 archetypes) + body zoo (8 archetypes)
- matchup matrix runner + non-transitivity/meta analyzer

### The Constitution

`docs/CONSTITUTION.md` is the hard contract: the engine owns truth, matches are reproducible from versioned inputs, actions are simultaneous, policies are sealed mid-match, canon is append-only, the cinematic layer never reverses an outcome, and **nothing is called "emergent" unless measured from interaction**.

### Run

```bash
export PYTHONPATH=src
python3 -m robobladez.cli demo --out ./out     # baseline + strategic match
python3 -m robobladez.cli battle --out ./out   # two-phase: mechanical reveal -> sealed avatars
python3 -m robobladez.cli audit --seeds 250    # fuzz/energy/canon verification
python3 -m robobladez.cli season --out ./out   # 3-agent evolving season
python3 scripts/run_matrix.py --seeds 5 --out matrix.tsv  # matchup matrix
python3 -m robobladez.meta matrix.tsv          # non-transitivity diagnosis
```

Tests:

```bash
python3 -m unittest discover -s tests -v
```

### View a replay

Open `viewer/index.html` in a browser and load a `match.json`. No build, no deps.

### Docs

See `docs/` — CONSTITUTION, GAMEPLAY, PHYSICS_SCOPE, BUILD_NEXT, EXTERNAL_INFRA, PEER_REVIEW_V1, GAMEPLAY_ORIGIN, SOURCE_COVERAGE. Raw historical source material is archived separately (not in this repo); the distilled design law lives in `docs/GAMEPLAY_ORIGIN.md` and the coverage map in `docs/SOURCE_COVERAGE.md`.

