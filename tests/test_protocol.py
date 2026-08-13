import unittest, json
from robobladez.agent import AgentState, DaimonState, agent_snapshot
from robobladez.mechanical import mechanical_report
from robobladez.battle import run_battle, ReportAwareStrategist, StaticStrategist
from robobladez.zoo import make_body
from robobladez.model import ArenaSpec


class MechanicalTests(unittest.TestCase):
    def test_report_shape(self):
        r = mechanical_report(make_body("balanced"), make_body("heavy"),
                              ArenaSpec(max_seconds=2), runs=4, rounds=1)
        d = r.to_dict()
        self.assertIn("win_probability", d)
        self.assertEqual(set(d["win_probability"]) - {"draw"}, {"balanced", "heavy"})
        self.assertAlmostEqual(sum(d["win_probability"].values()), 1.0)
        self.assertIn("advantages", d)
        self.assertIn("vulnerabilities", d)
        # Determinism: same inputs -> same report.
        r2 = mechanical_report(make_body("balanced"), make_body("heavy"),
                               ArenaSpec(max_seconds=2), runs=4, rounds=1)
        self.assertEqual(d, r2.to_dict())


class BattleTests(unittest.TestCase):
    def test_two_phase_protocol(self):
        a = AgentState("boris")
        b = AgentState("morty")
        outcome = run_battle(a, make_body("balanced", "-boris"),
                             b, make_body("heavy", "-morty"),
                             ArenaSpec(max_seconds=3),
                             mechanical_runs=6, strategic_rounds=3,
                             base_seed=77)
        d = outcome.to_dict()
        self.assertIn("mechanical", d)
        self.assertIn("avatars", d)
        self.assertEqual(len(outcome.avatars), 2)
        self.assertEqual(outcome.match.rounds[0].seed, 77 + 5000 + 1000003)
        # Every avatar policy was committed.
        for av in outcome.avatars.values():
            self.assertTrue(av.commitment)

    def test_strategists(self):
        report = mechanical_report(make_body("balanced"), make_body("heavy"),
                                   ArenaSpec(max_seconds=2), runs=3, rounds=1)
        rp = ReportAwareStrategist()
        sp = StaticStrategist("orbit")
        self.assertTrue(rp.choose(report, "balanced", "heavy").id)
        self.assertEqual(sp.choose(report, "a", "b").id, "orbit")


class DaimonTests(unittest.TestCase):
    def test_naming_at_manifest(self):
        d = DaimonState()
        # 40+ battles, 2+ signatures, 1+ salient -> MANIFEST (stage 3)
        for i in range(45):
            d.update({"earth": 1, "water": 0, "fire": 0, "air": 0, "aether": 0},
                     alpha=0.5, has_signature=(i % 10 == 0), salient=(i % 20 == 0))
        self.assertEqual(d.stage, "manifest")
        self.assertIsNotNone(d.name)

    def test_structural_stages_not_linear_xp(self):
        d = DaimonState()
        for _ in range(60):
            d.update({"earth": 1, "water": 0, "fire": 0, "air": 0, "aether": 0},
                     alpha=0.5)
        # Many battles but no signatures/salient events -> cannot reach MANIFEST.
        self.assertEqual(d.stage, "proto")
        self.assertIsNone(d.name)

    def test_snapshot(self):
        s = agent_snapshot(AgentState("x"), 1)
        self.assertEqual(s["status"], "NARRATIVE_PROJECTION")


if __name__ == "__main__":
    unittest.main()
