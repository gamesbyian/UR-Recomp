#!/usr/bin/env python3
"""Summarize the recovered USJO v8 control/state machine from static inventory."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "analysis" / "generated" / "usjo8-static-inventory.json"
JSON_OUT = ROOT / "analysis" / "generated" / "usjo8-control-model.json"
MD_OUT = ROOT / "analysis" / "generated" / "usjo8-control-model.md"

MEANINGS = {
    "mode": {"1": "jump search", "2": "first-twist timing search", "3": "stunt-combination search", "4": "best-candidate replay/evaluation", "5": "done"},
    "jumpstatus": {"0": "idle", "1": "trying to jump", "2": "airborne/rising", "3": "past peak", "4": "landed"},
    "twiststatus": {"0": "idle/ready", "1": "waiting for backward leg", "2": "waiting for forward leg"},
    "tabletopstatus": {"0": "idle/waiting", "1": "first half", "2": "second half", "6": "complete"},
    "zflipstatus": {"0": "idle/waiting", "1": "active until counter advances"},
    "flipstatus": {"0": "idle/waiting", "1": "active until counter advances"},
    "rollstatus": {"0": "idle/waiting", "1": "active until counter advances"},
    "strategy": {"1": "build up", "3": "tear down from maxima", "4": "replay best/finish"},
}


def build_model(inventory: dict) -> dict:
    domains = {}
    for item in inventory["state_assignments"]:
        domain = domains.setdefault(item["name"], {"values": set(), "assignment_lines": []})
        domain["values"].add(item["value"])
        domain["assignment_lines"].append(item["line"])
    states = {}
    for name, domain in domains.items():
        values = sorted(domain["values"], key=lambda value: int(value) if value.isdigit() else value)
        states[name] = {
            "values": values,
            "meanings": {value: MEANINGS.get(name, {}).get(value, "unlabeled recovered state") for value in values},
            "assignment_count": len(domain["assignment_lines"]),
            "first_assignment_line": min(domain["assignment_lines"]),
            "last_assignment_line": max(domain["assignment_lines"]),
        }
    return {
        "schema_version": 1,
        "source_inventory": str(INVENTORY.relative_to(ROOT)),
        "states": states,
        "controller_signals": {
            "jumping": "B button",
            "reverse": "swap forward/reverse horizontal direction",
            "flipping": "R when moving right, L when moving left",
            "rolling": "L when moving right, R when moving left",
            "xing": "X button",
        },
        "interpretation": {
            "status": "recovered-source control semantics",
            "warning": "This documents how USJO v8 drives Snes9x, not verified game-internal state names.",
        },
    }


def render_markdown(model: dict) -> str:
    lines = [
        "# USJO v8 control/state model",
        "",
        "This summarizes the optimizer itself. State labels describe recovered script behavior,",
        "not game-internal semantics unless separately reproduced.",
        "",
        "| Script state | Values | Meaning | Assignments |",
        "|---|---|---|---:|",
    ]
    for name, state in model["states"].items():
        values = ", ".join(state["values"])
        meaning = "; ".join(f"{value}={state['meanings'][value]}" for value in state["values"])
        lines.append(f"| `{name}` | `{values}` | {meaning} | {state['assignment_count']} |")
    lines += [
        "",
        "## Controller translation",
        "",
        "- `jumping` drives B.",
        "- `xing` drives X.",
        "- `flipping` and `rolling` choose opposite shoulder buttons based on travel direction.",
        "- `reverse` temporarily swaps the held horizontal direction for twist execution.",
        "- Outside a reverse interval, the bot continuously holds the current travel direction.",
        "",
        "The important implementation consequence is that v8 is a feedback controller, not a fixed",
        "movie: stunt-counter changes and air/rotation working state determine subsequent inputs.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    model = build_model(inventory)
    JSON_OUT.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    MD_OUT.write_text(render_markdown(model), encoding="utf-8")


if __name__ == "__main__":
    main()
