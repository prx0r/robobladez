# RoboBladez Testing

Strict, machine-runnable test discipline. **No hanging tests.** Every test is fast
(<2s each) and fails loudly on the specific invariant it guards.

## How to run

```bash
export PYTHONPATH=src
python -m unittest discover -s tests -v
```

CI runs the same suite plus deterministic-replay and mechanism-contract smoke
(`.github/workflows/ci.yml`). If a test hangs, it is a bug in the test, not the
engine — every test here is bounded.

## Fast-fail rule

- No test may call LTX, ComfyUI, a GPU, the network, or a wall-clock sleep.
- Renders are simulated (`mock://` URIs). This is intentional: the pipeline is
  validated CPU-side; the real renderer is a replaceable backend.
- If a simulation is "too slow," reduce `mechanical_runs`/`seeds` — never block.

## Test inventory (strict notes)

### `tests/test_engine.py` — engine determinism & match lifecycle
- `test_exact_determinism`: same (seed, arena, bodies, policies) ⇒ identical replay dict.
- `test_seed_changes_canon`: different seed ⇒ different replay (not a no-op).
- `test_policy_commitment_config_sensitive`: config change ⇒ different commitment hash.
- `test_replay_digest_detects_tamper`: mutating a result breaks `verify_replay_digest`.
- `test_invalid_specs_rejected`: bad body specs raise `ValueError`.
- `test_tie_is_not_awarded`: equal round-wins ⇒ `winner=None`, no fabricated score.
- `test_no_nan_many_seeds`: no non-finite state across many seeds (audit property).
- `test_role_symmetry_for_counter_vs_aggressive`: slot order doesn't bias outcome.
- `test_analysis_separates_projection`: elemental affinities normalize; NARRATIVE flag.

### `tests/test_physics.py` — physics invariants
- `test_passive_energy_does_not_increase`: passive play never gains mechanical energy.
- `test_spin_decays_passively`: passive spin decays toward zero.

### `tests/test_agent.py` — identity, daimon, interactions
- `test_daimon_ema_accumulates`: affinities EMA correctly; normalize to 1.
- `test_daimon_drifts_toward_behavior`: repeated behavior shifts the dominant element.
- `test_agent_remembers_and_models_opponent`: `remember_match` builds opponent models.
- `test_agent_snapshot_is_serializable`: snapshot has id + hash + NARRATIVE status.
- `test_human_interaction_is_append_only_and_immutable`: events are frozen + hash-addressed.
- `test_registry_requires_cross_match_support`: one match can never confirm a signature.
- `test_registry_confirms_with_cross_match_support`: multi-match/opponent → candidates.

### `tests/test_protocol.py` — two-phase battle, reincarnation, daimon stages
- `test_two_phase_protocol`: run_battle produces committed reincarnation avatars.
- `test_reincarnation_author`: author → RBZ-RC-1 manifest → compiled runtime.
- `test_naming_at_manifest`: structural requirements → MANIFEST + name.
- `test_structural_stages_not_linear_xp`: many battles but no evidence → stuck at PROTO.
- `test_single_decisive_match_does_not_inflate_salience`: no fake career events.

### `tests/test_reincarnation.py` — RBZ-RC-1 compiler, salience, seed protocol
- `test_canonical_bytes_stable`: same machine ⇒ same bytes; narrative fields excluded.
- `test_commitment_changes_on_execution_field`: changing a state/transition changes hash.
- `test_invalid_target_rejected`: unknown transition target → ValidationError.
- `test_unreachable_nonfinite_rejected`: NaN action value → ValidationError.
- `test_runtime_runs_deterministically`: interpreter holds state + memory.
- `test_lineage_append_only_and_verifiable`: lineage records verify.
- `test_seed_bound_to_commitments`: seed changes if commitment/nonce changes.
- `test_reincarnation_commit`: manifest commits to 64-char hash.
- `test_ordinary_decisive_match_not_salient`: no upset without low win probability.
- `test_upset_assigned_only_to_supported_agent`: only the underdog winner gets UPSET.
- `test_evidence_id_dedup`: same (type, agent, match) → one evidence id.
- `test_one_match_cannot_confirm`: signature registry min-matches gate.

### `tests/test_media.py` — renderer-agnostic media pipeline (no LTX)
- `test_control_mode_from_shot_class`: establish→T2V, battle→KEYFRAME.
- `test_control_modes_are_legal`: all shot-class controls are valid modes.
- `test_digest_stable_and_narrative_insensitive`: prompt excluded, constraints included.
- `test_renderer_objects`: RenderRequest/RenderJob/RenderArtifact/QAVerdict contract.
- `test_render_queue_draft_to_artifact`: queue → running → done → artifact.
- `test_simulate_render_no_ltx_call`: produces `mock://` artifact bound to shot digest.
- `test_produce_episode_end_to_end`: full media pipeline, canonical shots pass QA.
- `test_qa_rejects_broken_digest`: digest mismatch ⇒ fail with specific message.

## Property/fuzz targets (documented, not yet in suite)

From `docs/mechanisms/00-MECHANISM-SPEC-TEMPLATE.md` + rm8 test plan:
- affinities sum to 1 ± eps after arbitrary update sequences
- stage never regresses; cannot advance without every executable gate
- duplicate evidence IDs do not double-count stage requirements
- same manifest + same seed ⇒ identical replay digest
- controller cannot access wall clock / filesystem / network (sandbox Phase 4)
- Reincarnation AST parser/validator fuzz: malformed replay, NaN/±inf, cyclic graph,
  zero-state controller, max memory.

These require the out-of-process sandbox (Phase 4) for the resource-isolation ones.
