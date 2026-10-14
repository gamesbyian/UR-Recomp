#!/usr/bin/env python3
"""Original-emulator cross-check of already-executed native frontier cases.

Every completed frontier case left lossless 96-bit normalized fingerprints in
the signed cumulative census (``frontier_exact_coverage``) with its exact
run/seed/arm witness. This tool regenerates each case's exact controller
stream from the pinned planner, replays it on the ORIGINAL USA ROM in Snes9x
(snesref), and asks whether the original reaches the same normalized
fingerprint at the race-relative-equivalent frame. No native process is
launched: the native side is the already-signed census.

Race-relative alignment is required, not optional. The ordinary 2P route
enters the race on different absolute host frames in different runtimes
(docs/TWO-PLAYER-FIXTURE-PLAN.md: Beetle 1133, Snes9x 1134, native 1135 for
the generic target). Identical absolute-frame input therefore lands on
different race ticks. With a native-minus-original entry lag ``L``, every
controller event at or after the original entry is moved ``L`` frames
earlier for the original, and native checkpoint ``F`` is compared with
original frame ``F - L``. ``L`` is a declared input of the experiment; the
``calibrate`` command measures which lags are consistent with the single
seed-independent 1740 fingerprint, and the cross-check never searches lags
per case.

A fingerprint match is agreement of the quantized census fields only, never
strict original/native equality, complete-event acceptance or release credit.
A mismatch is a *candidate* discrepancy with an exact reproducer.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import qa02_native_2p_seeded_endurance as guest  # noqa: E402
import qa_adaptive_frontier as frontier  # noqa: E402
import qa_frontier_exact as exact  # noqa: E402
from summarize_paired_player_slots import state  # noqa: E402

SCHEMA = "ur-frontier-original-crosscheck/1"
CALIBRATION_SCHEMA = "ur-frontier-original-lag-calibration/1"
# Snes9x's first inRace=1/race_tick=1 host frame on the stock 2P route,
# re-measured by ``calibrate`` before any lag is evaluated.
ORIGINAL_ENTRY_HOST = 1134
ENTRY_PROBE = range(1128, 1141)
CENSUS_FRAMES = tuple(int(n.removeprefix("endurance-")) for n in frontier.FRAME_NAMES)
TRACE_FRAMES = tuple(guest.FRAMES)
SEED_INDEPENDENT_FRAME = 1740
MAX_LAG = 8


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shift_post_entry(text: str, lag: int, entry: int = ORIGINAL_ENTRY_HOST) -> str:
    """Move every controller event starting at/after ``entry`` by ``-lag`` frames."""
    if not -MAX_LAG <= lag <= MAX_LAG:
        raise ValueError("implausible race-entry lag")
    out = []
    for raw in text.splitlines():
        body = raw.split("#", 1)[0].strip()
        parts = body.split(":") if body else []
        if len(parts) in (3, 4) and int(parts[0]) >= entry:
            start = int(parts[0]) - lag
            if start < entry:
                raise ValueError("shift would move post-entry input before race entry")
            parts[0] = str(start)
            raw = ":".join(parts)
        out.append(raw)
    return "\n".join(out) + "\n"


def case_input(seed: int, arm: str) -> str:
    """The exact native frontier controller stream for one case."""
    prefix, _ = guest.base_source()
    actions, _ = frontier.actions_for(seed, arm)
    return guest.render_input(prefix, actions, None)


class Original:
    def __init__(self, snesref: Path, core: Path, rom: Path):
        for p in (snesref, core, rom):
            if not p.is_file():
                raise ValueError(f"missing original-emulator input {p}")
        if sha256(rom) != guest.ROM_SHA:
            raise ValueError("not the canonical original USA ROM")
        self.snesref, self.core, self.rom = snesref, core, rom
        self.identity = {"original_rom_sha256": guest.ROM_SHA,
                         "snes9x_core_sha256": sha256(core),
                         "snesref_sha256": sha256(snesref)}

    def run(self, control: str, frames: list[int], work: Path) -> dict[int, Path]:
        if work.exists():
            raise ValueError(f"refuse to reuse prior original evidence root {work}")
        work.mkdir(parents=True)
        (work / "case.input").write_text(control, encoding="utf-8")
        lines, prev = [], 0
        for f in sorted(set(frames)):
            lines += [f"wait {f - prev}", f"dump o-{f}"]
            prev = f
        lines.append("quit")
        (work / "case.script").write_text("\n".join(lines) + "\n", encoding="utf-8")
        env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1",
                   SNESREF_WRAM_FILL="0",
                   SNESREF_INPUT_FILE=str(work / "case.input"),
                   SNESREF_SCRIPT=str(work / "case.script"),
                   SNESREF_DUMP_DIR=str(work))
        done = subprocess.run([str(self.snesref), str(self.core), str(self.rom)],
                              env=env, capture_output=True, text=True,
                              errors="replace", timeout=300)
        (work / "original.log").write_text(done.stdout + done.stderr, encoding="utf-8")
        if done.returncode != 0:
            raise RuntimeError(f"original emulator exited {done.returncode}")
        dumps = {}
        for f in sorted(set(frames)):
            p = work / f"o-{f}.wram.bin"
            if not p.is_file() or p.stat().st_size != 131072:
                raise RuntimeError(f"original emulator did not dump frame {f}")
            if f"script f={f} dump o-{f} " not in done.stdout + done.stderr:
                raise RuntimeError(f"no original dump receipt for host frame {f}")
            dumps[f] = p
        return dumps


def load_census(ledger: dict) -> tuple[dict, str]:
    cov = ledger.get("frontier_exact_coverage")
    if not isinstance(cov, dict):
        raise ValueError("ledger has no exact frontier census")
    exact.validate_record(cov)
    return exact._parse(cov["witnesses_b64"], True), cov["record_sha256"]


def run_cases(census: dict, run_id: int) -> list[tuple[int, str]]:
    cases = {(seed, arm) for run, seed, arm, _shard in census.values() if run == run_id}
    if not cases:
        raise ValueError(f"census has no witnesses for run {run_id}")
    seeds = collections.Counter(seed for seed, _ in cases)
    if any(n != 1 for n in seeds.values()):
        raise ValueError("census attributes one seed to several arms")
    return sorted(cases)


def run_record(ledger: dict, run_id: int) -> dict:
    rows = [r for r in ledger.get("records", [])
            if r.get("campaign") == "frontier" and r.get("github_run_id") == run_id]
    if len(rows) != 1 or rows[0].get("disposition") != "completed_positive":
        raise ValueError("cross-check only a single completed frontier ledger record")
    return rows[0]


def calibrate(original: Original, census: dict, lags: list[int], work: Path) -> dict:
    """Measure original entry, then test each lag on the seed-independent sample."""
    probe = original.run(open(guest.CONTROL_FILE, encoding="utf-8").read(),
                         list(ENTRY_PROBE), work / "entry-probe")
    entry = next((f for f in ENTRY_PROBE if probe[f].read_bytes()[0x0313] == 1), None)
    if entry != ORIGINAL_ENTRY_HOST or probe[entry].read_bytes()[0x0FE7] != 1:
        raise ValueError(f"original entry moved: observed {entry}")
    # Every planner case starts with the same (1650,60,P1 080,P2 040) stimulus,
    # so the native 1740 sample is one shared token. Any seed reproduces it.
    seed, arm = 50000000, "balanced"
    rows = []
    for lag in lags:
        frame = SEED_INDEPENDENT_FRAME - lag
        dumps = original.run(shift_post_entry(case_input(seed, arm), lag),
                             [frame], work / f"lag{lag:+d}")
        token = frontier.normalized_token(dumps[frame], f"endurance-{SEED_INDEPENDENT_FRAME}")
        rows.append({"lag": lag, "original_frame": frame,
                     "token": token, "in_native_census": token in census})
    return {"schema": CALIBRATION_SCHEMA, "original_entry_host": entry,
            "original": original.identity, "rows": rows,
            "consistent_lags": [r["lag"] for r in rows if r["in_native_census"]],
            "note": "one seed-independent quantized sample cannot separate lags of "
                    "equal scheduler parity; declare the lag before cross-checking"}


# Bank-82 split-screen culling substitutes fixed per-screen coordinates for
# the OPPOSITE racer once it leaves that viewport; the ordinary 2P regression
# asserts these exact sentinels on both original and native.
OFFSCREEN_SENTINELS = {"screen1_player2": 0x70, "screen2_player1": 0x30}


def sentinel_labels(rows: list[dict]) -> list[str]:
    """Source-qualified opponent-offscreen incidence over the sampled frames."""
    found = set()
    for row in rows:
        screen = row["camera_and_viewport"]["screen_relative"]
        for key, value in OFFSCREEN_SENTINELS.items():
            if screen[key + "_x"] == value and screen[key + "_y"] == value:
                found.add(f"{key}-offscreen-sentinel")
    if len(found) == 2:
        found.add("both-opponents-offscreen-sentinel")
    return sorted(found)


def check_case(original: Original, census: dict, run_id: int, seed: int,
               arm: str, lag: int, work: Path, keep: bool = False) -> dict:
    frames = sorted({f - lag for f in TRACE_FRAMES + CENSUS_FRAMES})
    dumps = original.run(shift_post_entry(case_input(seed, arm), lag), frames,
                         work / f"{seed}-{arm}")
    checkpoints = []
    for f in CENSUS_FRAMES:
        label = f"endurance-{f}"
        token = frontier.normalized_token(dumps[f - lag], label)
        witness = census.get(token)
        if witness is None:
            relation = "absent"
        elif witness[1] == seed and witness[0] == run_id:
            relation = "this_case"
        elif f == SEED_INDEPENDENT_FRAME:
            relation = "shared_seed_independent"
        else:
            relation = "other_case"
        checkpoints.append({"native_frame": f, "original_frame": f - lag,
                            "token": token, "relation": relation})
    agree = [c["relation"] in ("this_case", "shared_seed_independent") for c in checkpoints]
    first = next((c["native_frame"] for c, ok in zip(checkpoints, agree) if not ok), None)
    rows = [state(dumps[f - lag]) for f in TRACE_FRAMES]
    air = state(dumps[2580 - lag])
    if not keep:
        shutil.rmtree(work / f"{seed}-{arm}")
    return {"seed": seed, "arm": arm,
            "disposition": "coarse_agreement" if first is None else "coarse_divergence",
            "first_divergent_native_frame": first,
            "checkpoints": checkpoints,
            "original_feature_labels": sorted(frontier._feature_labels(rows)),
            "original_offscreen_sentinel_labels": sentinel_labels(rows),
            "original_raw_air_at_native_2580":
                [air["slot1"]["air_effective"], air["slot2"]["air"]],
            "original_frame_for_native_2580": 2580 - lag}


PAIRED_SCHEMA = "ur-frontier-paired-race-relative/1"
SCHEDULER = {"phase0": 0x0300, "phase2": 0x0302, "phase3": 0x0304,
             "in_race": 0x0313, "race_tick": 0x0FE7}


def flat_state(path: Path) -> dict:
    """Every source-labelled field ``state`` decodes, plus scheduler bytes, exactly."""
    out = {}

    def walk(prefix, value):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(f"{prefix}.{k}" if prefix else k, v)
        elif isinstance(value, (list, tuple)):
            for i, v in enumerate(value):
                walk(f"{prefix}[{i}]", v)
        else:
            out[prefix] = value
    walk("", state(path))
    page = path.read_bytes()
    for name, addr in SCHEDULER.items():
        out["scheduler." + name] = page[addr]
    return out


def native_run(exe: Path, rom: Path, control: str, frames: list[int], work: Path) -> dict[int, Path]:
    """One real native process through the frontier's own isolated launcher."""
    work.mkdir(parents=True)
    (work / "case.input").write_text(control, encoding="utf-8")
    lines, prev = [], 0
    for f in sorted(set(frames)):
        lines += [f"wait {f - prev}", f"dump n-{f}"]
        prev = f
    lines.append("quit")
    (work / "case.script").write_text("\n".join(lines) + "\n", encoding="utf-8")
    guest.execute(exe, rom, work / "case.input", work / "case.script", work / "run", 600,
                  runtime_log=work / "native.log")
    dumps = {f: work / "run" / "dumps" / f"n-{f}.wram.bin" for f in sorted(set(frames))}
    for f, p in dumps.items():
        if not p.is_file() or p.stat().st_size != 131072:
            raise RuntimeError(f"native did not dump frame {f}")
    return dumps


