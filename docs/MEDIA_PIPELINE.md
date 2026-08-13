# Media Pipeline (rmdev Phase 13)

LTX / video generation is **downstream of canonical simulation** and **replaceable**.

```
MATCH REPLAY
  → EVENT SELECTION
  → SHOT SPEC
  → CONTROL ASSETS
  → LTX (2.3 today, 2.5 later, or any renderer)
  → VISION/LOGIC QA
  → EPISODE
```

## Canonical software objects (`src/robobladez/media.py`)

| Object | Role |
|---|---|
| `ShotSpec` | canonical, schema-valid shot (see `docs/ltx/templates/shot-spec.schema.json`) |
| `RenderRequest` | asks a backend to render a ShotSpec (family/version/profile) |
| `RenderJob` | a tracked render (queued/running/done/failed) |
| `RenderArtifact` | the returned clip (uri + digest) |
| `QAVerdict` | pass/fail with canonicality checks |

The world/game emits `ShotSpec` and consumes `RenderArtifact` — it never parses
model-specific workflow JSON. Backends map ShotSpec → LTX API / ComfyUI / local / future-2.5.

## Control hierarchy (least-generative route that solves the shot)

Loose → constrained: T2V → I2V → FIRST_LAST → KEYFRAME → ICLORA → RETAKE → EXTEND.

| Shot class | Control mode |
|---|---|
| establish_arena | T2V |
| competitor_intro | I2V |
| battle_event | KEYFRAME |
| daimon_manifestation | I2V |
| replay_analysis | ICLORA |
| round_result | RETAKE |

If a shot encodes a canonical event, increase control as event specificity increases.
Prompting should not carry constraints that a reference/control signal can express.

## LTX version status

Official line is **LTX-2.3** (`ltx-2-3-fast`, `ltx-2-3-pro`). LTX-2.5 is not an official
released target as of 2026-08-13; see `docs/ltx/11-LTX-2.5-WATCHLIST.md`. The renderer
abstraction allows a 2.5 backend swap without touching RoboBladez.

## Reference pack

Full research (feature matrix, prompting, ComfyUI, LoRA/IC-LoRA training, hardware,
audio, provenance) lives in `docs/ltx/` (imported from the LTX production pack).
