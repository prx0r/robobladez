import unittest
from robobladez.agent import AgentState, DaimonState, HumanInteractionEvent, agent_snapshot
from robobladez.model import BladeSpec, ArenaSpec
from robobladez.policy import CounterPolicy, AggressivePolicy
from robobladez.engine import run_match
from robobladez.analysis import analyze_behavior
from robobladez.evolution import evolve_agent
from robobladez.signatures import SignatureDetector
from robobladez.league import round_robin


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.m = run_match(5, ArenaSpec(max_seconds=3),
                           BladeSpec("a"), BladeSpec("b"),
                           CounterPolicy(), AggressivePolicy(), 3)
        self.analysis = analyze_behavior(self.m)

    def test_daimon_ema_accumulates(self):
        d = DaimonState()
        d.update({"earth": 1, "water": 0, "fire": 0, "air": 0, "aether": 0}, alpha=1.0)
        d.update({"earth": 1, "water": 0, "fire": 0, "air": 0, "aether": 0}, alpha=1.0)
        self.assertEqual(d.dominant(), "earth")
        self.assertEqual(d.battle_count, 2)
        self.assertAlmostEqual(sum(d.affinities.values()), 1.0)

    def test_daimon_drifts_toward_behavior(self):
        d = DaimonState()
        for _ in range(10):
            d.update({"water": 1, "earth": 0, "fire": 0, "air": 0, "aether": 0}, alpha=0.6)
        self.assertEqual(d.dominant(), "water")

    def test_agent_remembers_and_models_opponent(self):
        a = AgentState("a")
        b = AgentState("b")
        evolve_agent(a, self.m, "a", "b", b,
                     self.analysis["a"]["daimon_projection"]["affinities"])
        self.assertIn("b", a.opponent_models)
        self.assertEqual(a.match_history[-1]["opponent"], "b")
        self.assertEqual(a.daimon.battle_count, 1)

    def test_agent_snapshot_is_serializable(self):
        a = AgentState("a")
        snap = agent_snapshot(a, 1)
        self.assertEqual(snap["agent_id"], "a")
        self.assertIn("snapshot_hash", snap)
        self.assertEqual(snap["status"], "NARRATIVE_PROJECTION")

    def test_human_interaction_is_append_only(self):
        a = AgentState("boris")
        a.add_interaction(HumanInteractionEvent(
            type="MENTOR_ADVICE", human="owner-001", agent="boris",
            content="attack early", adopted=False))
        self.assertEqual(len(a.interactions), 1)
        self.assertIn("type", a.interactions[0])
        self.assertEqual(a.profile()["interaction_count"], 1)


class SignatureTests(unittest.TestCase):
    def test_detector_registers_and_reports(self):
        d = SignatureDetector(window=2, min_occurrences=1)
        m = run_match(9, ArenaSpec(max_seconds=3), BladeSpec("x"), BladeSpec("y"),
                      CounterPolicy(), AggressivePolicy(), 3)
        d.register(m, "x")
        for s in d.signatures():
            self.assertGreaterEqual(s.win_count, 0)


class LeagueTests(unittest.TestCase):
    def test_round_robin_standings(self):
        entries = [
            (BladeSpec("a"), CounterPolicy()),
            (BladeSpec("b"), AggressivePolicy()),
        ]
        results, standings = round_robin(entries, seed=7, rounds=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(len(standings), 2)


if __name__ == "__main__":
    unittest.main()