def paired_case(original: Original, exe: Path, seed: int, arm: str, lag: int,
                frames: list[int], work: Path) -> dict:
    """Exact field comparison: native frame F against original frame F - lag."""
    control = case_input(seed, arm)
    native = native_run(exe, original.rom, control, frames, work / "native")
    orig = original.run(shift_post_entry(control, lag), [f - lag for f in frames],
                        work / "original")
    def entry(dumps: dict[int, Path], offset: int) -> int | None:
        for f in frames:
            if f in ENTRY_PROBE and dumps[f - offset].read_bytes()[0x0313] == 1:
                return f - offset
        return None
    entries = {"native": entry(native, 0), "original": entry(orig, lag)}
    measured = (entries["native"] - entries["original"]
                if None not in entries.values() else None)
    rows, first = [], None
    for f in frames:
        if f < ORIGINAL_ENTRY_HOST + lag + 1:
            continue  # pre-entry frontend frames are not race-relative
        n, o = flat_state(native[f]), flat_state(orig[f - lag])
        diff = sorted(k for k in n if n[k] != o.get(k))
        npage, opage = native[f].read_bytes(), orig[f - lag].read_bytes()
        rows.append({"native_frame": f, "original_frame": f - lag,
                     "differing_fields": {k: [n[k], o[k]] for k in diff},
                     "semantic_wram_bytes_differing":
                         sum(a != b for a, b in zip(npage[0x200:], opage[0x200:]))})
        if diff and first is None:
            first = f
    return {"seed": seed, "arm": arm, "declared_lag": lag,
            "measured_entry_host": entries, "measured_lag": measured,
            "declared_lag_confirmed": measured == lag,
            "disposition": "exact_field_agreement" if first is None else "field_divergence",
            "first_divergent_native_frame": first, "rows": rows}


