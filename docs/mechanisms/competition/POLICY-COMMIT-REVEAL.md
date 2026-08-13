# Mechanism: POLICY COMMIT / REVEAL

## Purpose
Guarantee that a competitor's strategy is **sealed before the match begins** and cannot be
edited during it (Constitution rules 4, 6). The commit is a verifiable fingerprint; reveal
happens after the match for auditability and spectator drama (rm5 #25).

## Canonical status
GAMEPLAY (the commitment affects legitimacy of the result) + INFRA (verification).

## Inputs
- `policy: Policy` — has `id`, `decide(obs)`, `public_config()`.
- `match_nonce: str` — `f"{match_id}|{seed}|{ENGINE_VERSION}"`.

## State
- **Persistent**: none in the engine; commitments are stored in `MatchResult.policy_commitments`.
- **Ephemeral**: the manifest + commitment computed at match start.

## Transition
```
1. code_sha256  = sha256(source_of(policy.__class__))          # cached per class
2. manifest     = {policy_id, class, config, code_sha256, api_version}
3. payload      = {manifest, match_nonce}
4. commitment   = sha256(canonical_json(payload))               # sort_keys, no spaces
5. store in MatchResult.policy_commitments
6. REVEAL (post-match, ANALYSIS): compare stored commitment to re-computed manifest
   of the revealed policy.
```
`manifest()` and `commitment()` are in `src/robobladez/policy.py`. Code fingerprint is
cached via `lru_cache` keyed by class.

## Outputs
- `MatchResult.policy_manifests: {blade_id: manifest}`
- `MatchResult.policy_commitments: {blade_id: commitment_hex}`

## Invariants
1. Same policy + same nonce ⇒ same commitment.
2. Different config or different code ⇒ different commitment.
3. Commitment is bound to the specific match via nonce (cannot be reused across matches).
4. The committed policy cannot be swapped mid-match: the engine holds the exact policy
   object that produced the commitment.

## Information visibility
- **PUBLIC_BEFORE_MATCH**: the *commitment hash* is public (committed).
- **POST_MATCH**: the *manifest* (including config and code fingerprint) is revealed.
- **NEVER**: the policy code/config before commit (opponent sees only the hash).

## Determinism
- `canonical_json` uses `sort_keys=True`, `separators=(",",":")` → byte-identical payloads.
- Code fingerprint depends on source text; the cached value is stable within a process.

## Failure modes
- `inspect.getsource` fails (e.g. interactive/`<stdin>` class) → falls back to
  `f"{cls.__module__}.{cls.__qualname__}"` (still deterministic, less precise).
- Commitment mismatch at reveal → the match is suspect; canon flags it (auditability).

## Edge cases
- Two different policy instances with identical config+code → same fingerprint (intended).
- Policy mutates its config via `public_config()` between commit and reveal → mismatch
  (a violation the reveal detects).

## Telemetry
- `policy_commitments` per blade; reveal status (verified / mismatch).

## Versioning
- `api_version = "rbz-policy-1"` in the manifest; bump on SDK contract changes
  (see POLICY-RUNTIME).

## Security
- The commitment binds an untrusted policy to a hash without revealing its strategy. The
  engine still executes the policy in-process today (sandbox is Phase 4); the commitment is
  the correctness layer that survives out-of-process execution.

## Tests
- `tests/test_engine.py::test_policy_commitment_config_sensitive` (config changes hash).
- `tests/test_protocol.py::BattleTests::test_two_phase_protocol` (avatars carry commitments).

## Examples
**Normal**: Two `ReportAwareStrategist` picks commit different hashes; after the match, each
manifest verifies against its commitment.
**Adversarial**: Opponent tries to read the rival's policy before commit — impossible; only
the hash is public.

## Non-goals
- Does NOT enforce the policy sandbox (see POLICY-RUNTIME).
- Does NOT choose which policy an agent selects (see PREMATCH-PLANNING).
