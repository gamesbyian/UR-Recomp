#!/usr/bin/env python3
"""Manual two-job fan-out of exact original Windows bridge journeys; no QA credit."""
from __future__ import annotations

import argparse
import ctypes
from contextlib import contextmanager, nullcontext
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import re
import time
from pathlib import Path

import run_baldosa_parallel_windows_journeys as bridge
import baldosa_native_practice_courses_probe as practice

SCHEMA = "ur-win32-acceptance-fanout/5"
AGGREGATE_SCHEMA = "ur-win32-acceptance-fanout-aggregate/5"
GROUPS = {"seed-dependent": (0, 1, 2), "independent": tuple(range(3, 13))}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def original_script_hashes(commands=None):
    """Bind the existing case IDs to exact original Bash bodies, not just names.

    This is a source/test identity receipt for prospective same-script
    comparisons. It does not prove any Windows process executed on its own.
    """
    if commands is None:
        commands = bridge.extract_commands(bridge.WORKFLOW.read_text(encoding="utf-8"))
    bridge.independent_priority_indices(len(commands))
    require(len(commands) == len(bridge.STEPS), "original Windows journey population changed")
    return tuple(hashlib.sha256(script.encode("utf-8")).hexdigest()
                 for script in commands)


def candidate_identity(source_sha, exe, fixture, archive):
    require(bool(HEX40.fullmatch(source_sha)), "invalid source SHA")
    for path in (exe, fixture, archive):
        require(path.is_file() and not path.is_symlink(), "missing candidate input " + str(path))
    return {"source_sha": source_sha, "exe_sha256": bridge.sha256_file(exe),
            "fixture_sha256": bridge.sha256_file(fixture),
            "zip_sha256": bridge.sha256_file(archive)}


def attest_private_case_files(rows, work):
    """Bind private original script outputs without publishing their contents.

    Full guest logs stay on the ephemeral Windows runner. The artifact exposes
    only the SHA-256, size and fixed filename, so a later separately authorized
    read can detect whether the original bytes differ from the producer claim.
    A digest is not a signature and cannot, by itself, independently verify
    that the guest actually executed its claimed journey.
    """
    for row in rows:
        index = row["index"]
        for label, suffix in (("log", ".log"), ("summary", ".md")):
            expected = f"step-{index:02d}{suffix}"
            require(row.get(label) == expected,
                    "original script output name changed")
            path = work / expected
            # The existing original bridge permits an absent optional .md
            # summary; only the subprocess's combined .log is mandatory.
            require(not path.is_symlink(), "redirected original Windows " + label)
            if label == "summary" and not path.exists():
                row["summary_sha256"] = None
                row["summary_bytes"] = 0
                continue
            require(path.is_file(), "missing original Windows " + label)
            data = path.read_bytes()
            row[label + "_sha256"] = hashlib.sha256(data).hexdigest()
            row[label + "_bytes"] = len(data)
    return rows



def selected_practice_workers(env, group):
    """Attest the workflow's selected mode, and refuse seed-group leakage."""
    selected, effective = (env.get("UR_PRACTICE_SELECTED_WORKERS"),
                           env.get("UR_PRACTICE_CASE_WORKERS"))
    require(selected in ("1", "2") and effective in ("1", "2"),
            "Practice worker selection missing or invalid")
    require(effective == (selected if group == "independent" else "1"),
            "Practice worker selection differs from the intended matrix group")
    return int(selected)