def crosscheck(ledger: dict, run_id: int, lag: int, original: Original,
               work: Path, workers: int, limit: int | None,
               seeds: set[int] | None, keep: bool = False) -> dict:
    census, census_sha = load_census(ledger)
    record = run_record(ledger, run_id)
    cases = run_cases(census, run_id)
    if seeds:
        cases = [c for c in cases if c[0] in seeds]
    if limit is not None:
        cases = cases[:limit]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(check_case, original, census, run_id, s, a, lag, work, keep): (s, a)
                   for s, a in cases}
        for fut in concurrent.futures.as_completed(futures):
            s, a = futures[fut]
            try:
                results.append(fut.result())
            except Exception as exc:  # retain, never count as agreement
                results.append({"seed": s, "arm": a, "disposition": "original_error",
                                "error": str(exc)[:400]})
    results.sort(key=lambda r: r["seed"])
    counts = collections.Counter(r["disposition"] for r in results)
    features = collections.Counter(f for r in results for f in r.get("original_feature_labels", []))
    sentinels = collections.Counter(
        f for r in results for f in r.get("original_offscreen_sentinel_labels", []))
    return {
        "schema": SCHEMA,
        "native_run_id": run_id,
        "native_source_sha": record.get("source_sha"),
        "native_executable_sha256": record["metrics"].get("native_executable_sha256"),
        "native_full_trace_feature_counts": record["metrics"].get("full_trace_feature_counts"),
        "census_record_sha256": census_sha,
        "declared_native_minus_original_entry_lag": lag,
        "original": original.identity,
        "crosscheck_tool_sha256": sha256(Path(__file__)),
        "cases_checked": len(results),
        "cases_in_native_run": len(run_cases(census, run_id)),
        "counts": dict(sorted(counts.items())),
        "original_full_trace_feature_counts": dict(sorted(features.items())),
        "original_offscreen_sentinel_case_counts": dict(sorted(sentinels.items())),
        "divergent_cases": [
            {k: r[k] for k in ("seed", "arm", "first_divergent_native_frame")}
            for r in results if r["disposition"] == "coarse_divergence"],
        "cases": results,
        "claim": "quantized census-field agreement only",
        "original_native_parity_claimed": False,
        "release_gate_credit": 0,
    }


