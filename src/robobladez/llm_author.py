"""LLMReincarnationAuthor (rmdev2 Phase 4, high-urgency #1).

The defining RoboBladez mechanic: "the persistent AI writes its own battle-self."
This author calls an LLM (via the `hermes` CLI) to produce RBZ-RC-1 JSON — NOT
Python — then parse -> validate -> normalize -> commit. On any failure (bad JSON,
validation error, timeout, LLM down) it falls back to the deterministic
BaselineReincarnationAuthor so the match can always proceed.

The LLM is only called ONCE per match (authoring), never per physics tick.
"""
from __future__ import annotations
import json, re, subprocess, tempfile
from typing import Any

from .mechanical import MechanicalMatchupReport
from .reincarnation import ReincarnationManifest, validate, ValidationError
from .reincarnation_author import ReincarnationContext, BaselineReincarnationAuthor


def _hermes_call(prompt: str, timeout: int = 90) -> str:
    """Call hermes -z with the prompt; return stdout. Raises on failure."""
    proc = subprocess.run(
        ["hermes", "-z", prompt],
        capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"hermes failed rc={proc.returncode}: {proc.stderr[-500:]}")
    return proc.stdout


class LLMReincarnationAuthor:
    """Authors an RBZ-RC-1 battle-self via an LLM, falling back to baseline."""

    def __init__(self, agent_version: str, author: str = "",
                 hermes_timeout: int = 90):
        self.agent_version = agent_version
        self.author_id = author or agent_version.split("@")[0]
        self.hermes_timeout = hermes_timeout
        self._baseline = BaselineReincarnationAuthor(agent_version, self.author_id)
        self.last_raw: str = ""        # last LLM output (for debugging)
        self.last_fallback_reason: str = ""

    def author(self, context: ReincarnationContext,
               target_match: str = "", reincarnation_id: str = "",
               parent_id: str = "") -> ReincarnationManifest:
        try:
            manifest = self._llm_author(context, reincarnation_id, parent_id, target_match)
            if manifest is not None:
                return manifest
            raise RuntimeError(self.last_fallback_reason or "llm returned None")
        except Exception as e:  # noqa: BLE001 — fall back on any failure
            self.last_fallback_reason = str(e)
            return self._baseline.reincarnate(
                context.mechanical_report, context.agent_id,
                _opponent_id(context), target_match=target_match,
                reincarnation_id=reincarnation_id, parent_id=parent_id)

    def _llm_author(self, context: ReincarnationContext,
                    reincarnation_id: str, parent_id: str,
                    target_match: str) -> ReincarnationManifest | None:
        prompt = _build_prompt(context, reincarnation_id, parent_id, target_match)
        raw = _hermes_call(prompt, timeout=self.hermes_timeout)
        self.last_raw = raw
        parsed = _extract_json(raw)
        if parsed is None:
            self.last_fallback_reason = "no JSON in LLM output"
            return None
        try:
            return _manifest_from_dict(
                parsed, self.agent_version, reincarnation_id, parent_id,
                author=self.author_id, target_match=target_match)
        except (ValueError, TypeError, ValidationError) as e:
            self.last_fallback_reason = f"manifest invalid: {e}"
            return None


# ---------------------------------------------------------------------------
# Prompt + parsing helpers
# ---------------------------------------------------------------------------
_TELEMETRY = ("distance", "closing_speed", "relative_tangential_speed",
              "self_radius_fraction", "opponent_radius_fraction",
              "self_energy_fraction", "opponent_energy_fraction",
              "self_integrity_fraction", "opponent_integrity_fraction",
              "self_spin", "opponent_spin", "time", "arena_radius")

_MEM_OPS = ("set", "add")


