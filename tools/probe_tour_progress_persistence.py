#!/usr/bin/env python3
"""Power-cycle behaviour of rider stats and unfinished tour progress.

Decision served: policy feature ``unfinished-tour-session-loss``. Two things are
followed through a reload:

- rider 0 lifetime PLAYED/WON stats (SRAM 0x0230/0x0232), which persist (an earlier
  reading of 0x0230 as tour progress was wrong, R-2026-10-03-UI-19);
- the per-track tour completion flags at SRAM ``0x1075 + 5*tour_row + track``
  (static decode, Nitrodon bank 83/80 listings): a qualifying 1P result sets the
  track's flag (``83:87F5``), five set flags award the medal and clear the row
  (``83:8805``/``83:881B``), and confirming a rider (``80:BBC1``) zeroes all 50 flags.
  The flags are battery-backed, but every route into 1P tour play goes through
  rider select, so unfinished tour progress does not survive a power cycle.

Method (reference harness only, no guest pokes):

1. replay the historical 2014 Dessyreqt movie input from its anchored SRAM
   through the first in-session Crawler wins, dumping SRAM/WRAM every 250 frames;
2. take the battery SRAM image at the first settled non-race frame after the
   rider 0 PLAYED counter (0x0230) reaches 2 and 3;
3. power each image on in a fresh process with the same movie input and record
   the counter across boot, frontend selection, race entry, and the next win.

The movie only stays meaningful on the modern Snes9x core through its early
segment; the conclusions here use the first race on each reload, whose input and
race-entry route are identical to the baseline run.

``summarize`` is pure and unit-tested; ``main`` drives snesref.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Battery SRAM offsets that advance once per race in the baseline replay:
# 0x0230 rider-0 PLAYED, 0x0232 rider-0 WON (all movie races are wins), 0x10A9 unidentified.
COUNTER_OFFSETS = (0x0230, 0x0232, 0x10A9)
TOUR_FLAGS = 0x1075  # Crawler row: 0x1075..0x1079
TOUR_TRACKS = 5
MEDAL_RANGE = (0x069C, 0x072C)
WRAM_MENU = 0x009F
WRAM_TRACK = 0x00CE
WRAM_IN_RACE = 0x0313
SRAM_SIZE = 0x2000
WRAM_SIZE = 0x20000

BASELINE_LAST_FRAME = 12500
RELOAD_LAST_FRAME = 4000
STEP = 250
FIRST_DUMP = 750
BOOT_DUMP = 300


def sample(sram: bytes, wram: bytes) -> dict:
    return {
        "menu": wram[WRAM_MENU],
        "track": wram[WRAM_TRACK],
        "in_race": wram[WRAM_IN_RACE],
        "counters": [sram[o] for o in COUNTER_OFFSETS],
        "tour_flags": list(sram[TOUR_FLAGS:TOUR_FLAGS + TOUR_TRACKS]),
        "nonzero_medals_rows_0_7": sum(1 for i in range(MEDAL_RANGE[0], MEDAL_RANGE[0] + 0x80) if sram[i]),
    }


def counter_changes(samples: dict[int, dict]) -> list[dict]:
    out, prev = [], None
    for frame in sorted(samples):
        s = samples[frame]
        if prev is None or s["counters"] != prev:
            out.append({"frame": frame, **s})
        prev = s["counters"]
    return out


def snapshot_frame(samples: dict[int, dict], value: int) -> int | None:
    """First settled non-race frame whose primary counter equals ``value``."""
    for frame in sorted(samples):
        s = samples[frame]
        if s["counters"][0] == value and s["in_race"] == 0 and len(set(s["counters"])) == 1:
            return frame
    return None


def summarize(baseline: dict[int, dict], reloads: dict[int, dict]) -> dict:
    """reloads maps snapshot counter value -> {"input_counter", "input_tour_flags", "boot_diff", "samples"}."""
    base_changes = counter_changes(baseline)
    primary = [c["counters"][0] for c in base_changes]
    flag_seq = []
    for frame in sorted(baseline):
        flags = baseline[frame]["tour_flags"]
        if not flag_seq or flags != flag_seq[-1]:
            flag_seq.append(flags)
    fill = [[1] * n + [0] * (TOUR_TRACKS - n) for n in range(len(flag_seq))]
    result = {
        "baseline_counter_sequence": primary,
        "baseline_tour_flag_sequence": flag_seq,
        "baseline_counter_changes": base_changes,
        "reloads": {},
    }
    checks = {
        "baseline_counter_advances_by_one_per_race": primary == list(range(len(primary))) and len(primary) >= 3,
        "reload_boot_preserves_counter": True,
        "reload_counter_survives_frontend_and_race_entry": True,
        "reload_next_race_increments_counter": True,
        "baseline_tour_flags_fill_in_track_order": len(flag_seq) >= 3 and flag_seq == fill,
        "reload_boot_preserves_tour_flags": True,
        "reload_rider_select_clears_tour_flags": True,
    }
    for value, run in sorted(reloads.items()):
        samples = run["samples"]
        frames = sorted(samples)
        boot = samples[frames[0]]["counters"][0]
        race_frames = [f for f in frames if samples[f]["in_race"] == 1]
        entry = samples[race_frames[0]]["counters"][0] if race_frames else None
        after = None
        if race_frames:
            later = [f for f in frames if f > race_frames[0] and samples[f]["in_race"] != 1]
            if later:
                after = samples[later[0]]["counters"][0]
        boot_flags = samples[frames[0]]["tour_flags"]
        entry_flags = samples[race_frames[0]]["tour_flags"] if race_frames else None
        result["reloads"][str(value)] = {
            "input_counter": run["input_counter"],
            "input_tour_flags": run["input_tour_flags"],
            "tour_flags_at_boot": boot_flags,
            "tour_flags_at_first_race": entry_flags,
            "boot_sram_bytes_changed": run["boot_diff"],
            "counter_at_boot": boot,
            "counter_at_first_race": entry,
            "counter_after_first_race": after,
            "counter_changes": counter_changes(samples),
        }
        checks["reload_boot_preserves_counter"] &= boot == run["input_counter"]
        checks["reload_counter_survives_frontend_and_race_entry"] &= entry == run["input_counter"]
        checks["reload_next_race_increments_counter"] &= after == run["input_counter"] + 1
        checks["reload_boot_preserves_tour_flags"] &= any(run["input_tour_flags"]) and boot_flags == run["input_tour_flags"]
        checks["reload_rider_select_clears_tour_flags"] &= entry_flags == [0] * TOUR_TRACKS
    result["checks"] = checks
    result["all_checks_pass"] = all(checks.values()) and bool(reloads)
    return result


def write_script(path: Path, first: int, last: int, prefix: str, boot: bool) -> None:
    lines, frame = [], 0
    if boot:
        lines += [f"wait {BOOT_DUMP}", f"dump {prefix}-{BOOT_DUMP:05d}"]
        frame = BOOT_DUMP
    lines += [f"wait {first - frame}", f"dump {prefix}-{first:05d}"]
    frame = first
    while frame < last:
        lines.append(f"wait {STEP}")
        frame += STEP
        lines.append(f"dump {prefix}-{frame:05d}")
    lines.append("quit")
    path.write_text("\n".join(lines) + "\n")


def run_snesref(args, sram_in: Path, script: Path, dump_dir: Path) -> None:
    dump_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ,
               SNESREF_HEADLESS="1", SNESREF_FAST="1", SNESREF_WRAM_FILL="0",
               SNESREF_SRAM_IN=str(sram_in), SNESREF_INPUT_FILE=str(args.work / "movie.input"),
               SNESREF_SCRIPT=str(script), SNESREF_DUMP_DIR=str(dump_dir))
    with open(dump_dir / "snesref.log", "w") as log:
        subprocess.run([str(args.snesref), str(args.core), str(args.rom)],
                       env=env, cwd=dump_dir, stdout=log, stderr=subprocess.STDOUT, check=True)


def load_samples(dump_dir: Path, prefix: str) -> dict[int, dict]:
    out = {}
    for sram_path in dump_dir.glob(f"{prefix}-*.sram.bin"):
        frame = int(sram_path.name[len(prefix) + 1:len(prefix) + 6])
        sram = sram_path.read_bytes()
        wram = (dump_dir / sram_path.name.replace(".sram.bin", ".wram.bin")).read_bytes()
        if len(sram) != SRAM_SIZE or len(wram) != WRAM_SIZE:
            raise SystemExit(f"unexpected dump size for {sram_path.name}")
        out[frame] = sample(sram, wram)
    return out


def main() -> int:
    tools = ROOT / ".tools/src"
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snesref", type=Path, default=tools / "snesrecomp/build-snesref/snesref")
    ap.add_argument("--core", type=Path, default=tools / "snes9x-libretro/libretro/snes9x_libretro.so")
    ap.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--smv", type=Path, default=ROOT / "reference/imported/tas-bots/dessyreqt-4250-submission.smv")
    ap.add_argument("--work", type=Path, help="scratch directory (default: temporary)")
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/tour-progress-persistence.json")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as td:
        args.work = args.work or Path(td)
        args.work.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, str(ROOT / "tools/extract_smv_input.py"), str(args.smv),
                        "--input-out", str(args.work / "movie.input"),
                        "--sram-out", str(args.work / "anchored.srm"), "--sram-size", str(SRAM_SIZE),
                        "--json-out", str(args.work / "movie.json")],
                       check=True, stdout=subprocess.DEVNULL)

        base_dir = args.work / "baseline"
        write_script(args.work / "baseline.script", FIRST_DUMP, BASELINE_LAST_FRAME, "base", boot=False)
        run_snesref(args, args.work / "anchored.srm", args.work / "baseline.script", base_dir)
        baseline = load_samples(base_dir, "base")

        reloads = {}
        write_script(args.work / "reload.script", FIRST_DUMP, RELOAD_LAST_FRAME, "reload", boot=True)
        for value in (2, 3):
            frame = snapshot_frame(baseline, value)
            if frame is None:
                raise SystemExit(f"baseline never settled with PLAYED counter {value}")
            image = base_dir / f"base-{frame:05d}.sram.bin"
            run_dir = args.work / f"reload-{value}"
            run_snesref(args, image, args.work / "reload.script", run_dir)
            booted = (run_dir / f"reload-{BOOT_DUMP:05d}.sram.bin").read_bytes()
            source = image.read_bytes()
            reloads[value] = {
                "input_counter": source[COUNTER_OFFSETS[0]],
                "input_tour_flags": list(source[TOUR_FLAGS:TOUR_FLAGS + TOUR_TRACKS]),
                "snapshot_frame": frame,
                "boot_diff": [f"0x{i:04x}" for i in range(SRAM_SIZE) if booted[i] != source[i]],
                "samples": load_samples(run_dir, "reload"),
            }

    report = summarize(baseline, reloads)
    for value, run in reloads.items():
        report["reloads"][str(value)]["snapshot_frame"] = run["snapshot_frame"]
    report = {
        "schema_version": 1,
        "question": "Across a power cycle, do rider 0 lifetime stats (SRAM 0x0230/0x0232) persist, and does unfinished tour progress (SRAM 0x1075 per-track flags) survive into the next tour run?",
        "correction": "Originally framed as a tour-progress test on 0x0230, which is the Player Scores PLAYED stat (R-2026-10-03-UI-19). Tour progress is the 0x1075 flag table.",
        "tour_flags": {"layout": "SRAM 0x1075 + 5*tour_row + track, 50 bytes, 1 = track qualified in the current tour run",
                       "set": "83:87F5 on a qualifying 1P result",
                       "award": "83:8805 sums the tour row; 5 -> 83:881B clears the row and increments the medal cell",
                       "cleared": "80:BBC1 zeroes all 50 when a rider is confirmed; 83:8957 clears the row when TRACK_SELECT is left back to TOUR_SELECT unless the medal cell equals SRAM 0x10D1 (unidentified)",
                       "checksum": "not covered by the 0x073C medal checksum (0x05E8-0x073B)"},
        "harness": "snesref + pinned snes9x-libretro, historical Dessyreqt 2014 movie input, anchored SRAM",
        "counter_offsets": [f"0x{o:04x}" for o in COUNTER_OFFSETS],
        **report,
        "limits": [
            "Only won races were observed; whether a lost race changes the counter is untested.",
            "The flags survive in battery SRAM but are zeroed at rider select, so a resumed tour starts empty; the medal award after five qualifying results is statically decoded, not replayed across a reload.",
            "The 0x10D1 comparison on leaving TRACK_SELECT is not decoded.",
            "Counter semantics beyond 'advances once per won tour race and persists' are not promoted.",
        ],
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["checks"], indent=2))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
