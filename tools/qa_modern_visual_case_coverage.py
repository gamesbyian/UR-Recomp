#!/usr/bin/env python3
"""Reconcile the 25 Modern visual requirements against retained native evidence.

Never convert a real screenshot, CI green, or semantic-route label into human,
hardware, source-equivalent, or full acceptance. Output is an *audit ledger*,
not a release-quality ledger. Only exact geometry plus a consciously bounded
route/state correspondence can qualify as an acceptance candidate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CASE_MAP = {
    # Target id: (original full SDL route, original output pixels, claim limit)
    "title-reduced-motion": ("title-intro-reduced", [1280, 720],
                             "reduced-motion flag, real title source/FNV and final SDL at requested size; keyboard/hardware not tested"),
    "root-wide-720": ("root-quit", [1280, 720],
                      "normal native root geometry and final SDL; aesthetic/focus signoff absent"),
    "root-43-768": ("root-quit", [1024, 768],
                     "genuine compact 256px source/root and final SDL; aesthetic signoff absent"),
    "profile-first-run": ("profile-first-p1", [1280, 720],
                          "P1 no-profile/first racer creation; saved-next-process restore not established"),
    "options-available": ("options-p1", [1024, 768],
                           "P1 Options with changed DISPLAY resulting in 1024x768; normal initial state may differ"),
}
PARTIAL = {
    "title-wide-keyboard": "title at 1280x720 captured, but actual input owner is native P1, not keyboard",
    "title-compact-43": "native 256px source title captured at 1024x768, not required 640x480",
    "root-keyboard": "root at 1280x720 captured, but keyboard entry is not source-proven in this cohort",
    "root-disabled": "no-profile identity captured, but stale-profile disabled interaction is not demonstrated",
    "multiplayer-p2-owner": "unbound warning at 1280x720, not a named independent P2 join",
    "practice-locked": "Practice picker at 1280x720, but locked-course state is not demonstrated",
    "records-empty": "Records at 1280x720 via keyboard; acceptance calls for P1 pad",
    "transition-back-release": "native P1 title→root captured; held-confirm/back edge release not tested",
    "authentic-stock-wide": "original stock RGB at 1280x720 preserved; physical pad and source CRC oracle not established",
}
# This consumer names one frozen historical run. New native captures need a new
# independently verified cohort/contract, not an edited old manifest claiming
# to be the same 21 screenshots.
FROZEN_RUN_ID = 39536021531
FROZEN_CHECKOUT_SHA = "44c192d9c43e69068461f5d524b50a9d097ca907"
FROZEN_PE_SHA256 = "b36b76f5c15f225fd69351e83d6969fcebabab3b033f3250c60f01ccefce9cad"
CANONICAL_CASE_IDS = frozenset({
    "title-wide-1080", "title-wide-keyboard", "title-compact-43",
    "title-reduced-motion", "root-wide-720", "root-wide-1080",
    "root-wide-4k-virtual", "root-43-768", "root-43-480",
    "root-moved-selection", "root-keyboard", "root-disabled",
    "profile-first-run", "profile-switch-existing", "multiplayer-p2-owner",
    "practice-locked", "options-available", "options-refused",
    "records-empty", "records-earned-1p", "records-earned-2p",
    "transition-back-release", "authentic-title-stock",
    "authentic-stock-wide", "focus-loss-modal",
})
# Exact input/state interpretation for the five close technical candidates,
# deliberately not inferred from any other captured route.
CANDIDATE_REQUIREMENTS = {
    "title-reduced-motion": ("title", "modern", "16:9", "pad-p1", "reduced-motion"),
    "root-wide-720": ("root", "modern", "16:9", "pad-p1", "normal"),
    "root-43-768": ("root", "modern", "4:3", "pad-p1", "normal"),
    "profile-first-run": ("profiles", "modern", "16:9", "pad-p1", "no-profile"),
    "options-available": ("options", "modern", "4:3", "pad-p1", "normal"),
}


def validate_frozen_cohort(matrix: dict, evidence: dict) -> tuple[list, list]:
    """Refuse substituted source/PE, omitted capture flags or a rewritten case.

    The source flags are independently reported observations, not raw P7
    verification. Original Actions ZIP bytes must still be audited with
    qa_modern_visual_actions_archive.py before this summary can be trusted.
    """
    cases = matrix.get("cases")
    captures = evidence.get("cases")
    if not isinstance(cases, list) or not isinstance(captures, list):
        raise ValueError("matrix/evidence cases missing")
    if (len(cases) != 25 or not all(isinstance(x, dict) for x in cases)
            or {x.get("id") for x in cases} != CANONICAL_CASE_IDS):
        raise ValueError("not the 25 canonical distinct cases")
    run = evidence.get("run")
    if (evidence.get("schema_version") != 1 or not isinstance(run, dict)
            or run.get("id") != FROZEN_RUN_ID
            or run.get("merge_checkout_sha") != FROZEN_CHECKOUT_SHA
            or run.get("win32_conclusion") != "success"
            or not isinstance(run.get("executable"), dict)
            or run["executable"].get("sha256") != FROZEN_PE_SHA256
            or run["executable"].get("architecture") != "AMD64 PE32+"):
        raise ValueError("unqualified historical source/PE/run identity")
    counts = evidence.get("counts")
    if (not isinstance(counts, dict)
            or counts.get("original_native_capture_receipts") != 21
            or counts.get("lossless_exact_RGBA_matches") != 21
            or counts.get("successful_process_logs") != 21
            or counts.get("actual_human_visual_signoffs") != 0
            or counts.get("release_gate_credit") != 0):
        raise ValueError("source-native capture count/approval mismatch")
    if (len(captures) != 21 or not all(isinstance(x, dict) for x in captures)
            or any(x.get(field) is not True for x in captures for field in (
                "actual_native_P7_png_RGBA_byte_equal",
                "successful_native_log_hash_verified",
                "source_sha_exact", "exe_sha_exact"))):
        raise ValueError("not the qualified 21-case source/PE-bound SDL cohort")
    ids = [x.get("id") for x in captures]
    if (any(not isinstance(x, str) or not x for x in ids)
            or len(set(ids)) != 21):
        raise ValueError("duplicate or missing original capture ID")
    for case in cases:
        if case["id"] in CANDIDATE_REQUIREMENTS:
            expected = CANDIDATE_REQUIREMENTS[case["id"]]
            actual = tuple(case.get(k) for k in (
                "screen", "mode", "aspect", "input", "state"))
            if actual != expected:
                raise ValueError("technical candidate's matrix state/owner was rewritten: " + case["id"])
    return cases, captures


def reconcile(matrix: dict, evidence: dict) -> dict:
    cases, captures = validate_frozen_cohort(matrix, evidence)
    if set(CASE_MAP) - {x["id"] for x in cases} or set(PARTIAL) - {x["id"] for x in cases}:
        raise ValueError("mapping references noncanonical acceptance cases")
    rows = []
    for case in cases:
        cid = case["id"]
        row = {"id":cid,"required_pixels":case["pixels"],
               "required_input":case["input"],"required_state":case["state"],
               "technical_candidate":False,"formal_visual_accepted":False,
               "human_approved":False,"hardware_approved":False,
               "release_gate_credit":0}
        if cid in CASE_MAP:
            route,pixels,limit=CASE_MAP[cid]
            matches=[x for x in captures
                     if x["route"]==route and
                        x["output"]==f"{pixels[0]}x{pixels[1]}"]
            if not matches or pixels!=case["pixels"]:
                raise ValueError(f"technical candidate has no exact evidence: {cid}")
            row.update(technical_candidate=True,source_route=route,
                       source_capture_ids=[x["id"] for x in matches],
                       limitation=limit)
        elif cid in PARTIAL:
            row.update(related_evidence_only=True,limitation=PARTIAL[cid])
        else:
            row.update(matching_technical_capture=False,
                       limitation="no matching source-native final SDL output and state/owner in this cohort")
        rows.append(row)
    return {
        "schema_version":1,
        "purpose":"technical acceptance matrix gap map, NEVER visual approval",
        "source_run_id":evidence["run"]["id"],
        "source_checkout":evidence["run"]["merge_checkout_sha"],
        "source_pe_sha256":evidence["run"]["executable"]["sha256"],
        "matrix_authority":matrix.get("authority"),
        "required_cases":25,
        "exact_geometry_route_technical_candidates":sum(x["technical_candidate"] for x in rows),
        "related_partial_evidence_only":sum(x.get("related_evidence_only",False) for x in rows),
        "remaining_without_corresponding_case_evidence":sum(
            not x["technical_candidate"] and not x.get("related_evidence_only",False)
            for x in rows),
        "formal_visual_accepted":0,
        "human_approved":False,"physical_device_approved":False,
        "release_gate_credit":0,
        "cases":rows,
    }
def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--matrix",type=Path,default=Path("analysis/modern-visual-acceptance-matrix.json"))
    ap.add_argument("--evidence",type=Path,default=Path("analysis/evidence/modern-visual-integrated-final-sdl-21cases-20261021.json"))
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    report=reconcile(json.loads(args.matrix.read_text()),
                     json.loads(args.evidence.read_text()))
    rendered=json.dumps(report,indent=2)+"\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.write_text(rendered)
    print(rendered)
    return 0
if __name__=="__main__":
    raise SystemExit(main())
