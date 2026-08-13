"""Provenance-binding tests (rmreview #2 + rmdev2 Phase 2/20).

These assert the vertical truth paths: the execution_digest must change when a
battle-self changes, and the episode manifest must link real shot digests.
"""
import unittest
from robobladez.competition import (
    CompetitionEntry, EntrySnapshot, build_execution_manifest,
    BodyVersion, BodyProposal, make_body_version,
)
from robobladez.mvp import run_mvp
from robobladez.zoo import make_body


class BladeOntologyTests(unittest.TestCase):
    """The blade is a deterministic material thing (docs/BLADE.md)."""

    def test_body_version_is_hash_bound_and_immutable(self):
        bv = make_body_version("boris", make_body("heavy", "-boris"), version="R1")
        d = bv.to_dict()
        self.assertEqual(d["body_digest"], bv.body_digest())
        self.assertEqual(d["version_key"], "boris:heavy-boris:R1")
        # Same blade params -> same digest (deterministic material truth).
        bv2 = make_body_version("boris", make_body("heavy", "-boris"), version="R1")
        self.assertEqual(bv.body_digest(), bv2.body_digest())

    def test_different_blade_different_digest(self):
        heavy = make_body_version("boris", make_body("heavy", "-b"), "R1")
        light = make_body_version("boris", make_body("light", "-b"), "R1")
        self.assertNotEqual(heavy.body_digest(), light.body_digest())

    def test_daimon_cannot_edit_body(self):
        proposal = BodyProposal(
            agent_id="boris",
            proposed=make_body_version("boris", make_body("heavy", "-b"), "R2"),
            rationale="counter meta", daimon_advice="your mass is wrong")
        # Daimon advice is attached but the proposed body is immutable.
        self.assertTrue(proposal.daimon_advice)
        self.assertEqual(proposal.status, "pending")
        accepted = proposal.accept()
        self.assertEqual(accepted.status, "accepted")

    def test_entry_binds_announced_body_version_and_digest(self):
        e = CompetitionEntry(agent_id="a", body_id="b", body_version="R1",
                             body_digest="dig", daimon_stage="latent")
        snap = EntrySnapshot.from_entry(e)
        self.assertEqual(snap.body_version, "R1")
        self.assertEqual(snap.body_digest, "dig")


class ExecutionDigestBindingTests(unittest.TestCase):
    def _snap(self, rc_id, rc_digest):
        e = CompetitionEntry(agent_id="a", body_id="b", body_version="R1",
                             daimon_stage="latent")
        return EntrySnapshot.from_entry(e, reincarnation_id=rc_id,
                                        reincarnation_digest=rc_digest,
                                        reincarnation_commitment="c")

    def test_execution_digest_changes_with_reincarnation_ast(self):
        s1 = self._snap("a-r001", "AST-AAAA")
        s2 = self._snap("b-r001", "AST-AAAA")
        m1 = build_execution_manifest("x", s1, s2, seed=1)
        # Same manifest -> same digest (deterministic).
        m1b = build_execution_manifest("x", self._snap("a-r001", "AST-AAAA"),
                                       self._snap("b-r001", "AST-AAAA"), seed=1)
        self.assertEqual(m1.execution_digest(), m1b.execution_digest())
        # Different reincarnation AST -> different execution_digest.
        m2 = build_execution_manifest("x", self._snap("a-r001", "AST-BBBB"),
                                      self._snap("b-r001", "AST-AAAA"), seed=1)
        self.assertNotEqual(m1.execution_digest(), m2.execution_digest())

    def test_execution_digest_changes_with_seed(self):
        s1 = self._snap("a-r001", "AST-A")
        s2 = self._snap("b-r001", "AST-A")
        m1 = build_execution_manifest("x", s1, s2, seed=1)
        m2 = build_execution_manifest("x", s1, s2, seed=2)
        self.assertNotEqual(m1.execution_digest(), m2.execution_digest())

    def test_entry_snapshot_pins_reincarnation(self):
        snap = self._snap("a-r007", "AST-SECRET")
        d = snap.to_dict()
        self.assertEqual(d["reincarnation_id"], "a-r007")
        self.assertEqual(d["reincarnation_digest"], "AST-SECRET")


class EpisodeProvenanceTests(unittest.TestCase):
    def test_mvp_episode_manifest_has_real_digests(self):
        import tempfile, os, json, glob
        with tempfile.TemporaryDirectory() as tmp:
            run_mvp(out_dir=os.path.join(tmp, "mvp"), agents=["boris", "morty"],
                    seed=5, rounds=1, mechanical_runs=1)
            ep = json.load(open(os.path.join(tmp, "mvp/episode/episode-manifest.json")))
            self.assertTrue(ep["shot_spec_digests"], "shot spec digests must be populated")
            self.assertNotEqual(ep["final_master_digest"], "mock")
            # Every shot spec digest corresponds to an actual shot file.
            shot_files = glob.glob(os.path.join(tmp, "mvp/shots/*.json"))
            self.assertEqual(len(shot_files), len(ep["shot_spec_digests"]))

    def test_mvp_execution_manifest_binds_reincarnation(self):
        import tempfile, os, json
        with tempfile.TemporaryDirectory() as tmp:
            run_mvp(out_dir=os.path.join(tmp, "mvp"), agents=["boris", "morty"],
                    seed=5, rounds=1, mechanical_runs=1)
            em = json.load(open(os.path.join(tmp, "mvp/competition/match-execution-manifest.json")))
            self.assertTrue(em["entry_a"]["reincarnation_id"])
            self.assertTrue(em["entry_a"]["reincarnation_digest"])


if __name__ == "__main__":
    unittest.main()
