# External Infrastructure — What to Reuse

Checked against public project pages in August 2026.

## 1. Bullet / PyBullet

https://github.com/bulletphysics/bullet3

Use for:
- later rigid-body / contact backend
- headless `DIRECT` simulation
- collision/force integration
- validating a more physical spinning-top model

Do **not**:
- couple canonical match schemas directly to PyBullet object IDs
- assume default rigid-body settings accurately reproduce real Beyblade/top dynamics

Integration target:
`PhysicsBackend` adapter behind the existing match engine.

---

## 2. PettingZoo

https://github.com/Farama-Foundation/PettingZoo

Use for:
- future standard multi-agent environment adapter
- compatibility with MARL/self-play tooling
- environment versioning ideas

Do **not**:
- make PettingZoo a hard MVP dependency
- redesign the game around RL before the game is fun

Integration target:
Expose RoboBladez later as a Parallel/AEC-compatible environment.

---

## 3. OpenSpiel

https://github.com/google-deepmind/open_spiel

Use for:
- formal simultaneous-move game representation
- imperfect-information concepts
- best-response / exploitability evaluation
- PSRO-style policy populations
- Alpha-Rank / non-transitive meta analysis

Do **not**:
- put 60 Hz physics directly into an extensive-form tree

Integration target:
Build a strategic abstraction around match/round policy choices and payoff matrices.

---

## 4. Robocode Tank Royale

https://github.com/robocode-dev/tank-royale

Use for:
- server-enforced rules versus external competitor code
- bot API design
- observers/controllers
- battle recording/replay architecture
- multi-language/network entrant architecture later

This is the closest architectural precedent for the open-league phase.

Do **not**:
- copy Robocode game mechanics; copy the *separation of responsibilities*.

---

## 5. MIT Battlecode 2026

https://github.com/battlecode/battlecode26

Scaffold:
https://github.com/battlecode/battlecode26-scaffold

Use for:
- competition packaging
- entrant scaffolds
- tournament workflow
- reproducible competition seasons
- examples of how competitors receive a stable programming surface

Do **not**:
- take its license/competition assumptions for granted; inspect licenses before reuse.

---

## 6. LTX-2

https://github.com/Lightricks/LTX-2

Use for:
- downstream audio/video cinematic reconstruction
- later LoRA/IC-LoRA work for stable RoboBladez visual identity
- remote GPU rendering

Do **not**:
- place it in the game loop
- let a generated video determine canon

Important:
Review the current LTX-2 license before commercial deployment.

---

## 7. ComfyUI-LTXVideo

https://github.com/Lightricks/ComfyUI-LTXVideo

Use for:
- production workflows around LTX-2.3
- image/video conditioning
- motion tracking / control workflows
- queueable render jobs

Integration target:
`ShotSpec → ComfyUI workflow JSON → render → QA`.

---

## 8. LTX Director Motion Brush

https://github.com/exportAnything/ComfyUI-LTX-Director-Motion-Brush

Use for:
- storyboard timeline control
- motion tracks
- retake workflows
- carrying controlled motion between shots

Treat as optional/experimental relative to the official LTX repositories.

---

# What not to bring into MVP

- Neo4j
- microservices
- Kubernetes
- custom fine-tuned LLM
- quantum-computing libraries
- GNN controller
- IPFS
- RL training
- blockchain
- real-time cinematic generation

The valuable MVP is the deterministic competitive constitution + replay/canon contract.