def practice_report_witness(commands, env, who, selected):
    """Read the actual original script's private report, never expose its bytes.

    The report is emitted only after all ten actual native launches, Restart,
    both paused Options modes and private-save checks pass. Its fixed pathname
    comes from the unchanged original Bash case 12, never from user input.
    """
    original_out = bridge.OUT_RE.findall(commands[12])
    require(len(original_out) == 1, "original Practice output root changed")
    output_root = Path(env["RUNNER_TEMP"]) / original_out[0]
    report_path = output_root / "report.json"
    require(not output_root.is_symlink() and output_root.is_dir()
            and not report_path.is_symlink() and report_path.is_file(),
            "missing or redirected genuine Practice source report")
    require(report_path.stat().st_size <= 64 * 1024,
            "unbounded original Practice report")
    raw = report_path.read_bytes()
    require(len(raw) <= 64 * 1024, "unbounded original Practice report")
    try:
        report = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError("invalid original Practice source report") from error
    require(isinstance(report, dict), "invalid original Practice source report")
    require(type(report.get("experimental_practice_case_workers")) is int
            and report["experimental_practice_case_workers"] == selected,
            "original Practice executed worker count differs from selection")
    source = report.get("source_binding")
    require(isinstance(source, dict)
            and source.get("github_sha") == who["source_sha"]
            and source.get("exe_sha256") == who["exe_sha256"]
            and source.get("rom_sha256") == practice.USA_SHA256,
            "original Practice report source/exe/ROM differs")
    expected = [("tier0_never_played", *case)
                for case in practice.TIER0] + [
                    ("tier2_formatted_save", *case) for case in practice.TIER2]
    expected_cases = [
        {"group": group, "case": label, "track": track,
         "course": name, "picker_steps": steps}
        for group, label, steps, track, name in expected
    ]
    require(report.get("courses_admitted") == 10
            and report.get("cases") == expected_cases,
            "original Practice ten source-qualified cases changed")
    require(report.get("pause_options_in_practice") ==
            ["sdl_keys", "p1_pad_semantic"]
            and report.get("restart_in_practice") ==
            "pause_delayed_restart_rewound_sram_equal"
            and report.get("available_tier0") == 20
            and report.get("available_tier2") == 40
            and report.get("hunter_admitted") is False
            and report.get("player_save_bytes_unchanged") is True
            and report.get("practice_results_published") is False
            and report.get("physical_gamepad_certified") is False
            and report.get("release_gate_credit") == 0,
            "original Practice source claims changed")
    require(report.get("tier2_seed_sha256") ==
            hashlib.sha256(practice.tier2_seed()).hexdigest(),
            "original Practice save-seed provenance changed")
    return {"requested_workers": selected, "reported_workers": selected,
            "report_sha256": hashlib.sha256(raw).hexdigest(), "report_cases": 10}


# Source-local invocation windows are a diagnostic of bridge scheduling, not
# independent proof that two child Windows/SDL native processes ran together.
SEED_MODE_KEYS = frozenset((
    "requested_workers", "effective_workers", "source_seed_sha256",
    "invocation_windows", "invocation_overlap_ns",
    "native_process_overlap_verified",
))



@contextmanager
def protect_windows_seed_readonly(seed):
    """Keep the original 8KiB input share-readable but deny write/delete.

    This is a real Win32 file-sharing handle, not chmod, advisory flock,
    a digest, or proof that the two native game processes overlapped.
    Opening fails closed on non-Windows hosts or incompatible share modes.
    https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew
    """
    require(os.name == "nt",
            "parallel Records requires actual Windows seed write-denial")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = (
        ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
    )
    create.restype = ctypes.c_void_p
    close = kernel.CloseHandle
    close.argtypes = (ctypes.c_void_p,)
    close.restype = ctypes.c_int
    # GENERIC_READ, FILE_SHARE_READ only, OPEN_EXISTING,
    # FILE_ATTRIBUTE_NORMAL. This denies writes AND rename/delete while open.
    handle = create(str(seed), 0x80000000, 0x00000001,
                    None, 3, 0x00000080, None)
    if handle in (None, 0, ctypes.c_void_p(-1).value):
        raise OSError(ctypes.get_last_error(),
                      "could not hold read-only Windows SRAM share handle")
    try:
        yield
    finally:
        if not close(handle):
            raise OSError(ctypes.get_last_error(),
                          "failed to close Windows SRAM share handle")


