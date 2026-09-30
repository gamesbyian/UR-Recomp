#!/usr/bin/env python3
"""Extract the historical USJO v8 boost/scoring model as structured evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "imported" / "tas-bots" / "usjo8.lua"
JSON_OUT = ROOT / "analysis" / "generated" / "usjo8-boost-model.json"
MD_OUT = ROOT / "analysis" / "generated" / "usjo8-boost-model.md"

COUNTER_MAP = {
    "completedtwists": "twists",
    "completedtabletops": "tabletops",
    "completedzflips": "zflips",
    "completedrolls": "rolls",
    "completedflips": "flips",
}
COND_RE = re.compile(r"^\s*(?:if|elseif)\s+(?P<counter>completed[a-z]+)\s*(?P<op>==|>=)\s*(?P<threshold>\d+)\s+then")
ADD_RE = re.compile(r"^\s*thisboostmeter\s*=\s*thisboostmeter\s*\+\s*(?P<value>\d+)")


def build_model(text: str) -> dict:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if "thisboostmeter = 0" in line)
    end = next(i for i in range(start, len(lines)) if "finalscore = thisboostmeter + lastspeed" in lines[i])
    rewards = {name: [] for name in COUNTER_MAP.values()}
    pending = None
    for i in range(start, end + 1):
        condition = COND_RE.match(lines[i])
        if condition and condition.group("counter") in COUNTER_MAP:
            pending = {
                "line": i + 1,
                "counter": COUNTER_MAP[condition.group("counter")],
                "operator": condition.group("op"),
                "threshold": int(condition.group("threshold")),
            }
            continue
        addition = ADD_RE.match(lines[i])
        if addition and pending:
            pending["reward"] = int(addition.group("value"))
            pending["reward_line"] = i + 1
            rewards[pending["counter"]].append(pending)
            pending = None

    return {
        "schema_version": 1,
        "source": str(SOURCE.relative_to(ROOT)),
        "source_lines": [start + 1, end + 1],
        "reward_rules": rewards,
        "score_rule": "finalscore = thisboostmeter + lastspeed",
        "gates": [
            {"condition": "lastspeed < 0", "effect": "thisboostmeter = 0", "lines": [987, 988]},
            {"condition": "realboostmeter == 0", "effect": "thisboostmeter = 0", "lines": [990, 991]},
        ],
        "interpretation": {
            "status": "recovered-source evidence only",
            "warning": "These are USJO v8 optimization assumptions, not locally verified game boost values.",
        },
    }


def render_markdown(model: dict) -> str:
    rows = []
    for stunt, rules in model["reward_rules"].items():
        for rule in rules:
            rows.append(f"| {stunt} | {rule['operator']} {rule['threshold']} | {rule['reward']} | {rule['line']}-{rule['reward_line']} |")
    return "\n".join([
        "# USJO v8 historical boost model",
        "",
        "This is a structured extraction of what the recovered 2008 optimizer assumes.",
        "It is not a claim that these are the game's true boost units until reproduced locally.",
        "",
        "| Stunt counter | Condition | Added boost score | Source lines |",
        "|---|---:|---:|---:|",
        *rows,
        "",
        "The optimizer sums the applicable stunt reward contributions, then zeros the derived",
        "boost score if horizontal progress is negative or if the runtime byte it calls",
        "`realboostmeter` is zero. Its candidate score is derived boost plus horizontal speed.",
        "",
    ])


def main() -> None:
    model = build_model(SOURCE.read_text(encoding="utf-8"))
    JSON_OUT.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    MD_OUT.write_text(render_markdown(model), encoding="utf-8")


if __name__ == "__main__":
    main()
