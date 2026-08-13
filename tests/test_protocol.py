import unittest, json
from robobladez.agent import AgentState, DaimonState, agent_snapshot
from robobladez.mechanical import mechanical_report
from robobladez.battle import run_battle
from robobladez.reincarnation_author import BaselineReincarnationAuthor
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
        # Every avatar is a committed reincarnation (not a zoo pick).
        for av in outcome.avatars.values():
            self.assertTrue(av.commitment)
            self.assertTrue(av.manifest.reincarnation_id)

    def test_reincarnation_author(self):
        report = mechanical_report(make_body("balanced"), make_body("heavy"),
                                   ArenaSpec(max_seconds=2), runs=3, rounds=1)
        author = BaselineReincarnationAuthor(agent_version="boris@1", author="boris")
        man = author.reincarnate(report, "balanced", "heavy")
        self.assertEqual(man.format, "RBZ-RC-1")
        self.assertGreaterEqual(len(man.states), 2)
        rt = author.compile(man)
        self.assertEqual(rt.current_state, man.initial_state)


class DaimonTests(unittest.TestCase):
    def _sig(self, i):
        return [f"sig-{i % 3}"] if (i % 10 == 0) else []

    def test_naming_at_manifest(self):
        d = DaimonState()
        # 40+ battles, 2+ confirmed signatures, 1+ salient, stable phenotype -> MANIFEST.
        for i in range(45):
            d.update({"earth": 1, "water": 0, "fire": 0, "air": 0, "aether": 0},
                     alpha=0.5, confirmed_signature_ids=self._sig(i),
                     salience_evidence_ids=[f"UPSET|alice|m{i}"] if (i % 20 == 0) else [])
        self.assertEqual(d.stage, "manifest")
        self.assertIsNotNone(d.name)

    def test_structural_stages_not_linear_xp(self):
        d = DaimonState()
        for _ in range(60):
            d.update({"earth": 1, "water": 0, "fire": 0, "air": 0, "aether": 0},
                     alpha=0.5)
        # Many battles but no confirmed signatures or salient events -> stuck at PROTO.
        self.assertEqual(d.stage, "proto")
        self.assertIsNone(d.name)

    def test_single_decisive_match_does_not_inflate_salience(self):
        from robobladez.salience import SalienceDetector
        from robobladez.battle import run_battle
        from robobladez.zoo import make_body
        a = AgentState("alice")
        b = AgentState("bob")
        outcome = run_battle(a, make_body("balanced", "-a"), b,
                             make_body("balanced", "-b"),
                             ArenaSpec(max_seconds=3),
                             mechanical_runs=3, strategic_rounds=3, base_seed=5)
        # An ordinary decisive match must NOT award career events to both agents.
        for agent_id in ("alice", "bob"):
            self.assertEqual(outcome.salience.get(agent_id, []), [])

    def test_snapshot(self):
        s = agent_snapshot(AgentState("x"), 1)
        self.assertEqual(s["status"], "NARRATIVE_PROJECTION")


if __name__ == "__main__":
    unittest.main()
