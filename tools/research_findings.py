#!/usr/bin/env python3
"""Validate and render the evidence-driven research findings register.

``analysis/data/research-findings-register.json`` turns research outputs into
a work queue. Each finding is classified by its *practical significance*, not
by how much computation produced it, and names its exact reproducer, source
artifacts, remaining uncertainty, owning implementation lane and the single
experiment that would resolve that uncertainty.

The register is a triage instrument. It never grants release credit, never
changes the strict comparator, and never upgrades a finding's class on its
own: an ``original_native_discrepancy`` requires an original-emulator
reproduction, and ``fingerprint_novelty`` can never be actionable.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "analysis/data/research-findings-register.json"
SCHEMA = "ur-research-findings-register/1"

# Ordered by decision value: a lower rank is triaged first.
CLASSES = {
    "original_native_discrepancy": "independently reproducible original/native difference",
    "source_backed_behaviour": "source- or original-backed state transition / behaviour",
    "untested_circumstance": "gameplay circumstance no oracle has exercised yet",
    "graphics_observation_gap": "graphics/PPU fact the current observers cannot see",
    "windows_durability": "Windows durability / recovery defect or bound",
    "reproducible_anomaly": "reproducible but unexplained research observation",
    "method_hazard": "experimental design error that would mislead a consumer",
    "fingerprint_novelty": "native fingerprint novelty without a shown consequence",
}
STATUSES = ("open", "handed_off", "resolved", "retired")
LANES = ("research", "qa01-gameplay", "qa08-graphics", "windows-modern",
         "release-qa", "ci", "none")
EVIDENCE = ("native_only", "original_only", "original_and_native",
            "source_static", "synthetic")
ID = re.compile(r"^RF-\d{3}$")
RUN = re.compile(r"^\d{8,12}$")
REQUIRED = ("id", "title", "class", "status", "evidence", "owner_lane",
            "reproducer", "source_artifacts", "uncertainty",
            "resolving_experiment", "consequence")


def validate(register: dict) -> list[dict]:
    if register.get("schema") != SCHEMA:
        raise ValueError("not a research findings register")
    if register.get("release_gate_credit") != 0:
        raise ValueError("the findings register never grants release credit")
    findings = register.get("findings")
    if not isinstance(findings, list) or not findings:
        raise ValueError("register has no findings")
    seen = set()
    for f in findings:
        missing = [k for k in REQUIRED if k not in f]
        if missing:
            raise ValueError(f"{f.get('id')}: missing {missing}")
        fid = f["id"]
        if not ID.match(fid) or fid in seen:
            raise ValueError(f"invalid or duplicate finding id {fid}")
        seen.add(fid)
        if f["class"] not in CLASSES:
            raise ValueError(f"{fid}: unknown class {f['class']}")
        if f["status"] not in STATUSES:
            raise ValueError(f"{fid}: unknown status {f['status']}")
        if f["owner_lane"] not in LANES:
            raise ValueError(f"{fid}: unknown owner lane {f['owner_lane']}")
        if f["evidence"] not in EVIDENCE:
            raise ValueError(f"{fid}: unknown evidence level {f['evidence']}")
        rep = f["reproducer"]
        if not isinstance(rep, dict) or not rep.get("command"):
            raise ValueError(f"{fid}: a finding needs an exact reproducer command")
        for run in rep.get("runs", []):
            if not RUN.match(str(run)):
                raise ValueError(f"{fid}: malformed Actions run id {run}")
        if not f["source_artifacts"]:
            raise ValueError(f"{fid}: no source artifacts")
        if f["class"] == "original_native_discrepancy":
            if f["evidence"] != "original_and_native":
                raise ValueError(f"{fid}: a discrepancy needs original AND native evidence")
            if "race_relative_lag" not in rep:
                raise ValueError(f"{fid}: a discrepancy must declare its race-relative alignment")
        if f["class"] == "fingerprint_novelty":
            if f["owner_lane"] != "none" or f["status"] == "open":
                raise ValueError(f"{fid}: fingerprint novelty alone is never an open assignment")
        if f["status"] in ("resolved", "retired") and not f.get("resolution"):
            raise ValueError(f"{fid}: a closed finding records its resolution")
        if f["status"] == "handed_off" and f["owner_lane"] in ("research", "none"):
            raise ValueError(f"{fid}: a handoff names the receiving implementation lane")
    return findings


def queue(findings: list[dict]) -> list[dict]:
    """Actionable findings, most decision-relevant class first."""
    rank = {c: i for i, c in enumerate(CLASSES)}
    live = [f for f in findings if f["status"] in ("open", "handed_off")]
    return sorted(live, key=lambda f: (rank[f["class"]], f["id"]))


def render(findings: list[dict]) -> str:
    rows = ["| ID | Class | Status | Owner | Finding | Resolving experiment |",
            "| --- | --- | --- | --- | --- | --- |"]
    for f in queue(findings):
        rows.append(f"| {f['id']} | {f['class']} | {f['status']} | {f['owner_lane']} "
                    f"| {f['title']} | {f['resolving_experiment']} |")
    return "\n".join(rows) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--register", type=Path, default=REGISTER)
    ap.add_argument("--queue", action="store_true", help="print the actionable queue")
    args = ap.parse_args()
    findings = validate(json.loads(args.register.read_text(encoding="utf-8")))
    if args.queue:
        sys.stdout.write(render(findings))
    else:
        print(f"{len(findings)} findings valid; {len(queue(findings))} actionable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
