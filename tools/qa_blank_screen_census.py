#!/usr/bin/env python3
"""Player-visible blank-screen census: how long each engine shows a black screen.

Screen loads in the frontend run under a blank display. The number of host
frames a load keeps the screen black is directly visible to the player and
needs no WRAM access, so it works on cores that expose no system RAM (the
pinned high-accuracy bsnes-libretro build). For one controller stream this
tool dumps every frame on each engine, measures each framebuffer's peak
brightness, and reports the runs of black frames per engine, paired run by run.

Observation only: it grants no gameplay, original-parity or release credit.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import qa_frontier_original_crosscheck as xc  # noqa: E402

SCHEMA = "ur-blank-screen-census/1"
DARK = 3       # max channel value below which a sampled pixel counts as black
STRIDE = 97    # sample one pixel in 97 (coprime with the 256-pixel row)


def brightness(bgrx: bytes) -> float:
    """Mean of each sampled pixel's brightest channel (BGRX, 4 bytes/pixel)."""
    if len(bgrx) % 4:
        raise ValueError("framebuffer is not 32-bit BGRX")
    total = n = 0
    for i in range(0, len(bgrx) - 3, 4 * STRIDE):
        total += max(bgrx[i], bgrx[i + 1], bgrx[i + 2])
        n += 1
    return total / n if n else 0.0


def dark_runs(frames: list[int], values: list[float]) -> list[list[int]]:
    """Inclusive [first, last] host frames of each consecutive black run."""
    runs, start, prev = [], None, None
    for f, v in zip(frames, values):
        if v < DARK:
            if start is None or f != prev + 1:
                if start is not None:
                    runs.append([start, prev])
                start = f
            prev = f
        elif start is not None:
            runs.append([start, prev])
            start = None
    if start is not None:
        runs.append([start, prev])
    return runs


def pair_runs(reference: list[list[int]], other: list[list[int]]) -> list[dict]:
    """Pair runs by overlap, reporting each one's length difference."""
    rows = []
    for a, b in reference:
        match = next(((c, d) for c, d in other if c <= b and d >= a), None)
        rows.append({"reference": [a, b], "other": list(match) if match else None,
                     "length_delta": None if match is None else (match[1] - match[0]) - (b - a)})
    return rows


def census(frames: list[int], engines: dict[str, list[float]], reference: str) -> dict:
    runs = {name: dark_runs(frames, values) for name, values in engines.items()}
    return {
        "schema": SCHEMA, "first_frame": frames[0], "last_frame": frames[-1],
        "dark_threshold": DARK, "reference": reference,
        "dark_frames": {name: sum(b - a + 1 for a, b in r) for name, r in runs.items()},
        "dark_runs": runs,
        "paired_against_reference": {name: pair_runs(runs[reference], r)
                                     for name, r in runs.items() if name != reference},
        "release_gate_credit": 0, "original_native_parity_claimed": False,
    }


def framebuffers(dumps: dict[int, Path]) -> dict[int, float]:
    out = {}
    for f, wram in dumps.items():
        fb = wram.with_name(wram.name.replace(".wram.bin", ".fb.bgrx"))
        if not fb.is_file():
            raise RuntimeError(f"engine did not dump a framebuffer for frame {f}")
        out[f] = brightness(fb.read_bytes())
    return out


class FramebufferOriginal(xc.Original):
    """Reference run that needs only framebuffers (no WRAM fill/dump)."""

    def run(self, control: str, frames: list[int], work: Path) -> dict[int, Path]:
        import os
        import subprocess
        if work.exists():
            raise ValueError(f"refuse to reuse prior evidence root {work}")
        work.mkdir(parents=True)
        (work / "case.input").write_text(control, encoding="utf-8")
        lines, prev = [], 0
        for f in frames:
            lines += [f"wait {f - prev}", f"dump o-{f}"]
            prev = f
        (work / "case.script").write_text("\n".join(lines + ["quit"]) + "\n", encoding="utf-8")
        env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1",
                   SNESREF_INPUT_FILE=str(work / "case.input"),
                   SNESREF_SCRIPT=str(work / "case.script"), SNESREF_DUMP_DIR=str(work))
        done = subprocess.run([str(self.snesref), str(self.core), str(self.rom)], env=env,
                              cwd=work, capture_output=True, text=True, errors="replace",
                              timeout=600)
        if done.returncode != 0:
            raise RuntimeError(f"reference emulator exited {done.returncode}")
        return {f: work / f"o-{f}.wram.bin" for f in frames}


