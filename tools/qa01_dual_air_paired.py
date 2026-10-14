#!/usr/bin/env python3
"""QA-01 read-only paired original/native replay of one frontier raw-air lead.

Both engines receive the *same* unmodified neutral two-controller stream and
absolute-host dump schedule. The distinct original/native executable identities,
guest phase and provisional source register meanings are never elided.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import qa02_native_2p_seeded_endurance as guest
import qa_adaptive_frontier as frontier
from summarize_paired_player_slots import state

SCHEMA = "ur-qa01-dual-air-paired/1"
SEED = 50036056
ARM = "rotation"
FRAME = 2580
SOURCE_SHA = "dd5632f0a612ee22cc46d9b1ce7a6005a5fa555f"
RUN = 38446393623
NATIVE_FRONTIER_SHA = "28501fa3268f82d83672122cddbd2628ce5b2458e625f46d93766f50befbe515"
STOCK_INPUT_SHA = "28f2842fd262030e434b3aef88eb360f74de94fbf558f0eb0ba8edce645fb490"
STOCK_SCRIPT_SHA = "ebac1a3505281e9793c8197006081c5d88f6ab3383df48f23ba2475159e9e6e3"
ROM_SHA = guest.ROM_SHA
BASE = guest.BASE_CHECK
NEIGHBORS = (FRAME - 1, FRAME, FRAME + 1)


def paired_script(source: str) -> str:
    """Add just two no-input, read-only dumps around the observed frontier hit.

    Host-frame deltas are explicit; no engine is advanced, delayed or rebased
    relative to its own original 2P input stream.
    """
    rendered = guest.render_script(source)
    anchor = "wait 120\ndump endurance-2580\nwait 120\ndump endurance-2700\n"
    replace = ("wait 119\ndump qa01-neighbor-2579\n"
               "wait 1\ndump endurance-2580\n"
               "wait 1\ndump qa01-neighbor-2581\n"
               "wait 119\ndump endurance-2700\n")
    if rendered.count(anchor) != 1:
        raise ValueError("unrecognized canonical frontier event checkpoint spacing")
    return rendered.replace(anchor, replace, 1)


def checkpoints() -> list[str]:
    names = [BASE]
    for frame in guest.FRAMES:
        if frame == FRAME:
            names.extend(("qa01-neighbor-2579", f"endurance-{FRAME}",
                          "qa01-neighbor-2581"))
        else:
            names.append(f"endurance-{frame}")
    return names


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def regular(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing or symlinked source evidence: {path}")


def prepare(out: Path) -> dict:
    if out.exists():
        raise ValueError("refuse to overwrite prior independent paired evidence")
    prefix, source_script = guest.base_source()
    if digest(prefix) != STOCK_INPUT_SHA or digest(source_script) != STOCK_SCRIPT_SHA:
        raise ValueError("historical 2P stock fixture drift: source route no longer pinned")
    actions, info = frontier.actions_for(SEED, ARM)
    if actions[0] != (1650, 60, 0x080, 0x040):
        raise ValueError("frontier changed the two-seat first intervention")
    control = guest.render_input(prefix, actions, None)
    script = paired_script(source_script)
    if f"dump endurance-{FRAME}" not in script:
        raise ValueError("source sampling script omitted decisive frame")
    out.mkdir(parents=True)
    (out / "case.input").write_text(control, encoding="utf-8")
    (out / "case.script").write_text(script, encoding="utf-8")
    # Reject generated input that the actual engine-neutral loader cannot read.
    from controller_input import load_controller_runs
    load_controller_runs(out / "case.input")
    manifest = {
        "schema": SCHEMA, "source_sha": SOURCE_SHA,
        "frontier_run": RUN, "seed": SEED, "arm": ARM, "shard": 2,
        "first_source_observed_both_air_frame": FRAME,
        "raw_air_addresses": {"p1": "7E:0545", "p2": "7E:0547"},
        "original_rom_sha256": ROM_SHA,
        "frontier_native_executable_sha256": NATIVE_FRONTIER_SHA,
        "input_sha256": digest(control), "script_sha256": digest(script),
        "stock_input_sha256": STOCK_INPUT_SHA,
        "stock_script_sha256": STOCK_SCRIPT_SHA,
        "checkpoints": checkpoints(),
        "post_entry_control_intervals": info["intervals"],
        "release_gate_credit": 0, "exact_original_native_acceptance": False,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return manifest


def frame_receipts(log_path: Path, tags: list[str], *, side: str) -> dict:
    """Attest that this engine itself reported each dump at its expected host tick.

    A correctly named WRAM file is not proof of the frame in which it was
    captured. Keep the original/native axes separate; do not infer guest
    entry-phase equality from absolute host ticks.
    """
    regular(log_path)
    if side not in ("original", "native"):
        raise ValueError("unknown original/native runtime transcript")
    log = log_path.read_text(encoding="utf-8", errors="replace")
    if len(log) > 2_000_000:
        raise ValueError("unbounded emulator frame receipt transcript")
    expected = []
    for tag in tags:
        if tag == BASE:
            frame = 1620
        elif tag.startswith("endurance-"):
            frame = int(tag.removeprefix("endurance-"))
        elif tag in ("qa01-neighbor-2579", "qa01-neighbor-2581"):
            frame = int(tag.removeprefix("qa01-neighbor-"))
        else:
            raise ValueError("unexpected frame label in pinned replay manifest")
        expected.append((frame, tag))
    matches = [(int(frame), label) for frame, label in re.findall(
        r"script f=(\\d+) dump ([A-Za-z0-9-]+) ok\\b", log)]
    selected = [row for row in matches if row[1] in tags]
    if selected != expected:
        raise ValueError(
            f"{side} real guest dump frame receipts missing, duplicated, reordered or mistimed; "
            f"expected {expected}, observed {selected[:len(expected) + 3]}")
    return {"emulator": side, "observed_frame_label_pairs": selected,
            "transcript_sha256": sha(log_path),
            "frame_labels_from_actual_guest_transcript": True}


def checked_states(folder: Path, tags: list[str]) -> tuple[dict, dict]:
    samples, hashes = {}, {}
    for tag in tags:
        p = folder / (tag + ".wram.bin")
        regular(p)
        if p.stat().st_size != 131072:
            raise ValueError(f"{tag}: not a genuine 128-KiB WRAM snapshot")
        samples[tag] = state(p)
        hashes[tag] = sha(p)
    return samples, hashes


def summarize(manifest_path: Path, original_dir: Path, native_dir: Path,
              rom: Path, core: Path, native_exe: Path,
              original_log: Path, native_log: Path) -> dict:
    regular(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise ValueError("not the pinned dual-air evidence manifest")
    parent = manifest_path.parent
    for name, key in (("case.input", "input_sha256"),
                      ("case.script", "script_sha256")):
        p = parent / name
        regular(p)
        if sha(p) != manifest.get(key):
            raise ValueError(f"mutated paired {name}")
    source_input, source_script = guest.base_source()
    actions, _ = frontier.actions_for(SEED, ARM)
    if (manifest.get("input_sha256") != digest(
            guest.render_input(source_input, actions, None))
            or manifest.get("script_sha256") != digest(
                paired_script(source_script))):
        raise ValueError("source-independent regenerated paired input does not match manifest")
    if (manifest.get("stock_input_sha256") != STOCK_INPUT_SHA
            or manifest.get("stock_script_sha256") != STOCK_SCRIPT_SHA
            or manifest.get("raw_air_addresses") !=
               {"p1": "7E:0545", "p2": "7E:0547"}
            or manifest.get("original_rom_sha256") != ROM_SHA
            or manifest.get("frontier_native_executable_sha256") != NATIVE_FRONTIER_SHA
            or manifest.get("first_source_observed_both_air_frame") != FRAME):
        raise ValueError("original source register/fixture provenance changed")
    if (manifest.get("seed"), manifest.get("arm"),
            manifest.get("source_sha"), manifest.get("frontier_run"),
            manifest.get("release_gate_credit"),
            manifest.get("exact_original_native_acceptance")) != (
            SEED, ARM, SOURCE_SHA, RUN, 0, False):
        raise ValueError("paired frontier witness identity changed")
    if manifest.get("checkpoints") != checkpoints():
        raise ValueError("incomplete or reordered original/native frame schedule")
    for p in (rom, core, native_exe):
        regular(p)
    if sha(rom) != ROM_SHA:
        raise ValueError("original-USA ROM identity changed")
    receipts = {
        "original": frame_receipts(original_log, manifest["checkpoints"], side="original"),
        "native": frame_receipts(native_log, manifest["checkpoints"], side="native"),
    }
    original, orig_hash = checked_states(original_dir, manifest["checkpoints"])
    native, native_hash = checked_states(native_dir, manifest["checkpoints"])
    if (original[BASE]["camera_and_viewport"]["mode"]["split_screen_active_raw"] == 0
            or native[BASE]["camera_and_viewport"]["mode"]["split_screen_active_raw"] == 0):
        raise ValueError("paired 2P source fixture failed to enable second camera")
    # Prior to injected controls both sources must be in real active racing.
    if any((folder / (BASE + ".wram.bin")).read_bytes()[0x0313] != 1
           for folder in (original_dir, native_dir)):
        raise ValueError("paired source guests did not reach active racing")
    source = f"endurance-{FRAME}"
    out_rows = []
    for tag in manifest["checkpoints"]:
        o, n = original[tag], native[tag]
        o_page = (original_dir / (tag + ".wram.bin")).read_bytes()
        n_page = (native_dir / (tag + ".wram.bin")).read_bytes()
        out_rows.append({
            "original_active_race_raw": o_page[0x0313],
            "native_active_race_raw": n_page[0x0313],
            "original_menu_raw": o_page[0x009F],
            "native_menu_raw": n_page[0x009F],
            "original_course_raw": o_page[0x00CE],
            "native_course_raw": n_page[0x00CE],
            "host_frame_label": tag,
            "original_wram_sha256": orig_hash[tag],
            "native_wram_sha256": native_hash[tag],
            "full_wram_equal_same_host": orig_hash[tag] == native_hash[tag],
            "original_air_raw": [o["slot1"]["air_effective"], o["slot2"]["air"]],
            "native_air_raw": [n["slot1"]["air_effective"], n["slot2"]["air"]],
            "original_xy": [[o[x]["x_pos"], o[x]["y_pos"]] for x in ("slot1", "slot2")],
            "native_xy": [[n[x]["x_pos"], n[x]["y_pos"]] for x in ("slot1", "slot2")],
            "original_velocity": [[o[x]["x_speed"], o[x]["y_speed"]] for x in ("slot1", "slot2")],
            "native_velocity": [[n[x]["x_speed"], n[x]["y_speed"]] for x in ("slot1", "slot2")],
            "original_progress": o["race_progress"],
            "native_progress": n["race_progress"],
        })
    witness = next(x for x in out_rows if x["host_frame_label"] == source)
    orig_air = all(witness["original_air_raw"])
    native_air = all(witness["native_air_raw"])
    native_sha = sha(native_exe)
    window = []
    for frame in NEIGHBORS:
        tag = (f"endurance-{FRAME}" if frame == FRAME
               else f"qa01-neighbor-{frame}")
        row = next(x for x in out_rows if x["host_frame_label"] == tag)
        window.append({
            "host_frame": frame,
            "original_both_air_raw": all(row["original_air_raw"]),
            "native_both_air_raw": all(row["native_air_raw"]),
            "same_host_full_wram_equal": row["full_wram_equal_same_host"],
            "original_in_active_race": row["original_active_race_raw"] == 1,
            "native_in_active_race": row["native_active_race_raw"] == 1,
        })
    return {
        "schema": SCHEMA, "disposition": "source_observation_only_not_event_acceptance",
        "manifest": manifest,
        "reference_core_sha256": sha(core),
        "measured_native_executable_sha256": native_sha,
        "same_executable_as_frontier_witness": native_sha == NATIVE_FRONTIER_SHA,
        "original_rom_sha256": ROM_SHA,
        "same_neutral_input_and_host_frame_schedule": True,
        "both_engine_actual_dump_frame_receipts_verified": True,
        "independent_emulator_frame_receipts": receipts,
        "paired_guest_relative_entry_offset_calibrated": False,
        "raw_both_air_at_2580": {"original": orig_air, "native": native_air},
        "three_frame_host_phase_window": window,
        "neighbor_frames_are_diagnostic_not_clock_normalization": True,
        "active_race_at_2580": {
            "original": witness["original_active_race_raw"] == 1,
            "native": witness["native_active_race_raw"] == 1,
        },
        "raw_air_interpretation": "provisional source registers; no airborne physics proven",
        "source_frame_labels_are_host_ticks_not_event_relative_clocks": True,
        "original_wram_snapshots": len(orig_hash),
        "native_wram_snapshots": len(native_hash),
        "read_only_paired_samples": out_rows,
        "release_gate_credit": 0, "strict_complete_event_accepted": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--out-dir", required=True, type=Path)
    c = sub.add_parser("classify")
    for x in ("manifest", "original-dir", "native-dir", "rom", "core",
              "native-exe", "original-log", "native-log", "out"):
        c.add_argument("--" + x, required=True, type=Path)
    args = ap.parse_args()
    if args.mode == "prepare":
        result = prepare(args.out_dir)
    else:
        result = summarize(args.manifest, args.original_dir,
                           args.native_dir, args.rom, args.core, args.native_exe,
                           args.original_log, args.native_log)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("schema", "release_gate_credit")},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
