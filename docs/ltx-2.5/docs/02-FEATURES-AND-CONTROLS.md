# Features and Control Stack

## Current LTX platform capabilities

Official documentation currently exposes these production primitives:

### Generation
- Text-to-video
- Image-to-video
- Audio-to-video
- synchronized audiovisual generation

### Editing
- Retake: regenerate a specific section
- Extend: generate additional frames at beginning/end
- Reframe: create a new framing/aspect composition from an existing video

### Local/open-source controls
The official LTX ecosystem documents:
- two-stage generation
- latent/spatial upscaling
- LoRA customization
- IC-LoRA / in-context control
- depth control
- pose control
- edge control
- video-to-video transformations
- audio/video conditioning
- inpainting/outpainting families
- trainer support for many multimodal modes

## Best control hierarchy

Use the least generative method that satisfies the shot:

```text
T2V
↓
I2V
↓
FIRST/LAST FRAME
↓
KEYFRAME INTERPOLATION
↓
DEPTH / POSE / EDGE / MOTION CONTROL
↓
V2V / IC-LoRA
↓
RETAKE
↓
CUSTOM LoRA / IC-LoRA
↓
FULL FINETUNE
```

## Rule for canonical projects

The more exact the event, the stronger the conditioning.

- establishing shot → T2V
- recurring subject → I2V
- exact state transition → first/last frame
- exact trajectory → motion/depth/pose control
- tiny failed section → Retake
- recurring domain/style failure → LoRA
