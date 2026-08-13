import unittest, copy
from robobladez.model import BladeSpec,ArenaSpec
from robobladez.policy import CounterPolicy,AggressivePolicy,PassivePolicy,commitment,manifest
from robobladez.engine import run_match,verify_replay_digest,run_round
from robobladez.analysis import analyze_behavior

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.a=BladeSpec("a")
        self.b=BladeSpec("b",mass=.060)
        self.arena=ArenaSpec(max_seconds=2.0)

    def test_exact_determinism(self):
        m1=run_match(123,self.arena,self.a,self.b,CounterPolicy(),AggressivePolicy(),3)
        m2=run_match(123,self.arena,self.a,self.b,CounterPolicy(),AggressivePolicy(),3)
        self.assertEqual(m1.to_dict(),m2.to_dict())

    def test_seed_changes_canon(self):
        m1=run_match(123,self.arena,self.a,self.b,CounterPolicy(),AggressivePolicy(),3)
        m2=run_match(124,self.arena,self.a,self.b,CounterPolicy(),AggressivePolicy(),3)
        self.assertNotEqual(m1.replay_digest,m2.replay_digest)

    def test_replay_digest_detects_tamper(self):
        m=run_match(123,self.arena,self.a,self.b,CounterPolicy(),AggressivePolicy(),3)
        self.assertTrue(verify_replay_digest(m))
        m.rounds[0].reason="tampered"
        self.assertFalse(verify_replay_digest(m))

    def test_policy_commitment_config_sensitive(self):
        p1=CounterPolicy(center_bias=.5)
        p2=CounterPolicy(center_bias=.6)
        self.assertEqual(commitment(p1,"x"),commitment(p1,"x"))
        self.assertNotEqual(commitment(p1,"x"),commitment(p2,"x"))
        self.assertIn("code_sha256",manifest(p1))

    def test_tie_is_not_awarded(self):
        # Very short rounds force time draws.
        ar=ArenaSpec(max_seconds=.01)
        m=run_match(1,ar,self.a,self.b,PassivePolicy(),PassivePolicy(),3)
        self.assertEqual(m.wins,{"a":0,"b":0})
        self.assertIsNone(m.winner)

    def test_no_nan_many_seeds(self):
        for seed in range(20):
            m=run_match(seed,self.arena,self.a,self.b,CounterPolicy(),AggressivePolicy(),3)
            for r in m.rounds:
                for f in r.frames:
                    for s in f.states.values():
                        vals=[*s["pos"].values(),*s["vel"].values(),s["omega"],s["energy"],s["integrity"]]
                        self.assertTrue(all(v==v and abs(v)<1e12 for v in vals))

    def test_analysis_separates_projection(self):
        m=run_match(5,self.arena,self.a,self.b,CounterPolicy(),AggressivePolicy(),3)
        x=analyze_behavior(m)
        self.assertIn("phenotype",x["a"])
        self.assertEqual(x["a"]["daimon_projection"]["status"],"NARRATIVE_PROJECTION")
        self.assertAlmostEqual(sum(x["a"]["daimon_projection"]["affinities"].values()),1.0)


    def test_role_symmetry_for_counter_vs_aggressive(self):
        ar=ArenaSpec(max_seconds=12.0)
        left=BladeSpec("left"); right=BladeSpec("right")
        m1=run_match(7,ar,left,right,CounterPolicy(),AggressivePolicy(),3,record_frames=False)
        m2=run_match(7,ar,left,right,AggressivePolicy(),CounterPolicy(),3,record_frames=False)
        # With identical bodies, swapping the policies should swap which identity benefits.
        self.assertEqual(m1.winner,"left")
        self.assertEqual(m2.winner,"right")

    def test_invalid_specs_rejected(self):
        with self.assertRaises(ValueError):
            run_match(1,self.arena,BladeSpec("bad",mass=-1),self.b,PassivePolicy(),PassivePolicy(),3)

if __name__=="__main__":
    unittest.main()
