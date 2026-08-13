# External Infrastructure

Use these as adapters/reference implementations, not as the ontology of RoboBladez.

- Bullet / PyBullet — https://github.com/bulletphysics/bullet3
  - future 3D/contact backend
  - keep PyBullet IDs out of canonical schemas

- Robocode Tank Royale — https://github.com/robocode-dev/tank-royale
  - best precedent for isolated autonomous competitors, battle server, observer/replay architecture
  - copy responsibility boundaries, not tank mechanics

- OpenSpiel — https://github.com/google-deepmind/open_spiel
  - strategic abstraction, simultaneous games, best response, exploitability, PSRO, Alpha-Rank
  - feed it payoff/matchup abstractions, not 240 Hz rigid-body state

- PettingZoo — https://github.com/Farama-Foundation/PettingZoo
  - later environment adapter for MARL/self-play tooling
  - not a core dependency

- MIT Battlecode 2026 — https://github.com/battlecode/battlecode26
- Battlecode scaffold — https://github.com/battlecode/battlecode26-scaffold
  - entrant SDK/scaffold and competition-operations inspiration

- LTX-2 — https://github.com/Lightricks/LTX-2
- ComfyUI-LTXVideo — https://github.com/Lightricks/ComfyUI-LTXVideo
  - downstream cinematic reconstruction only

- LTX Director Motion Brush — https://github.com/exportAnything/ComfyUI-LTX-Director-Motion-Brush
  - optional motion/storyboard control; treat as experimental
