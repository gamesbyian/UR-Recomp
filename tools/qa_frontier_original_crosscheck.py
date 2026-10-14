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
        # The emulator runs inside each case's work directory (it writes
        # audio/trace side files to its cwd), so never keep relative paths.
        self.snesref, self.core, self.rom = (p.resolve() for p in (snesref, core, rom))
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
                              env=env, cwd=work, capture_output=True, text=True,
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


def adjudicate(checkpoints: list[dict]) -> tuple[str, int | None]:
    """Case disposition from its checkpoint relations to the census.

    The census keeps only the EARLIEST witness of each token. A token owned by
    another case is therefore not evidence of divergence: this case may also
    have produced it (the 10k postmortem documents such repeats). Only a token
    the native census never saw is a divergence.
    """
    absent = [c["native_frame"] for c in checkpoints if c["relation"] == "absent"]
    if absent:
        return "coarse_divergence", absent[0]
    if any(c["relation"] == "other_case" for c in checkpoints):
        return "census_attribution_ambiguous", None
    return "coarse_agreement", None


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
    disposition, first = adjudicate(checkpoints)
    rows = [state(dumps[f - lag]) for f in TRACE_FRAMES]
    air = state(dumps[2580 - lag])
    if not keep:
        shutil.rmtree(work / f"{seed}-{arm}")
    return {"seed": seed, "arm": arm,
            "disposition": disposition,
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
    guest.execute(exe.resolve(), rom, work / "case.input", work / "case.script",
                  work / "run", 600, runtime_log=work / "native.log", observe_result=False)
    dumps = {f: work / "run" / "dumps" / f"n-{f}.wram.bin" for f in sorted(set(frames))}
    for f, p in dumps.items():
        if not p.is_file() or p.stat().st_size != 131072:
            raise RuntimeError(f"native did not dump frame {f}")
    return dumps


FINISH_START = 3430  # after the planner's last interval (< 3400 + 35)
FINISH_MASK = 0x080  # both seats hold Right: completes the ordinary 2P race


def finish_suffix(hold: int) -> str:
    """Declared, seed-independent stimulus that drives both racers to the finish."""
    if not 0 < hold <= 30000:
        raise ValueError("finish hold must be a bounded positive frame count")
    return f"# declared finish stimulus\n{FINISH_START}:{hold}:{FINISH_MASK:03x}:{FINISH_MASK:03x}\n"


def terminal_events(dumps: dict[int, Path], frames: list[int], offset: int) -> dict:
    """First native-indexed frame of each terminal transition seen by one engine."""
    events = {"both_laps_zero": None, "race_exit": None, "menu_first_nonzero": None}
    menus = []
    for f in frames:
        if f < FINISH_START:
            continue
        page = dumps[f - offset].read_bytes()
        d = state(dumps[f - offset])
        laps = (d["race_progress"]["player1"]["laps_remaining"],
                d["race_progress"]["player2"]["laps_remaining"])
        if events["both_laps_zero"] is None and laps == (0, 0):
            events["both_laps_zero"] = f
        if events["race_exit"] is None and page[0x0313] == 0:
            events["race_exit"] = f
        if events["menu_first_nonzero"] is None and page[0x009F] != 0:
            events["menu_first_nonzero"] = f
        if not menus or menus[-1][1] != page[0x009F]:
            menus.append((f, page[0x009F]))
    events["menu_sequence"] = menus
    return events


def paired_case(original: Original, exe: Path, seed: int, arm: str, lag: int,
                frames: list[int], work: Path, finish_hold: int = 0) -> dict:
    """Exact field comparison: native frame F against original frame F - lag."""
    control = case_input(seed, arm)
    if finish_hold:
        control += finish_suffix(finish_hold)
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
    terminal = None
    if finish_hold:
        terminal = {"native": terminal_events(native, frames, 0),
                    "original": terminal_events(orig, frames, lag)}
        terminal["race_relative_equal"] = (
            {k: v for k, v in terminal["native"].items()} ==
            {k: v for k, v in terminal["original"].items()})
    return {"seed": seed, "arm": arm, "declared_lag": lag,
            "finish_hold": finish_hold, "terminal_events_native_indexed": terminal,
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
    # Append-only journal: a killed run resumes without recomputing finished
    # cases. The header pins run, lag, original identity and tool digest, so a
    # resumed population is one cohort; errored cases are retried, not reused.
    header = {"schema": SCHEMA, "native_run_id": run_id, "lag": lag,
              "original": original.identity, "tool_sha256": sha256(Path(__file__))}
    journal = work / "results.jsonl"
    done: dict[int, dict] = {}
    if journal.exists():
        lines = journal.read_text(encoding="utf-8").splitlines()
        if not lines or json.loads(lines[0]) != header:
            raise ValueError("journal belongs to a different cross-check cohort")
        for line in lines[1:]:
            row = json.loads(line)
            if row.get("disposition") != "original_error":
                done[row["seed"]] = row
    else:
        work.mkdir(parents=True, exist_ok=True)
        journal.write_text(json.dumps(header, sort_keys=True) + "\n", encoding="utf-8")
    todo = [(s, a) for s, a in cases if s not in done]
    for s, a in todo:  # an interrupted case left a partial, unjournaled root
        shutil.rmtree(work / f"{s}-{a}", ignore_errors=True)
    results = [done[s] for s, _ in cases if s in done]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool, \
            journal.open("a", encoding="utf-8") as log:
        futures = {pool.submit(check_case, original, census, run_id, s, a, lag, work, keep): (s, a)
                   for s, a in todo}
        for fut in concurrent.futures.as_completed(futures):
            s, a = futures[fut]
            try:
                row = fut.result()
            except Exception as exc:  # retain, never count as agreement
                row = {"seed": s, "arm": a, "disposition": "original_error",
                       "error": str(exc)[:400]}
            results.append(row)
            log.write(json.dumps(row, sort_keys=True) + "\n")
            log.flush()
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
        "cases_resumed_from_journal": len(results) - len(todo),
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


SUMMARY_SCHEMA = "ur-frontier-original-crosscheck-summary/1"
RESULT_MENU, RESTORED_MENU = 0x84, 0x16


def terminal_summary(events: dict | None) -> dict | None:
    """Native-indexed terminal transitions and the result-phase duration per engine."""
    if not events:
        return None
    out = {}
    for side in ("native", "original"):
        e = events[side]
        firsts = {}
        for frame, menu in e["menu_sequence"]:
            firsts.setdefault(menu, frame)
        start, end = firsts.get(RESULT_MENU), firsts.get(RESTORED_MENU)
        out[side] = {"both_laps_zero": e["both_laps_zero"], "race_exit": e["race_exit"],
                     "result_menu_first": start, "restored_menu_first": end,
                     "result_phase_frames": end - start if None not in (start, end) else None}
    out["result_phase_delta_native_minus_original"] = (
        None if None in (out["native"]["result_phase_frames"], out["original"]["result_phase_frames"])
        else out["native"]["result_phase_frames"] - out["original"]["result_phase_frames"])
    return out


def rejudge(report: dict) -> dict:
    """Recompute dispositions and counts from stored checkpoint relations."""
    cases = []
    for c in report["cases"]:
        if "checkpoints" in c:
            disposition, first = adjudicate(c["checkpoints"])
            c = dict(c, disposition=disposition, first_divergent_native_frame=first)
        cases.append(c)
    out = dict(report, cases=cases)
    out["counts"] = dict(sorted(collections.Counter(c["disposition"] for c in cases).items()))
    out["divergent_cases"] = [
        {k: c[k] for k in ("seed", "arm", "first_divergent_native_frame")}
        for c in cases if c["disposition"] == "coarse_divergence"]
    out["attribution_ambiguous_cases"] = [
        {"seed": c["seed"], "arm": c["arm"],
         "tokens": [x["token"] for x in c["checkpoints"] if x["relation"] == "other_case"]}
        for c in cases if c["disposition"] == "census_attribution_ambiguous"]
    return out


def summarize(reports: list[dict], paired: list[dict]) -> dict:
    """Compact, reviewable evidence: per-run counts and every non-agreeing case."""
    runs = []
    for r in reports:
        if r.get("schema") != SCHEMA:
            raise ValueError("not a census cross-check report")
        r = rejudge(r)
        runs.append({k: r[k] for k in (
            "native_run_id", "native_source_sha", "native_executable_sha256",
            "declared_native_minus_original_entry_lag", "cases_checked",
            "cases_in_native_run", "counts", "divergent_cases",
            "original_full_trace_feature_counts", "native_full_trace_feature_counts",
            "original_offscreen_sentinel_case_counts", "census_record_sha256",
            "crosscheck_tool_sha256", "attribution_ambiguous_cases") if k in r})
        runs[-1]["original_errors"] = [
            {"seed": c["seed"], "arm": c["arm"], "error": c["error"]}
            for c in r["cases"] if c["disposition"] == "original_error"][:20]
    pairs = []
    for r in paired:
        if r.get("schema") != PAIRED_SCHEMA:
            raise ValueError("not a paired race-relative report")
        pairs.append({
            "seed": r["seed"], "arm": r["arm"], "declared_lag": r["declared_lag"],
            "measured_entry_host": r["measured_entry_host"],
            "declared_lag_confirmed": r["declared_lag_confirmed"],
            "disposition": r["disposition"],
            "first_divergent_native_frame": r["first_divergent_native_frame"],
            "frames_compared": len(r["rows"]),
            "max_semantic_wram_bytes_differing":
                max(row["semantic_wram_bytes_differing"] for row in r["rows"]),
            "native_executable_sha256": r["native_executable_sha256"],
            "finish_hold": r.get("finish_hold", 0),
            "terminal": terminal_summary(r.get("terminal_events_native_indexed"))})
    originals = {json.dumps(r["original"], sort_keys=True) for r in reports + paired}
    if len(originals) != 1:
        raise ValueError("reports mix different original emulator identities")
    total = collections.Counter()
    for r in runs:
        total.update(r["counts"])
    return {"schema": SUMMARY_SCHEMA, "original": json.loads(originals.pop()),
            "census_runs": runs, "census_totals": dict(sorted(total.items())),
            "paired_exact": pairs,
            "paired_totals": dict(sorted(collections.Counter(
                p["disposition"] for p in pairs).items())),
            "claim": "quantized census agreement and sampled exact semantic-WRAM agreement only",
            "original_native_parity_claimed": False, "release_gate_credit": 0}


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
    sm = sub.add_parser("summarize")
    sm.add_argument("--report", type=Path, action="append", default=[])
    sm.add_argument("--paired", type=Path, action="append", default=[])
    sm.add_argument("--out", type=Path, required=True)
    pr = sub.choices["paired"]
    pr.add_argument("--native-exe", type=Path, required=True)
    pr.add_argument("--seed", type=int, required=True)
    pr.add_argument("--arm", required=True, choices=frontier.ARMS)
    pr.add_argument("--lag", type=int, required=True)
    pr.add_argument("--finish-hold", type=int, default=0,
                    help="append the declared both-Right finish stimulus for N frames")
    pr.add_argument("--frames", default="1128-1140,1620,1740-3420/120",
                    help="native frames: a-b (every frame), a-b/step, or single values")
    args = ap.parse_args()
    if args.mode == "summarize":
        load = lambda p: json.loads(p.read_text(encoding="utf-8"))
        result = summarize([load(p) for p in args.report], [load(p) for p in args.paired])
        args.out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({k: result[k] for k in ("census_totals", "paired_totals")}))
        return 0
    if args.mode == "paired":
        original = Original(args.snesref, args.core, args.rom)
        if args.out.exists():
            raise SystemExit("refuse to overwrite a prior paired report")
        frames = parse_frames(args.frames)
        result = paired_case(original, args.native_exe, args.seed, args.arm, args.lag,
                             frames, args.work, args.finish_hold)
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
