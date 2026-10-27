#!/usr/bin/env python3
"""Observe real original idle attract beneath native Modern title, without guest writes.

Diagnostic only: this never claims that the modern host displays the original
attract or can safely wake from it. The original guest supplies every marker.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

EXPECTED_USA_ROM = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"

MARKER = re.compile(
    r"^UR_MODERN_TITLE_ORIGINAL_SOURCE "
    r"phase=(main_menu|attract_title|demo_race) "
    r"frame=(\d+) menu=([0-9a-f]{2}) race=([0-9a-f]{2}) "
    r"overlay_title=([01])$", re.MULTILINE
)
EXPECTED = ("main_menu", "attract_title", "demo_race")


def persist_exact_native_log(path: Path, log: str) -> str:
    """Receipt hashes actual retained ZIP bytes, even on Windows.

    Path.write_text() converts LF to CRLF on native Windows by default;
    previously that made the receipt describe a different byte stream
    from the uploaded artifact. Explicit UTF-8 bytes forbid translation.
    """
    raw = log.encode("utf-8")
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def verify_original_source_attract(log: str) -> list[dict[str, int | str]]:
    if "UR_BALDOSA_MODERN_ROOT opened=1" not in log:
        raise ValueError("no real Modern native host opening in guest log")
    markers = [
        {"phase": m[1], "frame": int(m[2]), "menu": m[3],
         "race": m[4], "overlay_title": int(m[5])}
        for m in MARKER.finditer(log)
    ]
    if tuple(m["phase"] for m in markers) != EXPECTED:
        raise ValueError("missing, duplicated or reordered authentic guest states")
    a, b, c = markers
    if (a["menu"] != "d7" or b["menu"] != "84" or c["race"] != "01"
            or any(m["overlay_title"] != 1 for m in markers)):
        raise ValueError("wrong original source state or Modern title not covering guest")
    if not (a["frame"] > 0 and a["frame"] < b["frame"] < c["frame"] <= 1800):
        raise ValueError("invalid actual original guest event chronology")
    # Independent Snes9x+Beetle source reference first displays demo
    # at 1531. This post-frame Windows WRAM observer first sees 0313=01
    # at 1532. Preserve BOTH exact facts; do not conflate raster entry
    # and after-frame state observation to mask a wider divergence.
    # MAIN->TITLE remains precisely 503 frames in both observations.
    # Fail closed if the native guest takes a different route. No timer in
    # production may be derived from this diagnostic alone.
    if b["frame"] - a["frame"] != 503:
        raise ValueError("native original main-to-title frame interval differs")
    if c["frame"] - b["frame"] != 589:
        raise ValueError("native original title-to-demo frame interval differs")
    if not (a["frame"] == 440 and b["frame"] == 943 and c["frame"] == 1532):
        raise ValueError("native original guest first-cycle timestamps differ")
    return markers


# The source did not change; only the host briefly revealed original
# 256px game pixels, and consumed a P1 wake before accepting a later A.
def verify_source_driven_preview(log: str, wake_route: str = "p1") -> list[dict[str, int | str]]:
    if "UR_BALDOSA_MODERN_ROOT opened=1" not in log:
        raise ValueError("preview missing real native game")
    markers = [
        {"phase": m[1], "frame": int(m[2]), "menu": m[3],
         "race": m[4], "overlay_title": int(m[5])}
        for m in MARKER.finditer(log)
    ]
    if (tuple(m["phase"] for m in markers) != EXPECTED or
            [m["frame"] for m in markers] != [440, 943, 1532] or
            [m["overlay_title"] for m in markers] != [1, 1, 0] or
            markers[0]["menu"] != "d7" or markers[1]["menu"] != "84" or
            markers[2]["race"] != "01"):
        raise ValueError("preview source guest lifecycle mismatch")
    if wake_route not in ("p1", "keyboard", "p2"):
        raise ValueError("unsupported original demo wake input route")
    wake = {
        "p1": "UR_MODERN_TITLE_STOCK_ATTRACT p1_wake_consumed=1 frame=1600 race=01",
        "keyboard": "UR_MODERN_TITLE_STOCK_ATTRACT keyboard_wake_consumed=1 frame=1600",
        "p2": "UR_MODERN_TITLE_STOCK_ATTRACT p2_wake_consumed=1 frame=1600",
    }[wake_route]
    confirm = {
        "p1": "UR_MODERN_TITLE_STOCK_ATTRACT separate_confirm=1 frame=1660",
        "keyboard": "UR_MODERN_TITLE_STOCK_ATTRACT separate_keyboard_confirm=1 frame=1660",
        "p2": "UR_MODERN_TITLE_STOCK_ATTRACT p2_then_p1_confirm=1 frame=1660",
    }[wake_route]
    required = (
        "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=main_menu frame=440",
        "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=attract_title frame=943",
        "UR_MODERN_TITLE_STOCK_ATTRACT source_revealed=1 frame=943 menu=84 focus=host guest_writes=0",
        "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=demo_race frame=1532",
        "UR_MODERN_TITLE_STOCK_ATTRACT restored_title=1 frame=1600 guest_writes=0",
        wake,
        *((("UR_MODERN_TITLE_STOCK_ATTRACT p2_wake_release_consumed=1 frame=1602",)
           if wake_route == "p2" else ())),
        *((("UR_MODERN_TITLE_STOCK_ATTRACT stable_title=1 frame=1640 root_unselected=1",)
           if wake_route == "p1" else ())),
        confirm,
        "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=1674 input_owned=1",
        "UR_MODERN_TITLE_STOCK_ATTRACT reached_root=1 frame=1690 no_stock_route=1",
    )
    before = -1
    for line in required:
        if log.count(line) != 1 or log.find(line, before + 1) < 0:
            raise ValueError("missing/duplicate/out-of-order original attract wake: " + line)
        before = log.find(line, before + 1)
    return markers


def verify_source_driven_recovery(log: str) -> list[dict[str, int | str]]:
    """Real guest demo must finish before *new* gameplay selection is admitted.

    No host timer, spoofed stock menu, profile activation or injected input.
    This deliberately does not claim the anonymous first-run Play journey.
    """
    required = (
        "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=main_menu frame=440",
        "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=attract_title frame=943",
        "UR_MODERN_TITLE_STOCK_ATTRACT source_revealed=1 frame=943 menu=84",
        "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=demo_race frame=1532",
        "UR_MODERN_TITLE_STOCK_ATTRACT restored_title=1 frame=1600",
        "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=1674",
        "UR_MODERN_TITLE_STOCK_ATTRACT play_deferred=1 frame=1710",
        "UR_MODERN_TITLE_STOCK_ATTRACT native_play_denied=1 frame=1710 profile_stale=0",
        "UR_MODERN_TITLE_STOCK_ATTRACT play_deferred=1 frame=3770",
        "UR_MODERN_TITLE_STOCK_ATTRACT native_play_denied_settling=1 frame=3770 menu=d7 guest_writes=0",
    )
    previous = -1
    for witness in required:
        if log.count(witness) != 1:
            raise ValueError("missing/duplicated real stock recovery witness: " + witness)
        pos = log.find(witness, previous + 1)
        if pos < 0:
            raise ValueError("out-of-order real stock recovery witness: " + witness)
        previous = pos
    marker = re.compile(
        r"UR_MODERN_TITLE_STOCK_ATTRACT source_main_recovered=1 "
        r"frame=(\d+) menu=d7 race=([0-9a-f]{2}) stable=(\d+) guest_writes=0"
    )
    observations = list(marker.finditer(log))
    if len(observations) != 1:
        raise ValueError("missing/duplicated native original MAIN recovery")
    recovery = observations[0]
    frame = int(recovery[1])
    if recovery.start() <= previous or not 3810 <= frame <= 3840:
        raise ValueError("real source MAIN recovery time/ordering mismatch")
    if recovery[2] == "01" or int(recovery[3]) != 60:
        raise ValueError("cannot rearm Play without 60 clean stock MAIN observations")
    marker = "UR_MODERN_TITLE_STOCK_ATTRACT play_rearmed=1 frame=3900 source_main=d7 stable=60 guest_writes=0"
    if log.count(marker) != 1 or log.find(marker, recovery.end()) < 0:
        raise ValueError("no new source-admitted gameplay after stock MAIN")
    if ("UR_BALDOSA_MODERN_ROOT active_profile_stale=1" in log or
            "UR_BALDOSA_MODERN_ROOT stock_requested players=" in log):
        raise ValueError("stock source guard incorrectly mutated route/profile state")
    return [
        {"phase": "denied_while_demo", "frame": 1710},
        {"phase": "denied_during_stock_menu_settling", "frame": 3770},
        {"phase": "native_main_recovered", "frame": frame},
        {"phase": "source_admission_rearmed", "frame": 3900},
    ]


def verify_named_original_play_after_recovery(log: str) -> list[dict[str, int | str]]:
    """Require a REAL named P1/source-menu handoff after native demo wake.

    This is not a fabricated menu/race: native stock router must publish
    existing stock_requested and stock_entered markers after 60 settled D7.
    """
    required = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=",
        # Named-profile cold boot has a source-observed -3-frame startup
        # offset (Windows exact-head runs 40092886488 and 40097172085):
        # 437/940/1529, source reveal 940 and stable MAIN recovery 3815.
        # Host-script action frames 1600/1674/1710/3770/3900 do not shift.
        # Preserve the exact source chronology, D7/84/01 state and title
        # overlay; anonymous 440/943/1532 checks remain independent.
        "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=main_menu frame=437 menu=d7 race=00 overlay_title=1",
        "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=attract_title frame=940 menu=84 race=00 overlay_title=1",
        "UR_MODERN_TITLE_STOCK_ATTRACT source_revealed=1 frame=940",
        "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=demo_race frame=1529 menu=00 race=01 overlay_title=0",
        "UR_MODERN_TITLE_STOCK_ATTRACT restored_title=1 frame=1600",
        "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=1674",
        "UR_MODERN_TITLE_STOCK_ATTRACT named_play_denied=1 frame=1710 source_admitted=0",
        "UR_MODERN_TITLE_STOCK_ATTRACT named_play_denied=1 frame=3770 source_admitted=0",
        "UR_MODERN_TITLE_STOCK_ATTRACT source_main_recovered=1 frame=3815 menu=d7 race=00 stable=60",
        # The native root logs stock_requested synchronously inside its
        # admission call; the title logs named_play_requested after that
        # call returns. Both must follow recovered MAIN, and stock_entered
        # must follow both. This order is observed in Windows run 40101417391.
        "UR_BALDOSA_MODERN_ROOT stock_requested players=1",
        "UR_MODERN_TITLE_STOCK_ATTRACT named_play_requested=1 frame=3900 source_main=d7 source_stable=60",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c",
    )
    last = -1
    for marker in required:
        count = log.count(marker)
        if count != 1:
            # The named-profile process may have a different original source
            # timeline. Preserve the actual stage observations before deciding
            # whether this is a timing expectation or a gameplay regression.
            observed_source_phases = re.findall(
                r"^UR_MODERN_TITLE_ORIGINAL_SOURCE[^\r\n]*", log, re.MULTILINE)
            raise ValueError(
                f"missing or duplicate named original-game proof: {marker}; "
                f"matches={count}; observed_source_phases={observed_source_phases[:12]!r}; "
                "inspect retained native-attract.log")
        current = log.find(marker, last + 1)
        if current < 0:
            raise ValueError("named stock input entered before real MAIN recovery: " + marker)
        last = current
    if ("UR_BALDOSA_MODERN_ROOT active_profile_stale=1" in log or
            "UR_BALDOSA_MODERN_ROOT stock_aborted" in log):
        raise ValueError("named original route not safely source-admitted")
    return [
        {"phase": "named_play_denied_while_demo", "frame": 1710},
        {"phase": "named_play_denied_while_menu_unsettled", "frame": 3770},
        {"phase": "original_main_stable", "frame": 3815},
        {"phase": "original_stock_one_player_entered", "frame": 3900},
    ]


def verify_original_guest_presentations(presented: Path, modern_width: int = 342) -> list[dict]:
    """Actual after-host P6, not final SDL/window, across the source handoff."""
    frame_path = presented / "presents.csv"
    if not frame_path.is_file():
        raise ValueError("missing native presented original stock screenshots")
    with frame_path.open(newline="", encoding="utf-8") as fd:
        rows = list(csv.DictReader(fd))
    if not 30 <= len(rows) <= 140:
        raise ValueError("unexpected stock preview native presentation count")
    photos = {}
    for i, row in enumerate(rows):
        if int(row["present"]) != i:
            raise ValueError("original stock presentation ordinal drift")
        frame = int(row["frame"])
        raw = (presented / f"present_{i:06d}.ppm").read_bytes()
        m = re.match(rb"\AP6\n(\d+) (\d+)\n255\n", raw)
        if not m:
            raise ValueError("missing real native P6 image")
        width, height = map(int, m.groups())
        if (height != 224 or width not in (256, 342) or
                len(raw) - m.end() != width * height * 3):
            raise ValueError("wrong stock/Modern presented image geometry")
        photos[frame] = (width, raw)
    if modern_width not in (256, 342):
        raise ValueError("invalid native Modern title logical width")
    expected = ((1568, 256), (1584, 256),
                (1616, modern_width), (1696, modern_width))
    for frame, width in expected:
        if frame not in photos or photos[frame][0] != width:
            raise ValueError(f"missing actual guest/host viewport witness at {frame}")
    if photos[1568][1] == photos[1584][1]:
        raise ValueError("original two-player demo image did not advance")
    retained = []
    for stage, frame in (("original-demo-before", 1568),
                         ("original-demo", 1584),
                         ("restored-title", 1616),
                         ("root", 1696)):
        width, raw = photos[frame]
        output = presented / f"native-{stage}.ppm"
        output.write_bytes(raw)
        retained.append({
            "stage": stage, "guest_frame": frame, "width": width,
            "height": 224, "sha256": hashlib.sha256(raw).hexdigest(),
            "file": output.name,
        })
    return retained


def set_attract_override(env: dict[str, str], *, preview_wake: bool,
                         default_attract: bool) -> None:
    """Remove ambient preview opt-in; only old opt-in probes restore it.

    The new default-mode witness must show authentic guest attract on a
    real native PE even with the old preview environment variable ABSENT.
    """
    env.pop("UR_MODERN_TITLE_STOCK_ATTRACT_PREVIEW", None)
    if preview_wake and not default_attract:
        env["UR_MODERN_TITLE_STOCK_ATTRACT_PREVIEW"] = "1"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--rom", type=Path, required=True)
    p.add_argument("--script", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--timeout", type=int, default=120)
    p.add_argument("--wake-route", choices=("p1", "keyboard", "p2"),
                   default="p1", help="native physical wake input route")
    p.add_argument("--aspect", choices=("wide", "4:3"), default="wide",
                   help="actual SDL drawable shape used to choose logical 342/256")
    p.add_argument("--preview-wake", action="store_true",
                   help="execute native source title/demo and consumed wake probes")
    p.add_argument("--default-attract", action="store_true",
                   help="prove source attract with old opt-in environment absent")
    p.add_argument("--named-play", action="store_true",
                   help="mint native first profile in separate prior process, then prove real stock 1P")
    p.add_argument("--bootstrap-script", type=Path,
                   help="genuine native P1 X/A profile creation route for named-play")
    p.add_argument("--recovery", action="store_true",
                   help="exercise source-admitted Play gating through genuine MAIN return")
    args = p.parse_args()
    if args.default_attract and not args.preview_wake:
        p.error("--default-attract requires --preview-wake")
    if args.recovery and not args.preview_wake:
        p.error("--recovery requires --preview-wake")
    if args.recovery and args.wake_route != "p1":
        p.error("--recovery requires P1 wake route")
    if args.named_play and (not args.preview_wake or not args.recovery or
                            args.wake_route != "p1" or not args.bootstrap_script):
        p.error("--named-play requires P1 --preview-wake --recovery --bootstrap-script")
    if os.name != "nt":
        p.error("native original-guest attract requires real Windows AOT")
    if not 30 <= args.timeout <= 150:
        p.error("timeout must be 30..150 seconds")
    exe, rom, script = (path.resolve(strict=True) for path in
                        (args.exe, args.rom, args.script))
    if hashlib.sha256(rom.read_bytes()).hexdigest() != EXPECTED_USA_ROM:
        raise ValueError("unexpected original USA ROM SHA256")
    binary = exe.read_bytes()
    if not binary.startswith(b"MZ"):
        raise ValueError("no genuine native Windows executable")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    user = out / "player"
    user.mkdir()
    cfg = out / "config.ini"
    cfg.write_text("[Sound]\nEnableAudio = 0\n" +
                   ("[Graphics]\nWindowSize = 960x720\n"
                    if args.aspect == "4:3" else ""), encoding="utf-8")
    env = dict(os.environ)
    env.pop("UR_BALDOSA_MODERN_ROOT_KEY_SMOKE", None)
    set_attract_override(env, preview_wake=args.preview_wake,
                         default_attract=args.default_attract)
    if args.preview_wake:
        env["UR_BALDOSA_MODERN_ROOT_KEY_SMOKE"] = (
            "23" if args.named_play else
            "20" if args.recovery else
            "21" if args.wake_route == "keyboard" else
            "22" if args.wake_route == "p2" else "28")
        presented = out / "presented"
        presented.mkdir()
    env.update({
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "SNESRECOMP_USER_DATA_DIR": str(user),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_ROOT": "1",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "0",
        "UR_BALDOSA_MODERN_TITLE_ATTRACT_PROBE": "1",
        "UR_REDUCED_MOTION": "0",
    })
    bootstrap_log_sha256 = None
    if args.named_play:
        # Process A invokes the real P1 X/A first-racer UI and canonical
        # native product writers. Process B reads that exact persisted root.
        bootstrap = args.bootstrap_script.resolve(strict=True)
        if bootstrap == script or bootstrap == rom:
            raise ValueError("named-profile bootstrap must be separate original input route")
        boot_dir = out / "named-p1-bootstrapped"
        boot_dir.mkdir()
        boot_env = dict(env)
        boot_env["UR_BALDOSA_MODERN_ROOT_KEY_SMOKE"] = "8"
        boot_env["UR_BALDOSA_MODERN_PROFILE_SELECT"] = "1"
        boot_env["UR_BALDOSA_MODERN_INPUT"] = "1"
        boot_env.pop("UR_MODERN_TITLE_STOCK_ATTRACT_PREVIEW", None)
        boot_env.pop("UR_BALDOSA_MODERN_TITLE_ATTRACT_PROBE", None)
        boot_cmd = [str(exe), "--no-launcher", "--config", str(cfg),
                    "--script", str(bootstrap), str(rom)]
        try:
            boot_result = subprocess.run(
                boot_cmd, cwd=boot_dir, env=boot_env, timeout=args.timeout,
                capture_output=True, text=True, errors="replace")
        except subprocess.TimeoutExpired as exc:
            (out / "native-profile-bootstrap-timeout.txt").write_text(str(exc))
            raise
        boot_log = boot_result.stdout + "\n" + boot_result.stderr
        bootstrap_log_sha256 = persist_exact_native_log(
            out / "native-profile-bootstrap.log", boot_log)
        if (boot_result.returncode or
                boot_log.count("UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process") != 1 or
                not (user / "profiles-v1.txt").is_file()):
            raise ValueError(
                "genuine P1 X/A native profile creation did not persist; "
                f"exit={boot_result.returncode}, "
                f"created={boot_log.count('UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process')}, "
                f"catalog={(user / 'profiles-v1.txt').is_file()}; "
                "inspect retained native-profile-bootstrap.log")
        env["UR_BALDOSA_MODERN_PROFILE_SELECT"] = "1"
        env["UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS"] = "1"
    if args.preview_wake:
        env.update({
            "SNESRECOMP_SCREENSHOT_DIR": str(presented),
            "SNESRECOMP_SCREENSHOT_FROM": "0",
            "SNESRECOMP_SCREENSHOT_TO": "1800",
            "SNESRECOMP_FRAMEDUMP_PIXELS": "0",
        })
    cmd = [str(exe), "--no-launcher", "--config", str(cfg),
           "--script", str(script)]
    if args.preview_wake:
        # Keep the native screenshot path on the identical known working
        # framedump invocation as ordinary title proof. Pixel dumps per
        # frame are disabled; only requested native P6 presents are kept.
        dump = out / "framedump"
        dump.mkdir()
        cmd.extend(("--framedump", str(dump)))
    cmd.append(str(rom))
    try:
        run = subprocess.run(
            cmd, cwd=out, env=env, timeout=args.timeout,
            capture_output=True, text=True, errors="replace")
    except subprocess.TimeoutExpired as exc:
        (out / "native-attract-timeout.txt").write_text(str(exc))
        raise
    log = run.stdout + "\n" + run.stderr
    retained_log_sha256 = persist_exact_native_log(out / "native-attract.log", log)
    if run.returncode:
        raise ValueError(f"real Windows native attract process exited {run.returncode}")
    observed = (
        verify_named_original_play_after_recovery(log) if args.named_play
        else verify_source_driven_recovery(log) if args.recovery
        else verify_source_driven_preview(log, wake_route=args.wake_route) if args.preview_wake
        else verify_original_source_attract(log))
    presented_receipt = (
        verify_original_guest_presentations(
            presented, modern_width=256 if args.aspect == "4:3" else 342)
        if args.preview_wake else [])
    receipt = {
        "schema_version": 1,
        "candidate_executable_sha256": hashlib.sha256(binary).hexdigest(),
        "pinned_original_usa_rom_sha256": EXPECTED_USA_ROM,
        "actual_guest_source_markers": observed,
        "log_sha256": retained_log_sha256,
        "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "genuine_native_profile_bootstrap_sha256": bootstrap_log_sha256,
        "named_source_play_verified": args.named_play,
        "diagnostic_guest_writes": False,
        "human_button_actions": 2 if args.preview_wake else 0,
        "scripted_host_preview_only": args.preview_wake,
        "historical_preview_environment_override_used": args.preview_wake and not args.default_attract,
        "default_stock_attract_without_preview_override": args.default_attract,
        "native_wake_route": args.wake_route if args.preview_wake else None,
        "drawable_aspect": args.aspect,
        "native_stock_demo_and_wake_presentations": presented_receipt,
        "native_stock_demo_index_sha256": (
            hashlib.sha256((presented / "presents.csv").read_bytes()).hexdigest()
            if args.preview_wake else None),
        "original_visual_demo_first_frame_reference": 1531,
        "native_post_frame_race_flag_first_observed": 1532,
        "modern_host_title_remained_visible": not args.preview_wake,
        "original_attract_displayed_on_native_P6": args.preview_wake,
        "wake_input_tested": args.preview_wake,
        "real_guest_main_recovery_verified": args.recovery,
        "play_source_admission_guard_tested": args.recovery,
        "final_sdl_capture": False,
        "release_gate_credit": 0,
    }
    (out / "native-attract-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("UR_MODERN_TITLE_GENUINE_ATTRACT_SOURCE=passed")
    if args.preview_wake:
        print("UR_MODERN_TITLE_ORIGINAL_P6_WAKE=passed")
    if args.recovery:
        print("UR_MODERN_TITLE_ORIGINAL_PLAY_RECOVERY=passed")
    if args.named_play:
        print("UR_MODERN_TITLE_REAL_NAMED_P1_AFTER_ATTRACT=passed")
    for m in observed:
        print(f"{m['phase']}={m['frame']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
