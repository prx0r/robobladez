import unittest
from robobladez.media import (
    ShotSpec, RenderRequest, RenderJob, RenderArtifact, QAVerdict,
    build_shot_spec, shot_class_for, SHOT_CLASS_CONTROL, CONTROL_MODES,
)
from robobladez.shots import compile_shots


class ShotSpecTests(unittest.TestCase):
    def test_control_mode_from_shot_class(self):
        self.assertEqual(shot_class_for("establish"), "establish_arena")
        self.assertEqual(shot_class_for("collision"), "battle_event")
        s = build_shot_spec(shot_id="s1", shot_class="establish_arena")
        self.assertEqual(s.control_mode, "T2V")
        s2 = build_shot_spec(shot_id="s2", shot_class="battle_event")
        self.assertEqual(s2.control_mode, "KEYFRAME")

    def test_control_modes_are_legal(self):
        for c in SHOT_CLASS_CONTROL.values():
            self.assertIn(c, CONTROL_MODES)

    def test_digest_stable_and_narrative_insensitive(self):
        s1 = build_shot_spec(shot_id="s", prompt="A")
        s2 = build_shot_spec(shot_id="s", prompt="B")
        self.assertEqual(s1.digest(), s2.digest())  # prompt is narrative-only
        s3 = build_shot_spec(shot_id="s", constraints=["X"])
        self.assertNotEqual(s1.digest(), s3.digest())  # constraints are executable

    def test_renderer_objects(self):
        rq = RenderRequest(shot_spec_uri="s1", profile="final")
        job = RenderJob(job_id="j1", request=rq)
        art = RenderArtifact(job_id="j1", shot_id="s1", uri="r2://x", digest="d")
        qa = QAVerdict(shot_id="s1", pass_=True, passed_checks=["ok"])
        self.assertEqual(qa.to_dict()["pass"], True)
        self.assertEqual(job.status, "queued")


class ShotCompileTests(unittest.TestCase):
    def setUp(self):
        self.ep = {
            "episode_id": "EP-1", "match_id": "m1", "replay_digest": "abc",
            "winner": "boris",
            "characters": {"boris": ["boris:talisman:v0"],
                           "morty": ["morty:talisman:v0"]},
            "beats": [
                {"round": 1, "t": 3.2, "type": "collision", "importance": 0.9,
                 "summary": "impact"},
                {"round": 1, "t": 5.0, "type": "round_result", "importance": 0.8,
                 "summary": "R1"},
            ],
        }

    def test_compiles_schema_valid_shots(self):
        out = compile_shots(self.ep)
        self.assertEqual(len(out["shots"]), 5)  # establish + 2 intros + 2 beats
        for s in out["shots"]:
            self.assertIn("shot_id", s)
            self.assertIn("canonicality", s)
            self.assertIn("control_mode", s)
            self.assertIn("constraints", s)

    def test_canonical_event_keeps_winner_constraint(self):
        out = compile_shots(self.ep)
        beat_shots = [s for s in out["shots"] if s["canonicality"] == "CANONICAL_EVENT"]
        self.assertTrue(beat_shots)
        # Winner preserved in constraints of battle-event shots.
        battle = [s for s in beat_shots]
        for s in battle:
            self.assertTrue(any("winner" in c for c in s["constraints"]))


if __name__ == "__main__":
    unittest.main()
