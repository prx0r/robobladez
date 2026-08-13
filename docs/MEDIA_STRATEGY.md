# Media Strategy — LTX-2.5 & controllability

The point of LTX-2.5 for RoboBladez is **not** "better-looking clips." It is whether the
renderer improves the exact failure modes that matter when generative video sits downstream
of a deterministic, evidence-constrained engine:

> identity persistence, motion adherence, image-conditioning fidelity, long-shot coherence,
> controllability.

The architectural consequence is decisive:

> **As LTX gets better at following control signals, the LESS intelligence it needs to
> exercise — and the MORE valuable our upstream machinery becomes.**

The renderer is increasingly commoditized. Our data/world/canon layer is not.

## The core rule

LTX does not decide what happened.

```
MATCH
  → REPLAY
  → CANONICAL EVENT
  → SHOT SPEC
  → LTX (obey)
  → QA AGAINST REPLAY
  → RETake / REFRAME
  → EPISODE
```

Truth lives in the simulator + canon. The renderer's job is to **obey**.

## Division of truth vs. presentation

| System | Owns |
|---|---|
| Simulator / canon | trajectory, contact, timing, orientation, relative position, winner |
| LTX | materials, lighting, camera, effects, atmosphere, audio, cinematic appearance |

A cleaner division of labor means the video model cannot override physics or canon.

## Production primitives (implemented in `src/robobladez/media.py`)

### I2V is the default, not T2V
We anchor on canonical assets and ask for motion:
```
CANONICAL ASSET → I2V → motion
```
instead of `text → hope it redraws the right subject`. This makes canonical asset work compound.

### First-frame → last-frame interpolation
Given canonical before/after states, tell LTX to fill in the cinematic motion. Less room to
invent than an unconstrained prompt.

### Multi-keyframe conditioning
Constrain `A → B → C → D`; LTX cinematizes only the interstitial motion. Our `control_mode`
supports `FIRST_LAST` / `KEYFRAME`.

### Retake (interval repair)
Localized repair of a failed temporal interval (e.g. 2.8–4.1s) instead of re-rendering the
whole shot. Enables the loop:
```
Render → QA vs ShotSpec → localize error → Retake → verify
```
Implemented as `RenderQueue.retake(shot, parent_job_id, interval)`.

### Reframe (aspect variants)
Produce one master (16:9), derive 9:16 / 4:5 / 1:1 without re-generating the scene.
Implemented as `RenderQueue.reframe(master, aspect_ratio)`.

### Guide render → control signals (future)
```
simulator → cheap ugly guide render → depth/motion/edges → LTX → cinematic
```
The strongest long-term control path.

## Why this makes RoboBladez's canon more valuable

Any generator can eventually make a pretty spinning-top battle. It cannot reproduce:

```
persistent AI competitors
+ reincarnation policies
+ battle history
+ opponent models
+ emergent Daimons
+ deterministic canon
+ league meta
```

Stronger, more controllable models raise the relative value of this upstream machinery.

## LTX version status

- Official line: **LTX-2.3** today (`ltx-2-3-fast`, `ltx-2-3-pro`).
- **LTX-2.5** is the target direction (temporal stability, I2V fidelity, keyframes, retake,
  reframe) but not an official released checkpoint as of 2026-08-13. See
  `docs/ltx-2.5/` for the full pack and `docs/ltx/11-LTX-2.5-WATCHLIST.md`.
- The renderer abstraction keeps 2.5 a backend swap with no RoboBladez changes.

## References

- `docs/ltx/` — LTX-2.3 production pack (feature matrix, prompting, ComfyUI, LoRA/IC-LoRA,
  hardware, audio, control hierarchy).
- `docs/ltx-2.5/` — LTX-2.5 pack (2.5 features, migration checklist, production queue,
  renderer-agnostic integration, shot-spec schema).
- `docs/MEDIA_PIPELINE.md` — the media pipeline + control hierarchy.
