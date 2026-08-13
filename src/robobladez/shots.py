def compile_shots(episode):
    shots=[{
      "id":"S001","duration_s":5,"purpose":"establish",
      "camera":"wide_arena",
      "canon":{"replay_digest":episode["replay_digest"]},
      "instruction":"Establish the canonical competitors and arena. Do not imply an outcome."
    }]
    for i,b in enumerate(episode["beats"][:10],2):
        shots.append({
          "id":f"S{i:03d}",
          "duration_s":6 if b["importance"]>=0.9 else 4,
          "purpose":b["type"],
          "camera":"impact_close" if b["type"]=="collision" else "result_wide",
          "canon":{
              "round":b["round"],"event_type":b["type"],
              "actor":b["actor"],"target":b["target"],
              "winner":episode["winner"],
              "replay_digest":episode["replay_digest"]
          },
          "instruction":"Cinematic reconstruction only; preserve the canonical event and identity."
        })
    return {"episode_id":episode["episode_id"],"renderer":"LTX-2/ComfyUI","shots":shots}