def parse_frames(spec: str) -> list[int]:
    frames = set()
    for part in spec.split(","):
        step = 1
        if "/" in part:
            part, step_text = part.split("/")
            step = int(step_text)
        if "-" in part:
            a, b = (int(x) for x in part.split("-"))
            frames.update(range(a, b + 1, step))
        else:
            frames.add(int(part))
    if not frames or min(frames) < 1 or step < 1:
        raise ValueError("invalid frame specification")
    return sorted(frames)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    for name in ("calibrate", "run", "paired"):
        p = sub.add_parser(name)
        p.add_argument("--ledger", type=Path, required=True)
        p.add_argument("--snesref", type=Path, required=True)
        p.add_argument("--core", type=Path, required=True)
        p.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
        p.add_argument("--work", type=Path, required=True)
        p.add_argument("--out", type=Path, required=True)
    sub.choices["calibrate"].add_argument("--lags", default="-2,-1,0,1,2,3")
    r = sub.choices["run"]
    r.add_argument("--run-id", type=int, required=True)
    r.add_argument("--lag", type=int, required=True)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--limit", type=int)
    r.add_argument("--seeds", default="")
    r.add_argument("--keep-dumps", action="store_true",
                   help="retain each case's original WRAM dumps (128 KiB x 15)")
    pr = sub.choices["paired"]
    pr.add_argument("--native-exe", type=Path, required=True)
    pr.add_argument("--seed", type=int, required=True)
    pr.add_argument("--arm", required=True, choices=frontier.ARMS)
    pr.add_argument("--lag", type=int, required=True)
    pr.add_argument("--frames", default="1128-1140,1620,1740-3420/120",
                    help="native frames: a-b (every frame), a-b/step, or single values")
    args = ap.parse_args()
    if args.mode == "paired":
        original = Original(args.snesref, args.core, args.rom)
        if args.out.exists():
            raise SystemExit("refuse to overwrite a prior paired report")
        frames = parse_frames(args.frames)
        result = paired_case(original, args.native_exe, args.seed, args.arm, args.lag,
                             frames, args.work)
        result.update({"schema": PAIRED_SCHEMA, "original": original.identity,
                       "native_executable_sha256": sha256(args.native_exe),
                       "release_gate_credit": 0, "original_native_parity_claimed": False})
        args.out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({k: result[k] for k in ("disposition", "first_divergent_native_frame")}))
        return 0
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    original = Original(args.snesref, args.core, args.rom)
    if args.out.exists():
        raise SystemExit("refuse to overwrite a prior cross-check report")
    if args.mode == "calibrate":
        census, _ = load_census(ledger)
        result = calibrate(original, census,
                           [int(x) for x in args.lags.split(",")], args.work)
    else:
        seeds = {int(x) for x in args.seeds.split(",") if x}
        result = crosscheck(ledger, args.run_id, args.lag, original, args.work,
                            args.workers, args.limit, seeds or None, args.keep_dumps)
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in result if k in
                      ("counts", "consistent_lags", "divergent_cases",
                       "original_full_trace_feature_counts",
                       "native_full_trace_feature_counts")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
