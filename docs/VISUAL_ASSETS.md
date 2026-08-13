# Visual Asset System (rmart)

RoboBladez image generation is a **canon-building asset pipeline**, not per-video
decoration. The goal is never `prompt -> image -> use once`. It is:

```
GAME STATE / CANON
  → VISUAL SPEC
  → ASSET GENERATOR
  → CANDIDATES
  → VALIDATION
  → CANONICAL ASSET VERSION
  → ASSET GRAPH
  → SHOT COMPILER
  → IMAGE / VIDEO / UI / POSTER / THUMBNAIL
  → REUSE
```

## Constitution rule (add to CONSTITUTION.md)

> **Generative models may propose visual reality. Only the canon system may establish it.**
> **Once visual reality is established, downstream generators reference it rather than
> reinventing it.**

This gives RoboBladez an accumulating world instead of disconnected AI generations.

## Two representations of every persistent thing

```
STRUCTURAL STATE   what it is       -> mechanical/gameplay truth
VISUAL STATE       how it appears   -> canonical presentation truth
```

Neither is reconstructed from prose every time.

## The MVP ontology (`src/robobladez/assets.py`)

| Object | Role |
|---|---|
| `VisualSpec` | machine-readable spec that drives generation (prompt is compiled FROM it, never the source of truth) |
| `VisualAsset` | a versioned, hash-addressed canonical image (records `mechanical_version`) |
| `StyleProfile` | reusable rendering medium (cinematic/poster/UI/analysis) |
| `AssetLibrary` | append-only, versioned store of CANONICAL + EDITORIAL assets |
| `AssetResolver` | returns the canonical reference bundle for a query |
| `VisualForge` | autonomous service: `ensure_*` returns existing or generates+validates+stores missing |
| `ShotAssetBundle` | the coherent reference package handed to LTX |

Asset types (MVP): `AGENT_PORTRAIT, TALISMAN, DAIMON, ARENA, EFFECT`.
Required views (MVP): `HERO, SIDE, TOP, THREE_QUARTER`.
Statuses: `DRAFT, CANDIDATE, APPROVED, SUPERSEDED, RETIRED`.
Canonicality: `CANONICAL, PROJECTION, EDITORIAL`.

## Key mechanisms

- **`mechanical_version` is recorded**: an image states "BORIS_TALISMAN mechanical R17,
  visual R4" — visual and gameplay truth stay coupled but distinct.
- **Canonical vs Editorial**: CANONICAL assets define world identity (reused forever);
  EDITORIAL assets are episode flourishes (loose). LTX references only CANONICAL.
- **Generate once, reuse**: `VisualForge.ensure_visual` returns the existing canonical
  asset if present; it never regenerates Boris just because a new episode exists.
- **Image-to-image evolution**: R17 → R18 uses the R17 canonical asset + mechanical delta +
  a `VisualEvolutionSpec`, preserving visual lineage.
- **Daimon visual lifecycle**: tied to mechanical stages (LATENT→…→ASCENDED); a MANIFEST
  reveal is meaningful because the asset literally didn't exist before the event.
- **Reincarnation overlay ≠ body version**: a reincarnation may add a temporary visual
  signature (presentation) without mutating the canonical body.

## Autonomy vs human (rmart §36)

Humans concentrate on **high-leverage canon decisions**: approving a new main Talisman,
the first Daimon manifestation, a new season aesthetic. Everything repetitive (detect
missing asset, build VisualSpec, generate candidates, QA reject, rank, reuse, build LTX
refs) is autonomous.

## Example flow

```python
forge = VisualForge(library)
spec = VisualSpec(spec_id="vs-boris", entity_id="boris", asset_type="TALISMAN",
                  mechanical_version="R17")
pack = forge.ensure_shot_assets([spec])        # 4-view canonical pack
refs = AssetResolver(library).resolve(entity="boris")   # canonical bundle
```

Then `shots.py` embeds those canonical references into each ShotSpec, so LTX conditions on
approved assets rather than re-inventing them.

## Storage / provenance

- Binaries in R2; metadata (specs, assets, versions, relations, jobs, candidates,
  reviews, style profiles, effect grammars, shot bundles) in the canonical DB.
- Every asset stores generator, model, seed, prompt, references, timestamp, parent
  asset, and edit chain — so "Boris R18 looks wrong" is traceable and re-derivable.

## MVP proof targets

1. competitor genesis → automatic canonical pack
2. body evolves → automatic new version derived from old
3. Daimon manifests → automatic new asset family
4. match produces story → ShotCompiler resolves existing assets
5. new effect required → VisualForge generates the missing effect
6. LTX receives a complete reference bundle
