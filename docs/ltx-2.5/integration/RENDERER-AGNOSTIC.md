# Renderer-Agnostic Architecture

Both projects should compile into the same object:

```text
ShotSpec
```

Then:

```text
RoboBladez / Monstah
        ↓
      ShotSpec
        ↓
 Renderer Adapter
 ┌───────────────┬───────────────┬───────────────┐
 LTX API         ComfyUI         Local pipeline
 └───────────────┴───────────────┴───────────────┘
        ↓
 RenderArtifact
        ↓
 QA
```

## Invariant

The renderer may create pixels and audio.
It may not create canon.

For RoboBladez:
simulation owns battle truth.

For Monstah:
evidence/reconstruction owns scientific truth.
