# LTX-2.5 Status

Official model page supplied by the user:
https://docs.ltx.io/models/ltx-2-5

## Current documentation situation

The official LTX searchable model index currently still exposes LTX-2.3 prominently:
https://docs.ltx.io/models

The official API changelog:
https://docs.ltx.io/api-changelog

The current official platform supports:
- text-to-video
- image-to-video
- audio-to-video
- retake
- extend
- reframe
- synchronized audio/video generation
- Fast/Pro style production tiers in the currently indexed model family
- asynchronous production endpoints
- local/open-source workflows and trainer tooling

Do not assume any exact 2.3:
- model ID
- checkpoint filename
- VRAM figure
- duration matrix
- FPS matrix
- pricing
- LoRA compatibility
- VAE compatibility

for 2.5 unless the official 2.5 page or its linked docs explicitly confirm it.

## Architecture rule

Both projects should store:

```text
renderer_family = ltx
renderer_version = 2.5
backend = api | comfyui | local
model_id = exact official identifier
checkpoint_digest = exact digest if local
workflow_version = exact workflow version
```

Never hard-code `ltx-2-3-*` in domain logic.
