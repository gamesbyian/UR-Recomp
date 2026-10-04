#!/usr/bin/env python3
"""Identify the stock sound command behind each frontend UI event.

Decision served: the menu visual-language contract
(analysis/generated/menu-visual-language.json, docs/UI-STATE-MAP.md) had sound
timing but no sound identity, because the pinned core exposes no APU ports.
The game, however, queues every sound command in WRAM before the APU driver
drains it, so the identity is readable from ordinary dumps:

- ``82:8000`` (JSL, A = 16-bit word ``hhll``) appends ``ll`` to ``7E:2006+i`` and
  ``hh`` to ``7E:2016+i``, ``i`` = write index ``7E:2002`` (16-entry ring);
  ``82:8035`` sends queued entries to ``$2140-$2143``.
- Frontend wrappers in bank 80 send a priority/volume word ``08vv`` followed by
  ``02nn`` = play sound effect ``nn`` (``80:B0EB`` 3, ``80:B100`` 6, ``80:B115`` 4,
  ``80:B12A`` 2, ``80:B13F`` 1, ``80:B169`` 3).

The probe dumps WRAM before and after each action and records the commands the
action appended. ``new_commands`` and ``classify`` are pure and unit-tested;
``main`` drives snesref.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

import probe_name_entry as names

ROOT = Path(__file__).resolve().parents[1]
RING_HEAD, RING_LO, RING_HI = 0x2002, 0x2006, 0x2016

SETTLE = ["until 009F == D7 3600", "wait 60"]
CARRIER = "_carrier"  # multi-input step that only positions the cursor; the ring may wrap, so it is not recorded
FRONTEND = [  # (event, action lines)
    ("main_cursor_down", ["press down 2", "wait 20"]),
    ("main_cursor_up", ["press up 2", "wait 20"]),
    ("main_confirm_1p_slide", ["press a 2", "wait 90"]),
    ("rider_cursor_right", ["press right 2", "wait 20"]),
    ("rider_cursor_left", ["press left 2", "wait 20"]),
    ("rider_confirm", ["press a 2", "wait 90"]),
    ("tour_cursor_down", ["press down 2", "wait 20"]),
    ("tour_cursor_up", ["press up 2", "wait 20"]),
    ("tour_confirm", ["press a 2", "wait 90"]),
    ("track_cursor_down", ["press down 2", "wait 20"]),
    ("track_back_to_tour", ["press x 2", "wait 90"]),
    ("tour_back_to_rider", ["press x 2", "wait 90"]),
    ("rider_back_to_main", ["press x 2", "wait 90"]),
]


def editor_events(name: str, prefix: str) -> list[tuple[str, list[str]]]:
    """Type ``name`` and confirm it; the final OK press is its own event."""
    moves = names.plan_moves(name)
    return [(f"{prefix}_type_and_move{CARRIER}", moves[:-2]), (f"{prefix}_ok", moves[-2:] + ["wait 60"])]


EDITOR = [
    ("editor_cursor_right", ["press right 1", "wait 20"]),
    ("editor_type_letter", ["press a 2", "wait 20"]),
    ("editor_move_to_delete" + CARRIER, ["press down 1", "wait 12"] + ["press left 1", "wait 12"] * 7),
    ("editor_delete", ["press a 2", "wait 20"]),
]


def script(events: list[tuple[str, list[str]]], prefix: list[str]) -> str:
    lines = list(prefix) + ["dump e00-start"]
    for i, (_, action) in enumerate(events, 1):
        lines += action + [f"dump e{i:02d}"]
    return "\n".join(lines + ["quit"]) + "\n"


def new_commands(before: bytes, after: bytes) -> list[str]:
    """Commands appended to the WRAM sound ring between two dumps (at most 15)."""
    i, head, out = before[RING_HEAD] & 15, after[RING_HEAD] & 15, []
    while i != head:
        out.append(f"{after[RING_HI + i]:02X}{after[RING_LO + i]:02X}")
        i = (i + 1) & 15
    return out


def classify(cmds: list[str]) -> list[int]:
    """Sound-effect ids (op 02) in command order."""
    return [int(c[2:], 16) for c in cmds if c.startswith("02")]


def run(args, work: Path, events: list[tuple[str, list[str]]], prefix: list[str]) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    (work / "s.script").write_text(script(events, prefix))
    env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1", SNESREF_WRAM_FILL="0",
               SNESREF_SCRIPT=str(work / "s.script"), SNESREF_DUMP_DIR=str(work))
    with open(work / "snesref.log", "w") as log:
        subprocess.run([str(args.snesref), str(args.core), str(args.rom)], env=env, cwd=work,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    out, prev = {}, (work / "e00-start.wram.bin").read_bytes()
    for i, (event, _) in enumerate(events, 1):
        cur = (work / f"e{i:02d}.wram.bin").read_bytes()
        prev, before = cur, prev
        if event.endswith(CARRIER):
            continue
        cmds = new_commands(before, cur)
        out[event] = {"commands": cmds, "sfx": classify(cmds), "menu_after": f"0x{cur[0x9F]:02X}"}
    return out


def evaluate(obs: dict) -> dict:
    sfx = lambda e: obs[e]["sfx"]
    cursor = [e for e in obs if "cursor" in e]
    return {
        "cursor_moves_play_sfx_3": all(sfx(e) and set(sfx(e)) == {3} for e in cursor),
        "forward_slides_play_sfx_2": sfx("main_confirm_1p_slide") == [2] and sfx("tour_confirm") == [2],
        "rider_confirm_plays_sfx_4_then_slide": sfx("rider_confirm") == [4, 2],
        "back_slides_play_sfx_1": all(sfx(e) == [1] for e in ("track_back_to_tour", "tour_back_to_rider", "rider_back_to_main")),
        "editor_keys_play_sfx_6": sfx("editor_type_letter") == [6] and sfx("editor_delete") == [6],
        "name_ok_plays_sfx_4_and_saving_slides_back": sfx("forbidden_ok") == [4] and sfx("valid_ok") == [4, 1],
    }


def main() -> int:
    tools = ROOT / ".tools/src"
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snesref", type=Path, default=tools / "snesrecomp/build-snesref/snesref")
    ap.add_argument("--core", type=Path, default=tools / "snes9x-libretro/libretro/snes9x_libretro.so")
    ap.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/menu-sfx-ids.json")
    args = ap.parse_args()
    editor_prefix = names.route_prefix()
    obs = {}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        obs.update(run(args, td / "frontend", FRONTEND, SETTLE))
        obs.update(run(args, td / "editor", EDITOR, editor_prefix))
        obs.update(run(args, td / "forbidden", editor_events("SONIC", "forbidden"), editor_prefix))
        obs.update(run(args, td / "valid", editor_events("ZED", "valid"), editor_prefix))
    checks = evaluate(obs)
    table = {}
    for event, o in obs.items():
        for n in o["sfx"]:
            table.setdefault(n, []).append(event)
    report = {
        "schema_version": 1,
        "purpose": "Stock sound-effect id per frontend UI event, read from the WRAM sound-command ring.",
        "mechanism": "82:8000 queues 16-bit sound commands at 7E:2006/7E:2016 (index 7E:2002); 02nn = play SFX nn, 08vv precedes it",
        "events": obs,
        "sfx_to_events": {str(k): v for k, v in sorted(table.items())},
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "limits": ["Sound identity is the driver's command id, not a decoded sample; the APU sample bank is not mapped.",
                   "Scene and in-race sounds (bank 83 wrappers 83:A286-A4BD, bank 81/82/83 direct sites) are not covered."],
    }
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({"checks": checks, "sfx_to_events": report["sfx_to_events"]}, indent=1))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
