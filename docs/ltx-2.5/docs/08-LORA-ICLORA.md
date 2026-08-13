# LoRA / IC-LoRA Strategy

Official LTX open-source docs describe LoRA and IC-LoRA-style controls.

Use standard LoRA for:
- stable house visual style
- recurring character/object fidelity
- domain-specific material/lighting
- specialized motion priors

Use IC-LoRA / paired conditioning for:
- pose
- depth
- edge
- motion transfer
- style transfer
- restoration
- paired transformations

## Do not train too early

First try:
1. better prompt
2. better reference image
3. first/last frames
4. keyframes
5. depth/pose/edge control
6. Retake
7. shot decomposition

Only train after recurring failure is demonstrated across many shots.