def invocation_overlap_ns(windows):
    """Calculate only overlapping bridge.run_one invocation time on one host."""
    if len(windows) != 2:
        return 0
    return max(0, min(w["ended_ns"] for w in windows) -
               max(w["started_ns"] for w in windows))


def seed_mode_default(group, requested):
    return {
        "requested_workers": requested if group == "seed-dependent" else 1,
        "effective_workers": 0,
        "source_seed_sha256": None,
        "invocation_windows": [],
        "invocation_overlap_ns": 0,
        "native_process_overlap_verified": False,
    }


def validate_seed_followup_mode(mode, group, rows):
    """Fail closed on unsupported/mislabeled Records execution-mode receipts.

    A self-digested producer receipt never constitutes an independent native
    subprocess-overlap or Windows-window/focus witness.
    """
    require(type(mode) is dict and set(mode) == SEED_MODE_KEYS,
            "missing Records follow-up worker-mode evidence")
    require(type(mode["requested_workers"]) is int
            and mode["requested_workers"] in (1, 2)
            and type(mode["effective_workers"]) is int
            and mode["effective_workers"] in (0, 1, 2)
            and mode["native_process_overlap_verified"] is False,
            "invalid Records follow-up worker-mode claim")
    require(type(mode["invocation_overlap_ns"]) is int
            and mode["invocation_overlap_ns"] >= 0,
            "invalid Records invocation-overlap claim")
    windows = mode["invocation_windows"]
    require(type(windows) is list, "malformed Records invocation windows")
    if group == "independent":
        require(mode == seed_mode_default(group, 1),
                "independent group falsely claimed Records worker execution")
        return
    require(type(rows) is list, "missing Records original-case inventory")
    ran_followups = (len(rows) == 3 and
                     [row.get("index") for row in rows if isinstance(row, dict)]
                     == [0, 1, 2])
    if not ran_followups:
        require(mode["effective_workers"] == 0
                and mode["source_seed_sha256"] is None
                and windows == [] and mode["invocation_overlap_ns"] == 0,
                "missing Records cases falsely claimed executed follow-ups")
        return
    require(mode["effective_workers"] == mode["requested_workers"],
            "selected Records workers differ from executed mode")
    require(type(mode["source_seed_sha256"]) is str
            and bool(HEX64.fullmatch(mode["source_seed_sha256"])),
            "missing actual source SRAM digest")
    require(len(windows) == 2, "missing original Records invocation windows")
    for index, window in zip((1, 2), windows):
        require(type(window) is dict
                and set(window) == {"index", "started_ns", "ended_ns"}
                and type(window["index"]) is int and window["index"] == index
                and type(window["started_ns"]) is int
                and type(window["ended_ns"]) is int
                and 0 < window["started_ns"] < window["ended_ns"],
                "invalid Records source invocation window")
    overlap = invocation_overlap_ns(windows)
    require(mode["invocation_overlap_ns"] == overlap,
            "Records invocation-overlap calculation contradicted")
    require((mode["requested_workers"] == 1 and overlap == 0)
            or (mode["requested_workers"] == 2 and overlap > 0),
            "Records requested parallel mode lacks observed bridge overlap")


