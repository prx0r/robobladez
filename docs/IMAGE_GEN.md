# Image Generation — Cloudflare Workers AI Findings

Verified working models + the canon-building asset pipeline they feed.

## Working model (confirmed, fast)

**`@cf/black-forest-labs/flux-1-schnell`** — the cheap/fast default.
- Returns a valid **1024x1024 JPEG** (~200KB), ~1-2s.
- Response is base64 in `result.image` (decode before saving).
- Call:

```bash
TOKEN="<CF_API_TOKEN>"; ACCOUNT="<account_id>"
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT/ai/run/@cf/black-forest-labs/flux-1-schnell" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  --data '{"prompt":"<prompt>"}'
```

Decode: `python3 -c "import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)['result']['image']))"`.

## Other models tested

| Model | Result |
|---|---|
| `@cf/black-forest-labs/flux-1-schnell` | ✅ valid 1024x1024 JPEG, ~1-2s |
| `@cf/black-forest-labs/flux-2-klein-4b` | ⚠️ needs `multipart` input (not JSON); 0.7s when reachable |
| `@cf/bytedance/stable-diffusion-xl-lightning` | ⚠️ output truncated on our call |
| `@cf/lykon/dreamshaper-8-lcm` | ⚠️ empty via JSON path |
| `@cf/leonardo/phoenix-1.0` | ⚠️ empty via JSON path |
| `@cf/stabilityai/stable-diffusion-xl-base-1.0` | ⚠️ empty via JSON path |

**Recommendation:** standardize on `flux-1-schnell` for MVP canonical packs.
Investigate `flux-2-klein-4b` multipart later (it's the fastest at 0.7s).

## How this feeds the canon pipeline

Per `docs/VISUAL_ASSETS.md`: image gen is a **canon-building pipeline**, not
per-video decoration. The flow:

```
VisualSpec -> PromptCompiler -> ImageGeneratorBackend (flux-1-schnell)
  -> 4 candidates -> VisualQA -> approve -> AssetLibrary (CANONICAL)
  -> ShotSpec.references -> LTX
```

`VisualForge` currently has a **mock backend** (hardcoded `qa_score=0.95`,
`mock-auto-approved`). The real `ImageGeneratorBackend` interface exists; wiring
`flux-1-schnell` in is the high-urgency work (HANDOVER item 3).

## Credentials

- R2/S3 endpoint: `https://954612afb5a97bb15dddcdc70176813d.r2.cloudflarestorage.com`
- Account id: `954612afb5a97bb15dddcdc70176813d`
- API token: stored in env / secrets (see `.env` — never commit)
