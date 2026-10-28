#!/usr/bin/env python3
"""Read-only intake triage for one offline Windows H01-H07 tester report.

Valid format != genuine physical observation, independently inspected evidence
or authorized v2/release admission. No ROM, guest runner, file upload or source
candidate mutation occurs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RECORDER = ROOT / "docs/playtest/windows-h01-h07-offline.html"
SCHEMA = "ur-recomp-offline-physical-playtest-h01-h07/1"
H_IDS = tuple(f"H{i:02}" for i in range(1, 8))
STATUSES = frozenset({"PASS", "FAIL", "BLOCKED", "NOT_RUN"})
PLATFORMS = frozenset({"physical_pc", "virtual_machine", "hosted_runner", "unspecified"})
HASH_STATES = frozenset({"yes", "no", "not_checked"})
ENV_FIELDS = ("setup", "platform", "windows", "gpu", "monitor",
              "controllers", "audio", "launcher", "hashCheck")
MAX_REPORT_BYTES = 65536
MAX_TEXT = {"setup": 32, "platform": 32, "windows": 100, "gpu": 100,
            "monitor": 100, "controllers": 120, "audio": 100,
            "launcher": 90, "hashCheck": 32}
TOP_FIELDS = frozenset({
    "schema", "authority", "candidate", "observed_at_utc",
    "environment", "results", "independent_qa_review",
    "official_release_gates_accepted_by_this_report",
    "complete_usa_events_accepted_by_this_report", "warning",
})


def require(ok, why):
    if not ok:
        raise ValueError("INVALID_PHYSICAL_INTAKE: " + why)


def source_pins(html: str) -> dict:
    """Extract the *single fixed* candidate object from tracked UI source."""
    match = re.search(r"const candidate = Object\.freeze\(\{(.*?)\}\);", html, re.S)
    require(match is not None and len(match.group(1)) < 1024,
            "canonical recorder candidate missing or altered")
    block = match.group(1)
    required = {
        "producing_run": r"producing_run:\s*(\d+)",
        "artifact_id": r"artifact_id:\s*(\d+)",
        "source_sha": r'source_sha:\s*"([a-f0-9]{40})"',
        "inner_zip_sha256": r'inner_zip_sha256:\s*"([a-f0-9]{64})"',
        "executable_sha256": r'executable_sha256:\s*"([a-f0-9]{64})"',
    }
    values = {}
    for key, pattern in required.items():
        found = re.findall(pattern, block)
        require(len(found) == 1, "ambiguous recorder candidate field " + key)
        values[key] = int(found[0]) if key in ("producing_run", "artifact_id") else found[0]
    return values


def checked_text(x, maxlen, label):
    require(type(x) is str and len(x) <= maxlen and not any(
        ord(ch) < 32 or ord(ch) == 127 for ch in x), "invalid string " + label)
    return x


def validate(report: dict, *, pins: dict) -> dict:
    require(type(report) is dict and set(report) == TOP_FIELDS,
            "unexpected top-level report schema/keys")
    require(report["schema"] == SCHEMA, "wrong report schema")
    require(report["authority"] == "unreviewed_tester_observations_zero_release_credit",
            "wrong reporter authority")
    require(type(report["candidate"]) is dict and report["candidate"] == pins,
            "candidate differs from source-pinned physical recorder")
    require(report["independent_qa_review"] == "PENDING",
            "tester must not declare independent QA review")
    require(type(report["official_release_gates_accepted_by_this_report"]) is int
            and report["official_release_gates_accepted_by_this_report"] == 0
            and type(report["complete_usa_events_accepted_by_this_report"]) is int
            and report["complete_usa_events_accepted_by_this_report"] == 0,
            "report cannot award a release gate or original USA event")
    checked_text(report["warning"], 500, "warning")
    stamp = checked_text(report["observed_at_utc"], 40, "UTC capture stamp")
    require(stamp.endswith("Z"), "observations must have UTC timestamp")
    try:
        observed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_PHYSICAL_INTAKE: malformed UTC timestamp") from exc
    require(observed.tzinfo is not None
            and datetime(2000, 1, 1, tzinfo=timezone.utc) <= observed
            <= datetime.now(timezone.utc).replace(microsecond=999999),
            "impossible or future timestamp")

    env = report["environment"]
    require(type(env) is dict and set(env) == set(ENV_FIELDS),
            "unknown/missing environment fields")
    for key in ENV_FIELDS:
        checked_text(env[key], MAX_TEXT[key], "environment." + key)
    require(env["platform"] in PLATFORMS and env["hashCheck"] in HASH_STATES,
            "unsupported environment or hash-verification state")
    rows = report["results"]
    require(type(rows) is list and len(rows) == len(H_IDS),
            "not exactly seven source-pinned journeys")
    outcome = {}
    need_review = []
    for idx, row in enumerate(rows):
        expected = H_IDS[idx]
        require(type(row) is dict
                and set(row) == {"id", "title", "criteria_label",
                                 "status", "notes", "evidence"}
                and row["id"] == expected,
                "missing/duplicated/out-of-order journey " + expected)
        checked_text(row["title"], 100, expected + ".title")
        checked_text(row["criteria_label"], 120, expected + ".criteria_label")
        require(row["status"] in STATUSES, "unsupported " + expected + " status")
        checked_text(row["notes"], 1200, expected + ".notes")
        evidence = checked_text(row["evidence"], 240, expected + ".evidence")
        require("/" not in evidence and "\\" not in evidence,
                expected + " evidence must be redacted filename labels, not paths")
        outcome[expected] = row["status"]
        if row["status"] in {"FAIL", "BLOCKED"}:
            need_review.append(expected + " observed " + row["status"]
                               + ": independent reproduction and product triage needed")
        if row["status"] == "PASS" and not row["notes"].strip():
            need_review.append(expected + " PASS has no observation narrative")
    if env["hashCheck"] != "yes":
        need_review.insert(0, "local inner ZIP/EXE SHA-256 not independently confirmed: "
                           + env["hashCheck"])
    if env["platform"] != "physical_pc":
        need_review.append("environment is not a confirmed physical Windows PC")
    if outcome["H04"] == "PASS" and env["platform"] != "physical_pc":
        need_review.append("H04 cannot prove physical two-pad functionality here")
    if outcome["H06"] == "PASS" and not env["audio"].strip():
        need_review.append("H06 PASS lacks actual audible output description")
    return {
        "schema": "ur-recomp-physical-intake-triage/1",
        "source_candidate_sha": pins["source_sha"],
        "reported_at_utc": stamp,
        "format_valid": True,
        "local_inner_zip_exe_hashes_confirmed_by_tester": env["hashCheck"] == "yes",
        "physical_pc_claimed": env["platform"] == "physical_pc",
        "outcomes": outcome,
        "counts": dict(sorted(Counter(outcome.values()).items())),
        "triage": need_review,
        "independent_qa_accepted": False,
        "release_gates_admitted": 0,
        "complete_original_native_usa_events_admitted": 0,
        "disclaimer": ("Valid reporter format and source metadata are not authenticated "
                       "physical witnesses, source/PE/ZIP byte verification, "
                       "full criterion acceptance or QA-04 three-machine coverage."),
    }


def read_report(path: Path):
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_size <= MAX_REPORT_BYTES, "missing, redirected or oversized report")
    try:
        return json.loads(path.read_text(encoding="utf-8"),
                          parse_constant=lambda c: (_ for _ in ()).throw(
                              ValueError("nonfinite JSON constant: " + c)))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("INVALID_PHYSICAL_INTAKE: malformed JSON") from exc


def markdown(result: dict) -> str:
    rows = [
        "# Windows H01-H07 intake: formatting and reviewer prompts only",
        "", "**Source candidate:** `" + result["source_candidate_sha"] + "`",
        "**Reported UTC:** " + result["reported_at_utc"],
        "**Local ZIP and EXE hashes confirmed by tester:** "
        + str(result["local_inner_zip_exe_hashes_confirmed_by_tester"]),
        "**Physical PC claimed:** " + str(result["physical_pc_claimed"]),
        "", "| Case | Tester-reported status |", "|---|---|",
    ]
    for key, status in result["outcomes"].items():
        rows.append("| " + key + " | " + status + " |")
    rows += ["", "## Independent reviewer follow-ups", ""]
    rows.extend("- " + item for item in result["triage"])
    if not result["triage"]:
        rows.append("No formatting-level follow-ups. Independently audit actual evidence.")
    rows += ["", "**0/12 release gates and 0/45 authentic USA events "
             "admitted by this intake. Independent QA is still PENDING.**",
             "", result["disclaimer"], ""]
    return "\n".join(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("report", type=Path, help="saved local JSON from offline H01-H07 recorder")
    p.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = p.parse_args()
    data = read_report(args.report)
    pins = source_pins(RECORDER.read_text(encoding="utf-8"))
    result = validate(data, pins=pins)
    print(json.dumps(result, sort_keys=True, indent=2) if args.format == "json"
          else markdown(result), end="\n")


if __name__ == "__main__":
    main()
