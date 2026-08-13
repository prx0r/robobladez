"""Adversarial tests per rmreview #19 (the highest-risk properties).

These assert the FAILURE modes the review called out, not just that objects
exist. They are fast and fail loudly on the specific invariant they guard.
"""
import unittest
from robobladez.reincarnation import (
    ReincarnationManifest, MemorySlot, ReincarnationRuntime,
    canonical_bytes,
)
from robobladez.assets import (
    AssetLibrary, VisualSpec, VisualForge, AssetResolver, CanonConflictError,
    build_asset,
)
from robobladez.media import ShotSpec, RenderArtifact, binding_qa, visual_qa
from robobladez.battle import run_battle, _reincarnation_binding
from robobladez.agent import AgentState
from robobladez.model import Vec2, Observation, ArenaSpec
from robobladez.zoo import make_body


def _obs():
    return Observation(0, 1, Vec2(0, 0), Vec2(1, 0), 500, 100, 100,
                       Vec2(0.5, 0), Vec2(2, 0), 500, 100, 100, 0.42)


class ReincarnationCorrectnessTests(unittest.TestCase):
    """rmreview #19: test_pressure_only_recovers_at_low_integrity, closing_speed."""

    def test_closing_speed_is_relative_velocity(self):
        man = ReincarnationManifest(reincarnation_id="t", agent_version="a@1",
                                    states=[{"id": "s", "action": {"radial": 0.1}}],
                                    initial_state="s")
        rt = ReincarnationRuntime(man)
        # opponent approaching self => closing_speed positive.
        closing = Observation(0, 1, Vec2(0, 0), Vec2(0, 0), 500, 100, 100,
                              Vec2(0.5, 0), Vec2(-1, 0), 500, 100, 100, 0.42)
        ctx = rt._obs_ctx(closing)
        self.assertGreater(ctx["closing_speed"], 0.0, "opponent closing => positive")

        # opponent retreating => closing_speed negative (not self_speed).
        opening = Observation(0, 1, Vec2(0, 0), Vec2(0, 0), 500, 100, 100,
                              Vec2(0.5, 0), Vec2(1, 0), 500, 100, 100, 0.42)
        ctx2 = rt._obs_ctx(opening)
        self.assertLess(ctx2["closing_speed"], 0.0, "opponent opening => negative")

    def test_memory_can_change_future_transition(self):
        man = ReincarnationManifest(reincarnation_id="t", agent_version="a@1",
            memory=[MemorySlot("pressure_seen", "u8", 0, 255)],
            states=[
                {"id": "press",
                 "action": {"radial": 0.1,
                            "memory": [{"name": "pressure_seen", "op": "add", "value": 1}]},
                 "transitions": [
                     {"if": {"op": "gte", "lhs": "memory.pressure_seen",
                             "threshold": 2}, "to": "orbit"}]},
                {"id": "orbit", "action": {"radial": 0.2}},
            ], initial_state="press")
        rt = ReincarnationRuntime(man)
        obs = _obs()
        rt.decide(obs)  # tick1: mem=1
        rt.decide(obs)  # tick2: mem=2 -> transitions to orbit (next tick)
        rt.decide(obs)  # tick3: mem=3, should now be orbit
        self.assertEqual(rt.current_state, "orbit",
                         "memory-driven transition should fire after threshold")

    def test_different_reincarnation_ast_changes_match_commitment(self):
        """rmreview #19: test_different_reincarnation_ast_changes_match_commitment."""
        m1 = ReincarnationManifest(reincarnation_id="a", agent_version="x@1",
                                   states=[{"id": "s", "action": {"radial": 0.1}}],
                                   initial_state="s")
        m2 = ReincarnationManifest(reincarnation_id="a", agent_version="x@1",
                                   states=[{"id": "s", "action": {"radial": 0.9}}],
                                   initial_state="s")
        b1 = _reincarnation_binding(m1, "c1")
        b2 = _reincarnation_binding(m2, "c1")
        self.assertNotEqual(b1["canonical_ast_sha256"], b2["canonical_ast_sha256"])

    def test_match_record_contains_reincarnation_ast_digest(self):
        """rmreview #19: test_match_record_contains_reincarnation_ast_digest."""
        o = run_battle(AgentState("a"), make_body("balanced", "-a"),
                       AgentState("b"), make_body("heavy", "-b"),
                       ArenaSpec(max_seconds=3), mechanical_runs=3,
                       strategic_rounds=3, base_seed=7)
        self.assertTrue(o.match.reincarnation_bindings)
        for bid, b in o.match.reincarnation_bindings.items():
            self.assertIn("canonical_ast_sha256", b)
            self.assertIn("commitment", b)


