#!/usr/bin/env python3
"""Manual QA-01 event campaign planner, per-case classifier, and final aggregator.

Transport/orchestration only. Original/native semantics stay in the existing
probe_original_event_complete.py, and RELEASE-QUALITY-LEDGER.json remains the
sole release-gate authority. Synthetic unit tests are not gameplay evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "ur-qa01-event-campaign/1"
CASES = {
    "zoom-zoo": {"course_id": "course:02", "family": "circuit-a"},
    "bowl": {"course_id": "course:03", "family": "stunt"},
    "switcher": {"course_id": "course:04", "family": "race-b"},
}
HEX256 = re.compile(r"^[0-9a-f]{64}$")


def canonical(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(data: object) -> str:
    return hashlib.sha256(canonical(data).encode("ascii")).hexdigest()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("expected JSON object")
    return obj


def make_plan(selection: str, source_sha: str) -> dict:
    if selection != "all" and selection not in CASES:
        raise ValueError("unknown case selection")
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("source revision must be an exact 40-character SHA-1")
    selected = list(CASES) if selection == "all" else [selection]
    body = {
        "schema": SCHEMA,
        "source_sha": source_sha,
        "selection": selection,
        "cases": [{"id": case, **CASES[case]} for case in selected],
        "matrix": {"include": [{"case": case} for case in selected]},
        "admission": "investigative only: zero automatic release/course credit",
    }
    body["plan_sha256"] = digest(body)
    return body


def validate_plan(plan: dict) -> None:
    if plan.get("schema") != SCHEMA:
        raise ValueError("invalid campaign schema")
    expected = make_plan(plan.get("selection", ""), plan.get("source_sha", ""))
    if plan != expected:
        raise ValueError("campaign plan modified or digest invalid")


def producer_failure_reason(producer_log: Path | None) -> str:
    """Expose the decisive bounded error, not the whole diagnostic/ROM log."""
    if producer_log is None:
        return ""
    try:
        lines = producer_log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    for line in reversed(lines[-200:]):
        line = line.strip()
        if ("CompleteEventError:" in line or
            "error while loading shared libraries:" in line or
            "ModuleNotFoundError:" in line or
            "subprocess.TimeoutExpired:" in line):
            return line[-260:]
    return ""


def classify(case: str, producer_rc: int, producer_path: Path,
             plan: dict, producer_log: Path | None = None) -> dict:
    validate_plan(plan)
    ids = [row["id"] for row in plan["cases"]]
    if case not in ids:
        raise ValueError("case not selected by plan")
    row = {
        "schema": SCHEMA,
        "plan_sha256": plan["plan_sha256"],
        "source_sha": plan["source_sha"],
        "case": case,
        "course_id": CASES[case]["course_id"],
        "family": CASES[case]["family"],
        "producer_exit_code": producer_rc,
        "disposition": "producer_error",
        "release_credit": 0,
        "reason": None,
        "evidence": {},
    }
    if producer_rc not in (0, 1):
        row["reason"] = "producer process failed, was killed, or timed out"
        detail = producer_failure_reason(producer_log)
        if detail:
            row["reason"] += ": " + detail
        return row
    try:
        report = load_json(producer_path)
        comparison = report["comparison"]
        event = report["original_source_event"]
        if not isinstance(comparison, dict) or not isinstance(event, dict):
            raise ValueError("missing original event or comparison")
        if report.get("schema_version") != 1 or report.get("name") != case:
            raise ValueError("wrong producer schema or case")
        if report.get("course_id") != CASES[case]["course_id"] or \
                report.get("family") != CASES[case]["family"]:
            raise ValueError("wrong course/family identity")
        if report.get("native_backend") != "pinned-baldosa":
            raise ValueError("not the pinned independent-original/native route")
        if report.get("admission") != "investigative candidate; not a release-ledger pass":
            raise ValueError("producer admission contract changed")
        keys = ("rom_sha256", "original_movie_sha256", "native_executable_sha256",
                "reference_core_sha256", "input_sha256", "source_sram_sha256",
                "original_movie_window_sha256", "reference_script_sha256")
        if any(not isinstance(report.get(key), str) or
               not HEX256.fullmatch(report[key]) for key in keys):
            raise ValueError("incomplete producer provenance")
        if any(type(event.get(k)) is not int or event[k] < 0
               for k in ("original_entry_frame", "original_result_frame",
                         "source_active_frames_to_result")) or (
                event["original_result_frame"] - event["original_entry_frame"]
                != event["source_active_frames_to_result"]) or (
                event["source_active_frames_to_result"] <= 0):
            raise ValueError("original archived event entry/result interval is incomplete or contradictory")
        if (any(type(report.get(k)) is not int or report[k] < 0
                for k in ("reference_entry", "native_entry", "native_frame_shift"))
                or report["native_entry"] - report["reference_entry"]
                != report["native_frame_shift"]):
            raise ValueError("fresh reference/native entry and input shift disagree")
        frames = comparison.get("terminal_result_guest_frame")
        if not isinstance(frames, dict) or any(type(frames.get(k)) is not int
               or frames[k] < 0 for k in ("reference_relative", "native_relative")):
            raise ValueError("terminal frame evidence missing")
        match = comparison.get("terminal_result_frame_matched")
        strict = comparison.get("paired_event_candidate")
        if type(match) is not bool or type(strict) is not bool:
            raise ValueError("strict comparator fields missing")
        if match != (frames["reference_relative"] == frames["native_relative"]):
            raise ValueError("contradictory terminal-frame assertion")
        if strict and (not match or producer_rc != 0):
            raise ValueError("strict outcome and producer exit disagree")
        if not strict and producer_rc == 0 and not comparison.get(
                "diagnostic_exit_success_without_full_event_parity", False):
            raise ValueError("non-strict result returned success without diagnostic contract")
        row["disposition"] = "strict_candidate" if strict else "strict_divergence"
        row["reason"] = ("strict paired-event candidate; NOT an independently "
                         "adjudicated course pass" if strict else
                         "strict original/native paired-event comparator is negative")
        row["evidence"] = {
            "producer_sha256": hashlib.sha256(producer_path.read_bytes()).hexdigest(),
            "rom_sha256": report["rom_sha256"],
            "movie_sha256": report["original_movie_sha256"],
            "core_sha256": report["reference_core_sha256"],
            "native_sha256": report["native_executable_sha256"],
            "input_sha256": report["input_sha256"],
            "source_sram_sha256": report["source_sram_sha256"],
            "original_movie_window_sha256": report["original_movie_window_sha256"],
            "reference_script_sha256": report["reference_script_sha256"],
            "original_movie_entry_frame": event["original_entry_frame"],
            "original_movie_result_frame": event["original_result_frame"],
            "reference_entry_frame": report["reference_entry"],
            "native_entry_frame": report["native_entry"],
            "native_frame_shift": report["native_frame_shift"],
            "original_event_frames": event["source_active_frames_to_result"],
            "terminal_guest_relative_frames": frames,
            "terminal_frame_matched": match,
            "strict_candidate": strict,
            "first_sample_disagreement": comparison.get("first_sample_disagreement"),
        }
    except (OSError, ValueError, KeyError, TypeError) as exc:
        row["reason"] = "invalid/missing producer evidence: " + str(exc)
        detail = producer_failure_reason(producer_log)
        if detail:
            row["reason"] += "; cause: " + detail
    return row


def aggregate(plan: dict, results_dir: Path) -> tuple[dict, str]:
    validate_plan(plan)
    results = []
    expected = {row["id"] for row in plan["cases"]}
    unexpected = []
    for path in sorted(results_dir.glob("qa01-campaign-case-*/case-result.json")):
        case_dir = path.parent.name
        if case_dir.removeprefix("qa01-campaign-case-") not in expected:
            unexpected.append(case_dir)
    for case in [row["id"] for row in plan["cases"]]:
        path = results_dir / ("qa01-campaign-case-" + case) / "case-result.json"
        try:
            row = load_json(path)
            if (row.get("schema") != SCHEMA or row.get("case") != case or
                row.get("course_id") != CASES[case]["course_id"] or
                row.get("source_sha") != plan["source_sha"] or
                row.get("plan_sha256") != plan["plan_sha256"] or
                type(row.get("release_credit")) is not int or
                row.get("release_credit") != 0 or
                row.get("disposition") not in
                    ("strict_candidate", "strict_divergence", "producer_error")):
                raise ValueError("case identity, schema or status mismatch")
            if row["disposition"] != "producer_error":
                ev = row.get("evidence")
                if not isinstance(ev, dict) or any(
                    not isinstance(ev.get(k), str) or
                    not HEX256.fullmatch(ev[k]) for k in (
                        "producer_sha256", "rom_sha256", "movie_sha256",
                        "core_sha256", "native_sha256", "input_sha256",
                        "source_sram_sha256", "original_movie_window_sha256",
                        "reference_script_sha256")
                ):
                    raise ValueError("incomplete case hash provenance")
                if (any(type(ev.get(k)) is not int or ev[k] < 0
                        for k in ("original_movie_entry_frame",
                                  "original_movie_result_frame",
                                  "original_event_frames",
                                  "reference_entry_frame", "native_entry_frame",
                                  "native_frame_shift"))
                        or ev["original_movie_result_frame"] - ev["original_movie_entry_frame"]
                        != ev["original_event_frames"]
                        or ev["original_event_frames"] <= 0
                        or ev["native_entry_frame"] - ev["reference_entry_frame"]
                        != ev["native_frame_shift"]):
                    raise ValueError("case original/native start and shift identity inconsistent")
                frames = ev.get("terminal_guest_relative_frames")
                if not isinstance(frames, dict) or any(
                    type(frames.get(k)) is not int or frames[k] < 0 for k in
                    ("reference_relative", "native_relative")
                ):
                    raise ValueError("case terminal frame evidence invalid")
                match = frames["reference_relative"] == frames["native_relative"]
                if (type(ev.get("terminal_frame_matched")) is not bool or
                    ev["terminal_frame_matched"] != match or
                    type(ev.get("strict_candidate")) is not bool or
                    ev["strict_candidate"] != (row["disposition"] == "strict_candidate") or
                    (row["disposition"] == "strict_candidate" and
                     (not match or row.get("producer_exit_code") != 0))):
                    raise ValueError("contradictory strict candidate receipt")
            if row["disposition"] == "producer_error":
                row["reason"] = str(row.get("reason") or "producer error")
        except (OSError, ValueError, TypeError) as exc:
            row = {
                "case": case, "course_id": CASES[case]["course_id"],
                "disposition": "missing_evidence",
                "reason": str(exc), "release_credit": 0,
            }
        results.append(row)
    # The embedded SRAM also comes from the same archived source movie:
    # cross-shard source boot differences invalidate a pooled experiment.
    # Event-relative input windows/scripts and native entry offsets vary.
    identity_keys = ("rom_sha256", "movie_sha256", "core_sha256",
                     "native_sha256", "source_sram_sha256")
    baseline = None
    for row in results:
        if row["disposition"] not in ("strict_candidate", "strict_divergence"):
            continue
        identity = tuple(row["evidence"][key] for key in identity_keys)
        if baseline is None:
            baseline = identity
        elif identity != baseline:
            row["disposition"] = "missing_evidence"
            row["reason"] = "cross-case ROM/movie/reference/native identity mismatch"
            row["release_credit"] = 0
    totals = {
        key: sum(row["disposition"] == key for row in results)
        for key in ("strict_candidate", "strict_divergence",
                    "producer_error", "missing_evidence")
    }
    valid = (not unexpected and
             totals["producer_error"] == 0 and totals["missing_evidence"] == 0)
    report = {
        "schema": SCHEMA, "plan_sha256": plan["plan_sha256"],
        "source_sha": plan["source_sha"], "selected_cases": len(expected),
        "completed": totals["strict_candidate"] + totals["strict_divergence"],
        "counts": totals, "unexpected_artifacts": unexpected,
        "transport_complete": valid, "release_admissions": 0,
        "results": results,
        "release_note": ("All observations are investigative. Independent QA "
                         "adjudication and the release ledger remain unchanged."),
    }
    lines = [
        "# QA-01 unattended event campaign",
        "",
        "Source SHA: " + plan["source_sha"],
        "Plan SHA-256: " + plan["plan_sha256"],
        "",
        "| Case | Outcome | Evidence |",
        "| --- | --- | --- |",
    ]
    for row in results:
        lines.append("| " + row["case"] + " | " + row["disposition"] +
                     " | " + str(row.get("reason") or "").replace("|", "/")[:160] + " |")
    lines += [
        "",
        "Completed investigative cases: " + str(report["completed"]) +
        "/" + str(len(expected)),
        "Missing/error: " + str(totals["missing_evidence"] +
                               totals["producer_error"]),
        "Transport complete: " + str(valid),
        "**USA course release admissions: 0.** A strict candidate is not a reviewed L4 pass.",
        "Physical Windows or player-hardware evidence: not exercised.",
    ]
    return report, "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="mode", required=True)
    make = sub.add_parser("plan")
    make.add_argument("--selected", choices=["all", *CASES], default="all")
    make.add_argument("--source-sha", required=True)
    make.add_argument("--out", required=True, type=Path)
    make.add_argument("--gha-output", type=Path)
    make.add_argument("--summary", type=Path)
    check = sub.add_parser("classify")
    check.add_argument("--plan", required=True, type=Path)
    check.add_argument("--case", required=True, choices=list(CASES))
    check.add_argument("--producer-exit", required=True, type=int)
    check.add_argument("--producer-report", required=True, type=Path)
    check.add_argument("--producer-log", type=Path)
    check.add_argument("--out", required=True, type=Path)
    agg = sub.add_parser("aggregate")
    agg.add_argument("--plan", required=True, type=Path)
    agg.add_argument("--results-dir", required=True, type=Path)
    agg.add_argument("--out", required=True, type=Path)
    agg.add_argument("--summary", required=True, type=Path)
    args = p.parse_args(argv)
    if args.mode == "plan":
        plan = make_plan(args.selected, args.source_sha)
        write_json(args.out, plan)
        if args.gha_output:
            with args.gha_output.open("a", encoding="utf-8") as fh:
                fh.write("matrix=" + canonical(plan["matrix"]) + "\n")
        if args.summary:
            args.summary.write_text(
                "# QA-01 campaign plan\n\n" +
                "Selected: " + ", ".join(row["id"] for row in plan["cases"]) +
                "\n\nSHA: " + plan["plan_sha256"] +
                "\n\nManual investigative execution only. No automatic course credit.\n",
                encoding="utf-8")
        return 0
    plan = load_json(args.plan)
    if args.mode == "classify":
        row = classify(args.case, args.producer_exit,
                       args.producer_report, plan, args.producer_log)
        write_json(args.out, row)
        # A failed producer is a failed case job. Artifacts and aggregate
        # still run, but a valid scientific strict divergence is not a
        # CI infrastructure failure.
        return 1 if row["disposition"] == "producer_error" else 0
    report, summary = aggregate(plan, args.results_dir)
    write_json(args.out, report)
    args.summary.write_text(summary, encoding="utf-8")
    return 0 if report["transport_complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
