#!/usr/bin/env python3
"""Derive two isolated cinematic 2P input scripts from pinned genuine Baldosa 2P.

Only alters controller commands *after* the game's genuine GO gate.
Never edits guest execution, track geometry, menus, race physics or rendering.
B=jump, L/R=airborne flip/roll, A=twist. Held B 24 + B+L/R 8\nfollows independently documented original route race-rotation-left.script.
A button press is only an *attempt*: presence of a trick must be witnessed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

PREFIX = "until 0E1F != 00\n"
EXPECTED_TAIL = ("press right+p2:right 60\ndump t060\n"
                 "press right+p2:right 60\ndump t120\n"
                 "press right+p2:right 120\ndump t240\n"
                 "press right+p2:right 240\ndump t480\nquit")

# Include landings after each pulse: a pressed button is not proof a stunt lands.
ROUTES = {
    # Native first-race airborne precedent is sustained B 24 frames followed
    # by B+L/R 8 frames, then a recovery interval (race-rotation-left.script).
    # Each B+rotation is an attempt, never proof it triggered/landed a trick.
    "p1-leads": [
        ("right", 170),
        ("right+b", 24), ("right+b+r", 8), ("right", 30),
        ("p2:right", 115), ("p2:right+p2:b", 24),
        ("p2:right+p2:b+p2:l", 8), ("p2:right", 32),
        ("right+p2:right", 60), ("right+b+p2:right", 24),
        ("right+b+l+p2:right", 8), ("right+p2:right", 48),
        ("right+p2:right+p2:b", 24),
        ("right+p2:right+p2:b+p2:r", 8), ("right+p2:right", 65),
        ("right+b+p2:right", 24), ("right+a+p2:right", 18),
        ("right+p2:right", 90),
        ("right+p2:right+p2:b", 24),
        ("right+p2:right+p2:a", 16),
        ("right+p2:right", 240),
        ("right+b+p2:right+p2:b", 24),
        ("right+b+r+p2:right+p2:b+p2:l", 8),
        ("right+p2:right", 330),
    ],
    "p2-leads": [
        ("p2:right", 195),
        ("p2:right+p2:b", 24), ("p2:right+p2:b+p2:r", 8),
        ("p2:right", 35),
        ("right", 120), ("right+b", 24),
        ("right+b+l", 8), ("right", 35),
        ("right+p2:right", 80),
        ("right+p2:right+p2:b", 24),
        ("right+p2:right+p2:a", 16),
        ("right+p2:right", 60),
        ("right+b+p2:right", 24),
        ("right+b+r+p2:right", 8),
        ("right+p2:right", 110),
        ("right+p2:right+p2:b", 24),
        ("right+p2:right+p2:b+p2:l", 8),
        ("right+p2:right", 70),
        ("right+b+p2:right", 24),
        ("right+a+p2:right", 24),
        ("right+p2:right", 310),
        ("right+p2:right+p2:b", 24),
        ("right+p2:right+p2:b+p2:r", 8),
        ("right+p2:right", 240),
    ],
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def produce(source: str, route: str) -> tuple[str, dict]:
    if route not in ROUTES:
        raise ValueError(f"Unknown route {route}")
    if source.count(PREFIX) != 1 or source.count(EXPECTED_TAIL) != 1:
        raise ValueError("Pinned source GO/tail must be unique and unchanged")
    if not source.rstrip().endswith(EXPECTED_TAIL) or source.count("turbo on\n") != 1:
        raise ValueError("Route tail / execution speed unknown")
    before, _ = source.split(PREFIX, 1)
    if "turbo off" in before:
        raise ValueError("Original already had altered turbo policy")
    script = before + PREFIX + "dump cinematic-go\nturbo off\n"
    # The framework's scene dumps are read-only, consume zero guest frames
    # and retain real 128 KiB WRAM. Three spaced checkpoints provide actual
    # P1/P2 world-position evidence without changing camera or physics.
    issued = 0
    checkpoints = set()
    for index, (mask, frames) in enumerate(ROUTES[route]):
        if frames < 1 or not re.fullmatch(r"(?:p2:)?[a-z]+(?:\+(?:p2:)?[a-z]+)*", mask):
            raise ValueError("Invalid controller command")
        script += f"press {mask} {frames}\n"
        issued += frames + 1  # scene-script hold includes one idle release
        if index == 0:
            script += "dump cinematic-lead\n"
            checkpoints.add("lead")
        if issued >= 500 and "middle" not in checkpoints:
            script += "dump cinematic-middle\n"
            checkpoints.add("middle")
        if issued >= 1000 and "late" not in checkpoints:
            script += "dump cinematic-late\n"
            checkpoints.add("late")
    if checkpoints != {"lead", "middle", "late"}:
        raise ValueError("Route did not span all source-world position checkpoints")
    script += "dump cinematic-end\nquit\n"
    count = sum(frames for _, frames in ROUTES[route])
    if count < 1150:
        raise ValueError("Insufficient post-GO runtime for 900-frame capture")
    metadata = {
        "route": route,
        "source_sha256": sha(source.encode()),
        "route_sha256": sha(script.encode()),
        "source_pre_go_prefix_sha256": sha((before + PREFIX).encode()),
        "unchanged_menu_and_go": True,
        "post_go_turbo_off": True,
        "post_go_scripted_frames": count,
        "capture_requested": {"start_guest_frame": None, "frames_after_observed_go": 111, "minimum_guest_start": 1990, "frame_count": 900},
        "controller_commands": [
            {"mask": mask, "duration": duration} for mask, duration in ROUTES[route]
        ],
        "controls_are_attempts_not_visual_or_landing_proof": True,
        "read_only_guest_position_dumps": ["cinematic-lead", "cinematic-middle", "cinematic-late"],
        "rendering_geometry_and_guest_unchanged": True,
    }
    return script, metadata


def self_test() -> None:
    source = "turbo on\n" + PREFIX + EXPECTED_TAIL + "\n"
    for route in ROUTES:
        rendered, data = produce(source, route)
        assert rendered.startswith("turbo on\n" + PREFIX)
        assert rendered.count("turbo off\n") == 1
        assert data["post_go_scripted_frames"] >= 1150
        assert data["unchanged_menu_and_go"]
        assert rendered.endswith("dump cinematic-end\nquit\n")
        assert all(rendered.count("dump cinematic-" + tag + "\n") == 1 for tag in ("lead", "middle", "late"))
        assert rendered != source
        assert "right+b" in rendered or "p2:b" in rendered
    for changed in (source.replace("until 0E1F != 00", "wait 9"),
                    source.replace("turbo on", "turbo off"),
                    source.replace("press right+p2:right 60", "press right 60")):
        try:
            produce(changed, "p1-leads")
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid source accepted")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    self_test()
    if args.self_test:
        print("DYNAMIC_2P_SCRIPT_SELF_TEST PASS")
        return
    if not args.source or not args.output:
        ap.error("Source and output paths required")
    content = args.source.read_text(encoding="utf-8")
    args.output.mkdir(parents=True, exist_ok=True)
    ledger = {}
    for route in ROUTES:
        script, data = produce(content, route)
        out = args.output / f"{route}.txt"
        out.write_text(script)
        ledger[route] = data
    (args.output / "controller-provenance.json").write_text(json.dumps(
        {"schema": "UR-DYNAMIC-2P-CONTROLLER-PROPOSALS/1",
         "routes": ledger,
         "claim": "Controller inputs specified; no jump or successful trick inferred."},
        indent=2, sort_keys=True) + "\n")
    print(json.dumps(ledger, indent=2))

if __name__ == "__main__":
    main()
