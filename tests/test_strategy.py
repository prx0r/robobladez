"""Strategy-profile + reincarnation-audit tests (rmdev Phase 1.4 / rmdev2 Phase 6).

Prove the author archetypes produce distinct machines and that the audit runs
and reports decisive rate / non-transitivity (without hanging).
"""
import unittest
import hashlib
from robobladez.reincarnation.normalize import canonical_bytes
from robobladez.reincarnation_author import BaselineReincarnationAuthor, ReincarnationContext
from robobladez.reincarnation_audit import audit_reincarnations, PROFILES
from robobladez.mechanical import mechanical_report
from robobladez.zoo import make_body
from robobladez.model import ArenaSpec


class StrategyProfileTests(unittest.TestCase):
    def setUp(self):
        self.report = mechanical_report(make_body("balanced"), make_body("heavy"),
                                        ArenaSpec(max_seconds=2), runs=2, rounds=1)

    def test_profiles_produce_distinct_machines(self):
        digests = {}
        for prof in PROFILES:
            a = BaselineReincarnationAuthor("x@1", "x", strategy_profile=prof)
            m = a.reincarnate(self.report, "balanced", "heavy")
            digests[prof] = hashlib.sha256(canonical_bytes(m)).hexdigest()[:16]
        self.assertGreaterEqual(len(set(digests.values())), len(PROFILES) - 1,
                                "profiles should produce (mostly) distinct machines")

    def test_each_profile_is_valid(self):
        for prof in PROFILES:
            a = BaselineReincarnationAuthor("x@1", "x", strategy_profile=prof)
            m = a.reincarnate(self.report, "balanced", "heavy")
            self.assertEqual(m.initial_state, "observe")
            self.assertTrue(m.states)


class ReincarnationAuditTests(unittest.TestCase):
    def test_audit_runs_and_reports(self):
        # Lightest bounded run: 2 profiles x 1 body x 1 seed, very short arena.
        from robobladez.reincarnation_audit import audit_reincarnations as ar
        r = ar(seeds=1, rounds=1, bodies=("balanced",), max_seconds=2)
        self.assertIn("decisive_rate", r)
        self.assertIn("profile_matrix", r)
        self.assertIn("non_transitive_cycles", r)
        self.assertGreaterEqual(r["decisive_rate"], 0.0)
        self.assertLessEqual(r["decisive_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
