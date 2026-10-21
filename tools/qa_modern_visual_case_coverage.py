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
def reconcile(matrix: dict, evidence: dict) -> dict:
    cases = matrix.get("cases")
    captures = evidence.get("cases")
    if not isinstance(cases, list) or not isinstance(captures, list):
        raise ValueError("matrix/evidence cases missing")
    if len(cases) != 25 or len({x.get("id") for x in cases}) != 25:
        raise ValueError("not the 25 canonical distinct cases")
    if len(captures) != 21 or any(
            x.get("actual_native_P7_png_RGBA_byte_equal") is not True or
            x.get("successful_native_log_hash_verified") is not True
            for x in captures):
        raise ValueError("not the qualified 21-case original SDL cohort")
    if evidence.get("counts",{}).get("lossless_exact_RGBA_matches") != 21:
        raise ValueError("source-native capture count mismatch")
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
