import argparse, json
from .demo import run_demo
from .audit import run_audit
from .league import run_season
from .simulate import simulate_full_stack
from .mvp import run_mvp
from .agent import AgentState
from .battle import run_battle
from .model import BladeSpec
from .policy import CenterControlPolicy, AggressivePolicy, CounterPolicy
from .zoo import make_body


def _season(out: str) -> dict:
    entries = [
        ("boris", make_body("balanced", "-boris"), CounterPolicy()),
        ("morty", make_body("heavy", "-morty"), AggressivePolicy()),
        ("alice", make_body("light", "-alice"), CenterControlPolicy()),
    ]
    return run_season(entries, out_dir=out, seed=2026, rounds=3)


def _battle(out: str) -> dict:
    boris = AgentState("boris")
    morty = AgentState("morty")
    outcome = run_battle(
        boris, make_body("balanced", "-boris"),
        morty, make_body("heavy", "-morty"),
        mechanical_runs=40, strategic_rounds=5, base_seed=9000,
        out_dir=out,
    )
    return {
        "mechanical_win_probability": outcome.mechanical.win_probability,
        "mechanical_advantages": outcome.mechanical.advantages,
        "mechanical_vulnerabilities": outcome.mechanical.vulnerabilities,
        "chosen_avatars": {
            k: v.manifest.reincarnation_id for k, v in outcome.avatars.items()
        },
        "winner": outcome.match.winner,
        "winner_agent_id": outcome.winner_agent_id(),
        "reflections": outcome.reflections,
        "salience": {k: [e["type"] for e in v] for k, v in outcome.salience.items()},
        "daimons": {
            k: {"dominant": v.daimon.dominant(),
                "affinities": v.daimon.affinities,
                "stage": v.daimon.stage,
                "name": v.daimon.name}
            for k, v in (("boris", boris), ("morty", morty))
        },
    }


def _simulate(out: str) -> dict:
    entries = [
        ("boris", make_body("balanced", "-boris"), CounterPolicy()),
        ("morty", make_body("heavy", "-morty"), AggressivePolicy()),
        ("alice", make_body("light", "-alice"), CenterControlPolicy()),
    ]
    return simulate_full_stack(entries, out_dir=out, seed=2026, rounds=3,
                               mechanical_runs=12, profiles="final")


def main():
    p = argparse.ArgumentParser(prog="robobladez")
    sp = p.add_subparsers(dest="cmd", required=True)
    d = sp.add_parser("demo"); d.add_argument("--out", default="./out")
    a = sp.add_parser("audit"); a.add_argument("--seeds", type=int, default=250)
    s = sp.add_parser("season"); s.add_argument("--out", default="./out")
    b = sp.add_parser("battle"); b.add_argument("--out", default="./out")
    sim = sp.add_parser("simulate"); sim.add_argument("--out", default="./out")
    mv = sp.add_parser("mvp"); mv.add_argument("--out", default="./out/mvp")
    mv.add_argument("--agents", nargs="*", default=["boris", "morty"])
    mv.add_argument("--seed", type=int, default=2026)
    mv.add_argument("--rounds", type=int, default=3)
    mv.add_argument("--no-render", action="store_true")
    mx = sp.add_parser("matrix", help="legacy policy-zoo matchup matrix analysis")
    mx.add_argument("--tsv", default="matrix.tsv")
    ra = sp.add_parser("audit-reincarnations",
                       help="strategy audit: decisive rate + non-transitivity over profiles x bodies")
    ra.add_argument("--seeds", type=int, default=30)
    ra.add_argument("--rounds", type=int, default=3)
    ra.add_argument("--bodies", nargs="*", default=["balanced", "heavy", "light"])
    x = p.parse_args()
    if x.cmd == "demo":
        print(json.dumps(run_demo(x.out), indent=2))
    elif x.cmd == "audit":
        r = run_audit(x.seeds)
        print(json.dumps({k: v for k, v in r.items() if k != "gameplay_sample"},
                         indent=2))
    elif x.cmd == "season":
        r = _season(x.out)
        print(json.dumps({
            "matches": r["matches"],
            "standings": r["standings"],
            "daimons": {k: {"dominant": max(v["affinities"], key=v["affinities"].get),
                            "affinities": v["affinities"]}
                        for k, v in r["daimons"].items()},
            "signature_counts": {k: len(v) for k, v in r["signatures"].items()},
        }, indent=2))
    elif x.cmd == "simulate":
        print(json.dumps(_simulate(x.out), indent=2))
    elif x.cmd == "mvp":
        run = run_mvp(out_dir=x.out, agents=x.agents, seed=x.seed,
                      rounds=x.rounds, render=not x.no_render)
        print(json.dumps(run, indent=2))
    elif x.cmd == "matrix":
        from . import meta
        print(json.dumps(meta.analyze(x.tsv), indent=2))
    elif x.cmd == "audit-reincarnations":
        from .reincarnation_audit import audit_reincarnations
        r = audit_reincarnations(seeds=x.seeds, rounds=x.rounds, bodies=tuple(x.bodies))
        print(json.dumps(r, indent=2))
    else:
        print(json.dumps(_battle(x.out), indent=2))


if __name__ == "__main__":
    main()