def validate_receipt(receipt, group, source_sha):
    require(isinstance(receipt, dict) and receipt.get("schema") == SCHEMA, "wrong receipt schema")
    require(group in GROUPS and receipt.get("group") == group, "wrong group")
    who = receipt.get("candidate_identity")
    require(isinstance(who, dict) and set(who) ==
            {"source_sha", "exe_sha256", "fixture_sha256", "zip_sha256"},
            "missing candidate identity")
    require(who["source_sha"] == source_sha and bool(HEX40.fullmatch(source_sha)),
            "source identity changed")
    require(all(isinstance(who[k], str) and bool(HEX64.fullmatch(who[k]))
                for k in ("exe_sha256", "fixture_sha256", "zip_sha256")),
            "invalid binary/ZIP digests")
    stamp = receipt.get("receipt_sha256")
    unsigned = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    require(isinstance(stamp, str) and bool(HEX64.fullmatch(stamp))
            and digest(unsigned) == stamp, "altered receipt")
    validate_seed_followup_mode(receipt.get("seed_followup_mode"),
                                group, receipt.get("cases"))
    mode = receipt.get("practice_mode")
    require(isinstance(mode, dict) and set(mode) ==
            {"requested_workers", "reported_workers", "report_sha256", "report_cases"},
            "missing Practice worker-mode evidence")
    require(type(mode["requested_workers"]) is int
            and mode["requested_workers"] in (1, 2),
            "invalid Practice selected worker mode")
    original_rows = receipt.get("cases")
    case12_passed = (isinstance(original_rows, list) and
                     any(isinstance(row, dict) and row.get("index") == 12
                         and row.get("exit_code") == 0 for row in original_rows))
    if group == "independent" and case12_passed:
        require(type(mode["reported_workers"]) is int
                and mode["reported_workers"] == mode["requested_workers"]
                and mode["report_cases"] == 10
                and type(mode["report_sha256"]) is str
                and bool(HEX64.fullmatch(mode["report_sha256"])),
                "invalid original Practice executed-mode evidence")
    else:
        require(mode["reported_workers"] is None
                and mode["report_sha256"] is None
                and mode["report_cases"] is None,
                "failed/non-Practice group falsely claimed Practice success")
    expected = GROUPS[group]
    original_hashes = original_script_hashes()
    require(receipt.get("expected_indices") == list(expected), "case inventory changed")
    rows = receipt.get("cases")
    require(isinstance(rows, list) and len(rows) == len(expected),
            "missing / duplicated original cases")
    for idx, row in zip(expected, rows):
        require(isinstance(row, dict) and row.get("index") == idx
                and row.get("name") == bridge.STEPS[idx], "original case identity changed")
        require(row.get("script_sha256") == original_hashes[idx],
                "original Windows shell script identity changed")
        require(type(row.get("exit_code")) is int, "invalid original step exit code")
        require(type(row.get("elapsed_seconds")) in (float, int)
                and row["elapsed_seconds"] >= 0, "invalid measured step time")
        for label, ext in (("log", ".log"), ("summary", ".md")):
            require(row.get(label) == f"step-{idx:02d}{ext}",
                    "changed original private Windows output label")
            value = row.get(label + "_sha256")
            require((value is None and label == "summary" and
                     row.get("summary_bytes") == 0)
                    or (type(value) is str and bool(HEX64.fullmatch(value))),
                    "missing original output SHA256")
            require(type(row.get(label + "_bytes")) is int
                    and 0 <= row[label + "_bytes"] < 50_000_000,
                    "invalid private original output size")
    require(receipt.get("release_gate_credit") == 0
            and receipt.get("independent_physical_qa") is False,
            "producer attempted QA promotion")
    require(receipt.get("all_passed") is
            all(row["exit_code"] == 0 for row in rows), "contradictory success marker")
    return who


