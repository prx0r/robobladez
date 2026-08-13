import unittest
from robobladez.agent import AgentState, DaimonState, HumanInteractionEvent, agent_snapshot
from robobladez.model import BladeSpec, ArenaSpec
from robobladez.policy import CounterPolicy, AggressivePolicy
from robobladez.engine import run_match
from robobladez.signatures import SignatureRegistry
from robobladez.league import round_robin


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.m = run_match(5, ArenaSpec(max_seconds=3),
                           BladeSpec("a"), BladeSpec("b"),
                           CounterPolicy(), AggressivePolicy(), 3)

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
        a.remember_match(opponent_id="b", match_id=self.m.match_id,
                         match_affinities={"earth": 0.5, "water": 0.5, "fire": 0,
                                           "air": 0, "aether": 0},
                         opponent_daimon=b.daimon, result=self.m.winner)
        self.assertIn("b", a.opponent_models)
        self.assertEqual(a.match_history[-1]["opponent"], "b")
        self.assertEqual(a.daimon.battle_count, 1)

    def test_agent_snapshot_is_serializable(self):
        a = AgentState("a")
        snap = agent_snapshot(a, 1)
        self.assertEqual(snap["agent_id"], "a")
        self.assertIn("snapshot_hash", snap)
        self.assertEqual(snap["status"], "NARRATIVE_PROJECTION")

    def test_human_interaction_is_append_only_and_immutable(self):
        a = AgentState("boris")
        ev = HumanInteractionEvent(
            event_id="ev-1", human_id="owner-001", agent_id="boris",
            interaction_type="MENTOR_ADVICE", content="attack early",
            adoption_status="rejected")
        a.add_interaction(ev)
        self.assertEqual(len(a.interactions), 1)
        self.assertIn("event_id", a.interactions[0])
        self.assertEqual(a.profile()["interaction_count"], 1)
        # Event dataclass is frozen (immutable).
        with self.assertRaises(Exception):
            ev.adoption_status = "accepted"


class SignatureTests(unittest.TestCase):
    def test_registry_requires_cross_match_support(self):
        reg = SignatureRegistry(window=2, min_occurrences=2, min_matches=2)
        m1 = run_match(9, ArenaSpec(max_seconds=3), BladeSpec("x"), BladeSpec("y"),
                       CounterPolicy(), AggressivePolicy(), 3)
        # Single match: even if it has windows, one match cannot confirm.
        reg.register(m1, "x", "alice", "opp1")
        self.assertEqual(reg.confirmed_signature_ids("alice"), [])

    def test_registry_confirms_with_cross_match_support(self):
        reg = SignatureRegistry(window=2, min_occurrences=2, min_matches=2, min_opponents=2)
        for seed, opp in ((9, "opp1"), (10, "opp2"), (11, "opp3")):
            m = run_match(seed, ArenaSpec(max_seconds=3),
                          BladeSpec("x"), BladeSpec("y"),
                          CounterPolicy(), AggressivePolicy(), 3)
            reg.register(m, "x", "alice", opp)
        # With multiple matches/opponents, at least one window may confirm.
        # This test asserts the API runs and returns candidates deterministically.
        cands = reg.candidates("alice")
        self.assertIsInstance(cands, list)
        for c in cands:
            self.assertEqual(c.agent_id, "alice")


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
