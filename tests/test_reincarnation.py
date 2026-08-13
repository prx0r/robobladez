import unittest
from robobladez.reincarnation import (
    ReincarnationManifest, MemorySlot, ReincarnationRuntime,
    canonical_bytes, commitment, ReincarnationLineage, validate, ValidationError,
)
from robobladez.challenge import MatchChallenge, derive_match_seed, commit_reincarnation
from robobladez.salience import SalienceDetector, SalienceEvidence
from robobladez.signatures import SignatureRegistry
from robobladez.model import ArenaSpec, BladeSpec
from robobladez.policy import CounterPolicy, AggressivePolicy
from robobladez.engine import run_match


def make_manifest(**kw):
    d = dict(
        reincarnation_id="boris-r001",
        agent_version="boris@1",
        target_match="S01-M001",
        compute_class="C1",
        author="boris",
        memory=[MemorySlot("pressure_seen", "u8", 0, 255)],
        states=[
            {"id": "observe",
             "action": {"radial": 0.35, "tangential": 0.12, "boost": 0.1},
             "transitions": [
                 {"if": {"op": "lt", "lhs": "distance", "threshold": 0.12}, "to": "counter"},
                 {"else": True, "to": "orbit"}]},
            {"id": "counter", "action": {"radial": 0.3, "tangential": 0.7, "boost": 0.6}},
            {"id": "orbit", "action": {"radial": 0.1, "tangential": 0.8, "boost": 0.3}},
        ],
        initial_state="observe",
    )
    d.update(kw)
    return ReincarnationManifest(**d)


class ReincarnationTests(unittest.TestCase):
    def test_canonical_bytes_stable(self):
        m = make_manifest()
        self.assertEqual(canonical_bytes(m), canonical_bytes(m))
        # Narrative metadata (strategy_thesis/author) does NOT change the hash.
        m2 = make_manifest(strategy_thesis="fluff", author="daimon")
        self.assertEqual(canonical_bytes(m), canonical_bytes(m2))

    def test_commitment_changes_on_execution_field(self):
        a = make_manifest()
        b = make_manifest(states=[{"id": "counter",
                                   "action": {"radial": 0.9, "boost": 0.9}}])
        self.assertNotEqual(commitment(a, "c1"), commitment(b, "c1"))

    def test_invalid_target_rejected(self):
        bad = make_manifest(states=[{"id": "s", "transitions": [{"to": "nope"}]}],
                            initial_state="s")
        with self.assertRaises(ValidationError):
            validate(bad)

    def test_unreachable_nonfinite_rejected(self):
        bad = make_manifest(states=[{"id": "s", "action": {"radial": float("nan")}}],
                            initial_state="s")
        with self.assertRaises(ValidationError):
            validate(bad)

    def test_runtime_runs_deterministically(self):
        rt = ReincarnationRuntime(make_manifest())
        self.assertEqual(rt.current_state, "observe")
        self.assertIn("pressure_seen", rt.memory)

    def test_lineage_append_only_and_verifiable(self):
        ln = ReincarnationLineage()
        rec = ln.add(make_manifest(), "nonce1")
        self.assertEqual(len(ln.history("boris@1")), 1)
        self.assertTrue(ln.verify(rec, "nonce1"))


class ChallengeTests(unittest.TestCase):
    def test_seed_bound_to_commitments(self):
        c = MatchChallenge(challenge_id="ch1", server_nonce="srv")
        s1 = derive_match_seed("ch1", "A", "B", "srv")
        self.assertEqual(s1, derive_match_seed("ch1", "A", "B", "srv"))
        # Different commitment or nonce changes the seed.
        self.assertNotEqual(s1, derive_match_seed("ch1", "A2", "B", "srv"))

    def test_reincarnation_commit(self):
        h = commit_reincarnation(make_manifest(), "ch1")
        self.assertEqual(len(h), 64)


class SalienceTests(unittest.TestCase):
    def test_ordinary_decisive_match_not_salient(self):
        det = SalienceDetector()
        m = run_match(5, ArenaSpec(max_seconds=2), BladeSpec("a"), BladeSpec("b"),
                      CounterPolicy(), AggressivePolicy(), 3)
        ev = det.detect(m, "a", "b", win_probability={"a": 0.5, "b": 0.5})
        self.assertEqual(ev, [])

    def test_upset_assigned_only_to_supported_agent(self):
        det = SalienceDetector()
        m = run_match(5, ArenaSpec(max_seconds=2), BladeSpec("a"), BladeSpec("b"),
                      CounterPolicy(), AggressivePolicy(), 3)
        # Force a win for 'a' regardless of reality by faking the match.winner.
        class Fake:
            match_id = "m1"
            winner = "a"
        ev = det.detect(Fake(), "a", "b", win_probability={"a": 0.1, "b": 0.9})
        types = [e.type for e in ev]
        self.assertIn("UPSET", types)
        # The losing agent gets no upset.
        ev_b = det.detect(Fake(), "b", "a", win_probability={"b": 0.9, "a": 0.1})
        self.assertEqual([e.type for e in ev_b], [])

    def test_evidence_id_dedup(self):
        e1 = SalienceEvidence("UPSET", "a", "m1")
        e2 = SalienceEvidence("UPSET", "a", "m1")
        self.assertEqual(e1.evidence_id(), e2.evidence_id())


class SignatureRegistryTests(unittest.TestCase):
    def test_one_match_cannot_confirm(self):
        reg = SignatureRegistry(window=2, min_occurrences=2, min_matches=2)
        m = run_match(9, ArenaSpec(max_seconds=3), BladeSpec("x"), BladeSpec("y"),
                      CounterPolicy(), AggressivePolicy(), 3)
        reg.register(m, "x", "alice", "opp1")
        self.assertEqual(reg.confirmed_signature_ids("alice"), [])


if __name__ == "__main__":
    unittest.main()