def run_group(group, source_sha, archive, work, env=None, workers=2,
              seed_followup_workers=1):
    require(group in GROUPS and workers in (1, 2), "invalid group/parallelism")
    # No current hosted workflow supplies this flag. The default is serial.
    require(type(seed_followup_workers) is int
            and seed_followup_workers in (1, 2),
            "invalid Records seed-followup worker count")
    require(group == "seed-dependent" or seed_followup_workers == 1,
            "Records seed-followup workers apply only to seed-dependent group")
    env = dict(os.environ if env is None else env)
    selected = selected_practice_workers(env, group)
    require(env.get("GITHUB_SHA") == source_sha, "not the checked-out source")
    require(bool(env.get("RUNNER_TEMP") and env.get("GITHUB_STEP_SUMMARY")),
            "not a pinned Actions run")
    require(not work.exists() and not work.is_symlink(), "work root already used")
    who = candidate_identity(source_sha, bridge.EXE, bridge.FIXTURE, archive)
    commands = bridge.extract_commands(bridge.WORKFLOW.read_text(encoding="utf-8"))
    bridge.independent_priority_indices(len(commands))
    require(len(commands) == 13, "missing original Windows journeys")
    original_hashes = original_script_hashes(commands)
    if group == "seed-dependent" and seed_followup_workers == 2:
        # The original 1P/2P scripts must each have exactly this seed and
        # exactly one baseline dependency, with no altered source body.
        canonical_seed = ('--seed "$RUNNER_TEMP/UR Baldosa Win32 Pause Route/'
                          'baseline/Modern Player Data With Spaces/saves/save.srm"')
        require(all(commands[i].count(canonical_seed) == 1
                    and commands[i].count("baseline/") == 1
                    for i in (1, 2)),
                "original Records seed source changed; no parallel execution")
        # The Windows children must not inherit an old Records output root,
        # whether its contents are regular files or a redirected directory.
        # Fail before producing a NEW baseline, not after partial gameplay.
        outputs = [bridge.OUT_RE.findall(commands[i]) for i in (0, 1, 2)]
        require(all(len(paths) == 1 for paths in outputs),
                "original Records output roots are ambiguous")
        names = [Path(paths[0]) for paths in outputs]
        require(all(not path.is_absolute()
                    and ".." not in path.parts and len(path.parts) >= 1
                    for path in names),
                "original Records output roots escape runner temp")
        # Authentic source layout is intentional: case 0 owns the parent
        # that contains the seed, while 1P and 2P write separate siblings.
        # Refuse a source change that moves either sibling into the other's
        # tree or outside the original baseline parent.
        parent = Path("UR Baldosa Win32 Pause Route")
        require(names == [
                    parent, parent / "native_real_1p_records",
                    parent / "native_real_2p_records",
                ],
                "original Records parent and sibling output layout changed")
        require(all(not (Path(env["RUNNER_TEMP"]) / name).exists()
                    and not (Path(env["RUNNER_TEMP"]) / name).is_symlink()
                    for name in names),
                "original Records output root already exists")

    mode_receipt = seed_mode_default(group, seed_followup_workers)
    work.mkdir(parents=True)
    started = time.monotonic()
    if group == "seed-dependent":
        first = bridge.run_one(0, commands[0], work, env)
        rows = [first]
        seed = (Path(env["RUNNER_TEMP"]) / "UR Baldosa Win32 Pause Route" /
                "baseline" / "Modern Player Data With Spaces" / "saves" / "save.srm")
        if first["exit_code"] == 0 and seed.is_file() and not seed.is_symlink() and seed.stat().st_size == 8192:
            seed_sha = bridge.sha256_file(seed)
            # The digest alone misses an identical-byte replace. Sampling
            # file identity and modification metadata adds a separate
            # negative control; it does not prove no transient write/restore.
            seed_stat = seed.stat()
            seed_identity = (seed_stat.st_dev, seed_stat.st_ino,
                             seed_stat.st_size, seed_stat.st_mtime_ns,
                             seed_stat.st_ctime_ns)
            def observed_case(index):
                started_ns = time.monotonic_ns()
                result = bridge.run_one(index, commands[index], work, env)
                ended_ns = time.monotonic_ns()
                return result, {
                    "index": index, "started_ns": started_ns,
                    "ended_ns": max(started_ns + 1, ended_ns),
                }
            # Hold the Win32 source handle from before either original
            # dependent Bash/script call until after both have completed and
            # their shared seed's bytes and identity have been rechecked.
            with (protect_windows_seed_readonly(seed)
                  if seed_followup_workers == 2 else nullcontext()):
                if seed_followup_workers == 1:
                    followups = [observed_case(i) for i in (1, 2)]
                else:
                    # Two bridge invocations may overlap. This does NOT attest
                    # simultaneous Windows child processes or SDL focus safety.
                    with ThreadPoolExecutor(max_workers=2) as pool:
                        followups = list(pool.map(observed_case, (1, 2)))
                rows.extend(item[0] for item in followups)
                windows = [item[1] for item in followups]
                mode_receipt.update({
                    "effective_workers": seed_followup_workers,
                    "source_seed_sha256": seed_sha,
                    "invocation_windows": windows,
                    "invocation_overlap_ns": invocation_overlap_ns(windows),
                })
                require(seed.is_file() and not seed.is_symlink()
                        and seed.stat().st_size == 8192
                        and bridge.sha256_file(seed) == seed_sha,
                        "original baseline SRAM changed during Records")
                seed_after = seed.stat()
                require((seed_after.st_dev, seed_after.st_ino,
                         seed_after.st_size, seed_after.st_mtime_ns,
                         seed_after.st_ctime_ns) == seed_identity,
                        "original baseline SRAM identity changed during Records")
                if seed_followup_workers == 2:
                    require(mode_receipt["invocation_overlap_ns"] > 0,
                            "parallel Records bridge invocations did not overlap")
    else:
        for idx in GROUPS[group]:
            require("baseline/" not in commands[idx],
                    "supposedly independent journey depends on SRAM baseline")
        paths = [bridge.OUT_RE.findall(script) for script in commands]
        require(all(len(x) == 1 for x in paths)
                and all(x[0].startswith(paths[0][0] + "/") for x in paths[1:]),
                "original script roots changed")
        parent = Path(env["RUNNER_TEMP"]) / paths[0][0]
        require(not parent.exists() and not parent.is_symlink(), "work parent already used")
        parent.mkdir(parents=True)
        indices = [i for i in bridge.INDEPENDENT_PRIORITY if i in GROUPS[group]]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(lambda i: bridge.run_one(i, commands[i], work, env), indices))
    require(candidate_identity(source_sha, bridge.EXE, bridge.FIXTURE, archive) == who,
            "candidate changed during original scripts")
    rows.sort(key=lambda row: row["index"])
    for row in rows:
        row["script_sha256"] = original_hashes[row["index"]]
    attest_private_case_files(rows, work)
    practice_passed = (group == "independent" and
                       next(row for row in rows if row["index"] == 12)["exit_code"] == 0)
    mode = (practice_report_witness(commands, env, who, selected)
            if practice_passed else
            {"requested_workers": selected, "reported_workers": None,
             "report_sha256": None, "report_cases": None})
    report = {
        "schema": SCHEMA, "group": group, "candidate_identity": who,
        "practice_mode": mode, "seed_followup_mode": mode_receipt,
        "expected_indices": list(GROUPS[group]), "cases": rows,
        "all_passed": len(rows) == len(GROUPS[group]) and all(row["exit_code"] == 0 for row in rows),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "release_gate_credit": 0, "independent_physical_qa": False,
    }
    report["receipt_sha256"] = digest(report)
    (work / "result.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def summarize_case_failures(group, rows):
    """Public, bounded failure identifiers only; never private guest logs."""
    expected = GROUPS[group]
    by_index = {row["index"]: row for row in rows}
    return [
        {"group": group, "index": index, "name": bridge.STEPS[index],
         "reason": "missing_case" if index not in by_index else "nonzero_exit",
         "exit_code": None if index not in by_index else by_index[index]["exit_code"]}
        for index in expected
        if index not in by_index or by_index[index]["exit_code"] != 0
    ]


def aggregate(root, source_sha):
    problems, cases, identities, failures, modes, seed_modes = [], [], [], [], {}, {}
    for group in GROUPS:
        path = root / ("windows-fanout-" + group) / "result.json"
        try:
            require(path.is_file() and not path.is_symlink(), "missing group receipt")
            row = json.loads(path.read_text(encoding="utf-8"))
            identities.append(validate_receipt(row, group, source_sha))
            modes[group] = row["practice_mode"]
            seed_modes[group] = row["seed_followup_mode"]
            cases.extend(row["cases"])
            failures.extend(summarize_case_failures(group, row["cases"]))
            if not row["all_passed"]:
                problems.append(group + ": " + str(len(summarize_case_failures(group, row["cases"]))) +
                                " failed/missing original Windows journeys")
        except (OSError, ValueError, TypeError, KeyError) as error:
            problems.append(group + ": " + str(error))
    if len(identities) == 2 and identities[0] != identities[1]:
        problems.append("different source/EXE/fixture/ZIP identities across groups")
    if len(modes) == 2 and (modes["seed-dependent"]["requested_workers"] !=
                            modes["independent"]["requested_workers"]):
        problems.append("Practice selected worker mode differs across group receipts")
    indices = [row["index"] for row in cases]
    if sorted(indices) != list(range(13)):
        problems.append("original thirteen-journey inventory incomplete or duplicated")
    return {
        "schema": AGGREGATE_SCHEMA,
        "source_sha": source_sha, "candidate_identity": identities[0] if identities else None,
        "practice_mode": modes.get("independent") if len(modes) == 2 else None,
        "seed_followup_mode": (seed_modes.get("seed-dependent")
                               if len(seed_modes) == 2 else None),
        "native_records_process_overlap_qualified": False,
        "cases": sorted(({"index": row["index"], "exit_code": row["exit_code"],
                          "script_sha256": row["script_sha256"],
                          "elapsed_seconds": row["elapsed_seconds"],
                          "log_sha256": row["log_sha256"],
                          "log_bytes": row["log_bytes"],
                          "summary_sha256": row["summary_sha256"],
                          "summary_bytes": row["summary_bytes"]} for row in cases),
                        key=lambda x: x["index"]),
        "observed_cases": len(indices), "expected_cases": 13,
        "failed_cases": sorted(failures, key=lambda x: x["index"]),
        "transport_complete": not problems, "issues": problems,
        "release_gate_credit": 0, "independent_physical_qa": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    run = commands.add_parser("run")
    run.add_argument("--group", choices=tuple(GROUPS), required=True)
    run.add_argument("--source-sha", required=True)
    run.add_argument("--archive", type=Path, required=True)
    run.add_argument("--work", type=Path, required=True)
    # Engineering-only opt-in. No existing hosted Actions workflow activates it.
    run.add_argument("--seed-followup-workers", type=int,
                     choices=(1, 2), default=1)
    agg = commands.add_parser("aggregate")
    agg.add_argument("--source-sha", required=True)
    agg.add_argument("--results", type=Path, required=True)
    agg.add_argument("--out", type=Path, required=True)
    agg.add_argument("--summary", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        result = run_group(args.group, args.source_sha, args.archive, args.work,
                           seed_followup_workers=args.seed_followup_workers)
        print("original Windows journeys:", len(result["cases"]), "passed:", result["all_passed"])
        return 0 if result["all_passed"] else 1
    result = aggregate(args.results, args.source_sha)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as output:
            output.write("\n### Windows fan-out pilot\n\n")
            output.write("Original journeys: %s/13\n\n" % result["observed_cases"])
            output.write("Transport complete: %s. Release credit: 0.\n" % result["transport_complete"])
            for problem in result["issues"]:
                output.write("\n- " + problem)
            if result["failed_cases"]:
                output.write("\n\nFailed source journeys (index, step, exit):\n")
                for row in result["failed_cases"]:
                    output.write("\n- %02d %s: %s (%s)" %
                                 (row["index"], row["name"], row["reason"],
                                  row["exit_code"]))
    return 0 if result["transport_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
