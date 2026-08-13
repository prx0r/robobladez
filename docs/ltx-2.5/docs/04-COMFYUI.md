# ComfyUI Usage

Official custom nodes:
https://github.com/Lightricks/ComfyUI-LTXVideo

## Workflow philosophy

Use ComfyUI as a renderer backend, never as project truth storage.

Your app should produce a `ShotSpec`.
A workflow adapter translates that into ComfyUI JSON.

## Production tiers

### Draft
- fast/distilled path
- lower base resolution
- several seeds
- no expensive upscale

### Final
- selected seed/composition
- higher quality path
- two-stage upscale
- QA
- Retake only failed intervals

## Recommended reusable workflows

Maintain workflow IDs rather than hardcoding node graphs in the domain code:

```text
ltx25/t2v-draft
ltx25/i2v-draft
ltx25/keyframe-controlled
ltx25/motion-controlled
ltx25/final-upscale
ltx25/retake
```

Each workflow should have a version and hash.
