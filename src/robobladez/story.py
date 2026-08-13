def compile_story(match,analysis):
    beats=[]
    for rnd in match.rounds:
        for e in sorted(rnd.events,key=lambda x:(x.tick,x.type)):
            if e.type in {"collision","round_end"} and (e.importance>=0.55 or e.type=="round_end"):
                beats.append({
                    "round":rnd.round_no,"t":e.t,"type":e.type,
                    "actor":e.actor,"target":e.target,
                    "importance":e.importance,"data":e.data
                })
    return {
        "episode_id":f"EP-{match.match_id}",
        "match_id":match.match_id,
        "replay_digest":match.replay_digest,
        "winner":match.winner,
        "beats":beats[:16],
        "characters":{
            bid:{"phenotype":v["phenotype"],"daimon":v["daimon_projection"]}
            for bid,v in analysis.items()
        },
        "hard_constraints":[
            "winner must match canonical replay",
            "round order may not change",
            "events may be omitted/compressed but not contradicted",
            "narrative daimon projection may not alter simulation facts"
        ]
    }