def _build_prompt(ctx: ReincarnationContext, rc_id: str, parent: str,
                  target_match: str) -> str:
    report = _report_summary(ctx.mechanical_report, ctx.agent_id)
    sys_ = (
        "You are the author of an autonomous battle-self for a deterministic "
        "spinning-top AI competition. Output ONLY a valid JSON object (no prose, "
        "no markdown fences) conforming to the RBZ-RC-1 state-machine schema.\n\n"
        f"SCHEMA:\n"
        f"- format: \"RBZ-RC-1\"\n"
        f"- compute_class: \"C1\" (max 32 states)\n"
        f"- memory: [{{name,type:u8,initial,max_abs}}]\n"
        f"- states: [{{id, action:{{radial,tangential,torque,boost each in [-1,1], "
        f"boost in [0,1]}}, "
        f"memory:[{{name,op:set|add,value}}], "
        f"transitions:[{{if:{{op:lt|gt|gte|lte, lhs, threshold}}, to}}]}}]\n"
        f"- initial_state: must equal a state id\n"
        f"- strategy_thesis: short string\n\n"
        f"AVAILABLE TELEMETRY (lhs keys): {', '.join(_TELEMETRY)} plus "
        f"memory.<slot>.\n"
        f"Memory ops: {_MEM_OPS}. Must be bounded and deterministic.\n"
        f"Constraints: every transition target must be a defined state; values "
        f"finite; keep it small (3-8 states).\n\n"
        f"CONTEXT:\n"
        f"- agent_id: {ctx.agent_id}\n"
        f"- reincarnation_id: {rc_id or ctx.agent_id + '-r001'}\n"
        f"- parent_reincarnation_id: {parent or 'none'}\n"
        f"- target_match: {target_match or 'unknown'}\n"
        f"- opponent_model: {json.dumps(ctx.opponent_model or {})[:500]}\n"
        f"- previous_reincarnations: {json.dumps(ctx.previous_reincarnations[:3] or [])[:400]}\n"
        f"- reflections: {json.dumps(ctx.reflections[:2] or [])[:400]}\n"
        f"- daimon_advice: {ctx.daimon_advice or 'none'}\n"
        f"- human_mentor: {json.dumps(ctx.human_mentor_messages[:2] or [])[:300]}\n"
        f"- mechanical_report: {report}\n\n"
        f"Author a battle-self that exploits the opponent's mechanical weaknesses "
        f"revealed above. Return the JSON object only."
    )
    return sys_


def _report_summary(report: MechanicalMatchupReport | None, me: str) -> str:
    if report is None:
        return "{}"
    return json.dumps({
        "win_probability": report.win_probability,
        "per_body": report.per_body,
        "advantages": report.advantages.get(me, []),
        "vulnerabilities": report.vulnerabilities.get(me, []),
    })[:900]


def _opponent_id(ctx: ReincarnationContext) -> str:
    return list(ctx.opponent_model.keys())[0] if ctx.opponent_model else ""


def _extract_json(text: str) -> dict | None:
    """Pull the first JSON object out of LLM output (tolerates fences/prose)."""
    # Strip markdown fences.
    text = re.sub(r"```(?:json)?", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find the first {...} balanced block.
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _manifest_from_dict(d: dict, agent_version: str, rc_id: str, parent: str,
                        author: str, target_match: str) -> ReincarnationManifest:
    """Build + validate a ReincarnationManifest from an LLM-authored dict.

    Robust to LLM quirks: state ids are coerced to strings; initial_state falls
    back to the first state id; missing memory defaults to empty.
    """
    from .reincarnation import parse_memory
    memory = parse_memory(d.get("memory") or [])
    states_raw = d.get("states") or []
    # Coerce state ids to strings (LLM may emit ints) and fix transition targets.
    states = []
    id_map = {}
    for s in states_raw:
        sid = str(s.get("id", "")).strip()
        id_map[sid] = sid
        s2 = dict(s)
        s2["id"] = sid
        # Re-map transition targets to strings.
        trans = []
        for t in s.get("transitions") or []:
            t2 = dict(t)
            t2["to"] = str(t.get("to", "")).strip()
            trans.append(t2)
        s2["transitions"] = trans
        states.append(s2)
    initial_raw = d.get("initial_state")
    initial = str(initial_raw).strip() if initial_raw is not None else ""
    if not initial and states:
        initial = states[0]["id"]
    manifest = ReincarnationManifest(
        format="RBZ-RC-1",
        reincarnation_id=rc_id or d.get("reincarnation_id") or "",
        agent_version=agent_version,
        target_match=target_match or d.get("target_match") or "",
        compute_class="C1",
        author=author,
        parent_reincarnation_id=parent,
        memory=memory,
        states=tuple(states),
        initial_state=initial,
        strategy_thesis=d.get("strategy_thesis") or "",
    )
    validate(manifest)  # raises ValidationError if invalid
    return manifest