class VisualVersionSafetyTests(unittest.TestCase):
    """rmreview #19: R17->R18 separation, typed resolver, conflicts, file digest."""

    def setUp(self):
        self.lib = AssetLibrary()
        self.forge = VisualForge(self.lib)

    def test_r18_visual_never_reuses_r17_asset(self):
        a17 = self.forge.ensure_visual(VisualSpec(spec_id="s1", entity_id="boris",
            asset_type="TALISMAN", mechanical_version="R17"), "HERO")
        a18 = self.forge.ensure_visual(VisualSpec(spec_id="s2", entity_id="boris",
            asset_type="TALISMAN", mechanical_version="R18"), "HERO")
        self.assertNotEqual(a17.asset_key(), a18.asset_key())
        self.assertEqual(a17.mechanical_version, "R17")
        self.assertEqual(a18.mechanical_version, "R18")

    def test_resolver_filters_exact_mechanical_version(self):
        self.forge.ensure_visual(VisualSpec(spec_id="s1", entity_id="boris",
            asset_type="TALISMAN", mechanical_version="R17"), "HERO")
        self.forge.ensure_visual(VisualSpec(spec_id="s2", entity_id="boris",
            asset_type="TALISMAN", mechanical_version="R18"), "HERO")
        res = AssetResolver(self.lib)
        r17 = res.resolve(entity="boris", mechanical_version="R17")
        r18 = res.resolve(entity="boris", mechanical_version="R18")
        self.assertEqual(len(r17), 1)
        self.assertEqual(len(r18), 1)
        self.assertNotEqual(r17[0]["asset_key"], r18[0]["asset_key"])

    def test_asset_key_conflict_with_different_digest_raises(self):
        a1 = build_asset("a", "TALISMAN", "boris", version=9, view="HERO",
                         mechanical_version="R1", uri="r2://x1.png")
        a2 = build_asset("a", "TALISMAN", "boris", version=9, view="HERO",
                         mechanical_version="R1", uri="r2://x2.png")
        self.assertEqual(a1.asset_key(), a2.asset_key())
        self.assertNotEqual(a1.digest(), a2.digest())
        self.lib.add(a1)
        with self.assertRaises(CanonConflictError):
            self.lib.add(a2)

    def test_latent_daimon_has_no_manifest_asset(self):
        from robobladez.shots import _daimon_entity_for
        a = AgentState("boris")  # daimon is latent/unnamed
        self.assertEqual(_daimon_entity_for(a), "")


class MediaQASplitTests(unittest.TestCase):
    """rmreview #19: test_semantic_qa_does_not_auto-pass_mock_render."""

    def test_binding_qa_rejects_contradicting_winner(self):
        shot = ShotSpec(shot_id="s1", canonicality="CANONICAL_EVENT",
                        constraints=["winner=boris"])
        art = RenderArtifact(job_id="j", shot_id="s1", digest=shot.digest())
        v = binding_qa(shot, art, expected_winner="morty")
        self.assertFalse(v.pass_)
        self.assertTrue(any("winner" in f for f in v.failures))

    def test_visual_qa_never_fakes_a_pass(self):
        shot = ShotSpec(shot_id="s1")
        art = RenderArtifact(job_id="j", shot_id="s1", digest=shot.digest())
        v = visual_qa(shot, art)
        self.assertFalse(v.pass_, "visual QA must not auto-pass a mock render")


if __name__ == "__main__":
    unittest.main()
