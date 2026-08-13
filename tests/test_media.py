import unittest
from robobladez.media import (
    ShotSpec, RenderRequest, RenderJob, RenderArtifact, QAVerdict, RendererManifest,
    build_shot_spec, shot_class_for, SHOT_CLASS_CONTROL, CONTROL_MODES,
    RenderQueue, simulate_render, run_qa, produce_episode,
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


class MediaPipelineTests(unittest.TestCase):
    def test_render_queue_draft_to_artifact(self):
        queue = RenderQueue()
        spec = build_shot_spec(shot_id="s1", shot_class="battle_event")
        job = queue.enqueue(spec, profile="draft", seed=1)
        queue.mark_running(job.job_id)
        art = simulate_render(spec, job)
        self.assertEqual(job.status, "running")
        queue.complete(job, uri=art.uri, digest=art.digest)
        self.assertEqual(job.status, "done")
        self.assertEqual(len(queue.artifacts), 1)

    def test_simulate_render_no_ltx_call(self):
        spec = build_shot_spec(shot_id="s2", shot_class="battle_event")
        job = RenderJob(job_id="j2", request=RenderRequest(shot_spec_uri="s2"))
        art = simulate_render(spec, job, RendererManifest(renderer_version="2.5"))
        self.assertTrue(art.uri.startswith("mock://ltx"))
        self.assertEqual(art.digest, spec.digest())

    def test_produce_episode_end_to_end(self):
        ep = {
            "episode_id": "EP-1", "match_id": "m1", "replay_digest": "abc",
            "winner": "boris",
            "characters": {"boris": ["b:v0"], "morty": ["m:v0"]},
            "beats": [
                {"round": 1, "t": 3.2, "type": "collision", "importance": 0.9,
                 "summary": "impact"},
                {"round": 1, "t": 5.0, "type": "round_result", "importance": 0.8,
                 "summary": "R1"},
            ],
        }
        shots_dict = compile_shots(ep)
        specs = [ShotSpec(**s) for s in shots_dict["shots"]]
        res = produce_episode(specs, winner="boris", profiles="final")
        self.assertEqual(res["accepted"] + res["rejected"], res["shots"])
        self.assertEqual(res["accepted"], res["shots"])  # canonical shots pass QA

    def test_qa_rejects_broken_digest(self):
        spec = build_shot_spec(shot_id="s3", shot_class="battle_event")
        bad_art = RenderArtifact(job_id="j", shot_id="s3", uri="u", digest="WRONG")
        v = run_qa(spec, bad_art)
        self.assertFalse(v.pass_)
        self.assertTrue(any("digest" in f for f in v.failures))

    def test_retake_repairs_interval(self):
        queue = RenderQueue()
        spec = build_shot_spec(shot_id="s4", shot_class="battle_event")
        parent = queue.enqueue(spec, profile="draft")
        retake = queue.retake(spec, parent.job_id, interval=(2.8, 4.1))
        self.assertEqual(retake.request.profile, "retake")
        self.assertEqual(retake.retake_parent, parent.job_id)
        self.assertEqual(retake.interval, [2.8, 4.1])

    def test_reframe_derives_aspect_variant(self):
        queue = RenderQueue()
        spec = build_shot_spec(shot_id="s5", shot_class="battle_event", aspect_ratio="16:9")
        job = queue.enqueue(spec, profile="final")
        master = simulate_render(spec, job)
        shorts = queue.reframe(master, "9:16")
        self.assertIn("9x16", shorts.shot_id)
        self.assertIn("aspect=9:16", shorts.uri)
        self.assertEqual(shorts.digest, master.digest)  # same content, reframed

    def test_produce_episode_reframes_variants(self):
        ep = {
            "episode_id": "EP-1", "match_id": "m1", "replay_digest": "abc",
            "winner": "boris",
            "characters": {"boris": ["b:v0"], "morty": ["m:v0"]},
            "beats": [{"round": 1, "t": 3.2, "type": "collision",
                       "importance": 0.9, "summary": "impact"}],
        }
        shots_dict = compile_shots(ep)
        specs = [ShotSpec(**s) for s in shots_dict["shots"]]
        res = produce_episode(specs, winner="boris", profiles="final",
                              reframe_aspects=("9:16", "4:5"))
        # Every output has 2 aspect variants.
        for o in res["outputs"]:
            self.assertEqual(len(o["variants"]), 2)


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
        for s in beat_shots:
            self.assertTrue(any("winner" in c for c in s["constraints"]))


if __name__ == "__main__":
    unittest.main()