def baldosa_run(exe: Path, rom: Path, frames: list[int], work: Path) -> dict[int, Path]:
    """Pinned Baldosa guest (gamesbyian/uniracers-recomp) with no controller input.

    Same launch contract as QA-01's ``run_pinned_baldosa``: ``--no-launcher``,
    an audio-off config, ``SNESRECOMP_DUMP_DIR``; no input shim, so only the
    no-input attract route is supported.
    """
    import os
    import subprocess
    if work.exists():
        raise ValueError(f"refuse to reuse prior evidence root {work}")
    (work / "dumps").mkdir(parents=True)
    (work / "config.ini").write_text("[Sound]\nEnableAudio = 0\n", encoding="utf-8")
    lines, prev = [], 0
    for f in frames:
        lines += [f"wait {f - prev}", f"dump b-{f}"]
        prev = f
    (work / "case.script").write_text("\n".join(lines + ["quit"]) + "\n", encoding="utf-8")
    env = dict(os.environ, SDL_AUDIODRIVER="dummy", SNESRECOMP_DUMP_DIR=str(work / "dumps"),
               SNESRECOMP_ROM=str(rom))
    env.pop("UR_QA_SCENE_INPUT_FILE", None)
    done = subprocess.run(["xvfb-run", "-a", str(exe.resolve()), "--no-launcher",
                           "--config", str(work / "config.ini"),
                           "--script", str(work / "case.script"), str(rom)],
                          cwd=work, env=env, capture_output=True, text=True,
                          errors="replace", timeout=1800)
    (work / "baldosa.log").write_text(done.stdout + done.stderr, encoding="utf-8")
    if done.returncode != 0:
        raise RuntimeError(f"Baldosa exited {done.returncode}")
    return {f: work / "dumps" / f"b-{f}.wram.bin" for f in frames}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, default=ROOT / "tests/input/two-player-first-race.input")
    ap.add_argument("--snesref", type=Path, required=True)
    ap.add_argument("--core", type=Path, action="append", required=True)
    ap.add_argument("--native-exe", type=Path)
    ap.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--frames", default="2-1126")
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--baldosa-exe", type=Path,
                    help="also run the pinned Baldosa guest (no-input routes only)")
    ap.add_argument("--allow-gaps", action="store_true",
                    help="accept several dense windows; runs at a window edge are truncated")
    ap.add_argument("--keep-dumps", action="store_true")
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("refuse to overwrite a prior census")
    frames = xc.parse_frames(args.frames)
    if frames != list(range(frames[0], frames[-1] + 1)) and not args.allow_gaps:
        raise SystemExit("blank-run lengths need every frame: use a dense a-b range")
    control = args.input.read_text(encoding="utf-8")
    if args.baldosa_exe and any(l.split("#", 1)[0].strip() for l in control.splitlines()):
        raise SystemExit("the Baldosa launcher supports only the no-input route")
    engines, identity = {}, {}
    for core in args.core:
        ref = FramebufferOriginal(args.snesref, core, args.rom)
        name = core.stem
        work = args.work / name
        values = framebuffers(ref.run(control, frames, work))
        engines[name] = [values[f] for f in frames]
        identity[name] = ref.identity
        if not args.keep_dumps:
            shutil.rmtree(work)
    if args.native_exe:
        work = args.work / "native"
        dumps = xc.native_run(args.native_exe, args.rom.resolve(), control, frames, work)
        values = framebuffers(dumps)
        engines["native"] = [values[f] for f in frames]
        identity["native"] = {"executable_sha256": xc.sha256(args.native_exe)}
        if not args.keep_dumps:
            shutil.rmtree(work)
    if args.baldosa_exe:
        work = args.work / "baldosa"
        values = framebuffers(baldosa_run(args.baldosa_exe, args.rom.resolve(), frames, work))
        engines["baldosa"] = [values[f] for f in frames]
        identity["baldosa"] = {"executable_sha256": xc.sha256(args.baldosa_exe)}
        if not args.keep_dumps:
            shutil.rmtree(work)
    result = census(frames, engines, args.core[0].stem)
    result["window_gaps_truncate_runs"] = frames != list(range(frames[0], frames[-1] + 1))
    result["identity"] = identity
    result["input_sha256"] = xc.sha256(args.input)
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["dark_frames"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
