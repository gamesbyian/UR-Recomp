#!/usr/bin/env python3
"""Reconcile TWO immutable Windows native Modern title/menu evidence epochs.

Read-only acceptance consumer: historical SDL captures are never current-main
proof, and semantic input scripts are never physical P1/P2 controllers.
Optionally re-read original Actions capture and PE ZIPs rather than trusting
their SHA-bearing summaries. Never modifies the release ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import sys

# Work both as `python -m tools...` and as a direct path CLI on Windows.
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import qa_modern_visual_case_coverage as legacy
from tools import qa_modern_visual_actions_archive as archive

SOURCE = "a20790e92c66b58a1630ec084db6f78596296a05"
PE = "5a2d3475d598447509b6addad1b206de27e30ce59ec4a4d8c3b246a976a466a7"
RUN = 39539086749
ARTIFACT = 12319405071
EXE_ARTIFACT = 12318866939
OLD_KINDS = {
    "close_geometry_and_route_only": "close geometry and semantic route only",
    "related_only_not_exact_requirement": "related partial only",
}
STRICT = {
    "root-43-480": (
        "ur-integrated-viewport-root-quit-640x480", "root-quit", (640,480),
        (256,224), (8,10,240,204),
        "906e078e9b22334dacfa77a025cf55c296381ef40c42be91ae33c6f0cda39d53",
        "4e1c138cf578e2627136fc2a1533b72eff03c32b3e48ade71c1d08ba25386296",
        None, None),
    "root-wide-1080": (
        "ur-integrated-viewport-root-quit-1920x1080", "root-quit", (1920,1080),
        (342,224), (11,10,320,204),
        "f7b28ae3a60a1c6a5dcf3a3eabbac3e89fac19072c01407c7d5ba3e696540124",
        "dc14fa61c4ef32231e0dc6c450b68a2cc118ca1727d6e08ac0da00670bbdf68f",
        None, None),
    "title-compact-43": (
        "ur-integrated-viewport-title-intro-compact-640x480", "title-intro-compact",
        (640,480), (256,224), None,
        "2619b70646dfe3458479be8d597b1e38eb6496c3b8e430d62dc94cea875b4beb",
        "5248d87e4dbcd9cedd9f90fb27b67b5e1e6bb832d42821962c47eddfe7f86970",
        "3959250c9dc6466f291bcb4cc59636ee6f7cabec9e4eb0ea0c3162e3fdc186fe",
        "61672ac5a543f7e2"),
    "title-wide-1080": (
        "ur-integrated-viewport-title-intro-wide-1920x1080", "title-intro-wide",
        (1920,1080), (342,224), None,
        "93b8b2e21b66412153c3b3829263cedbd8b5fc151fec8f2d7887d8652bb4cc1d",
        "8e252b1b480ab944be5f7b0644f09fde60be490808bbface02afbaeed427c46b",
        "f2ad1e081018afe7ef67cf3cf6cb40edccd890785e7a863d815d7e319eeaf592",
        "087cbca7b8b04aca"),
}


def _identities(strict: dict) -> dict:
    source = strict.get("source")
    if (strict.get("schema_version") != 1 or not isinstance(source, dict) or
            source.get("run_id") != RUN or
            source.get("artifact_id") != ARTIFACT or
            source.get("executable_artifact_id") != EXE_ARTIFACT or
            source.get("checkout_sha") != SOURCE or
            source.get("PE_SHA256") != PE or
            source.get("PE_bytes") != 20441088 or
            source.get("PE_type") != "Windows AMD64 PE32+"):
        raise ValueError("strict native executable/source epoch drift")
    return source


def validate_strict(strict: dict) -> dict:
    """Require all FOUR original routes and their actual image/source digests."""
    _identities(strict)
    cases = strict.get("cases")
    if not isinstance(cases, list) or len(cases) != len(STRICT):
        raise ValueError("not four original strict native captures")
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("non-object strict capture")
        cid = case.get("id")
        if not isinstance(cid, str) or cid not in STRICT or cid in seen:
            raise ValueError("duplicate or unknown strict native case ID")
        seen.add(cid)
        (folder, route, pixels, canvas, root, png, p7, original, fnv) = STRICT[cid]
        if (case.get("acceptance_matrix_id") != cid or
                case.get("route") != route or case.get("output") != list(pixels) or
                case.get("logical_source") != list(canvas) or
                case.get("PNG_sha256") != png or
                case.get("final_SDL_P7_sha256") != p7):
            raise ValueError("strict route/size/source/hash substitution: " + cid)
        if root is None:
            if ("root" in case or case.get("original_title_P7_sha256") != original
                    or case.get("original_title_source_RGBA_FNV64") != fnv):
                raise ValueError("title source witness mismatch: " + cid)
        elif case.get("root") != list(root):
            raise ValueError("compact/wide root geometry mismatch: " + cid)
    result = strict.get("result")
    if (not isinstance(result, dict) or
            result.get("original_PNG_P7_exact_matches") != 4 or
            result.get("original_source_title_P7_FNV_matches") != 2 or
            result.get("full_25_case_matrix_approvals") != 0 or
            result.get("human_approved") is not False or
            result.get("physical_hardware_approved") is not False or
            result.get("original_guest_parity_approved") is not False or
            result.get("release_gate_credit") != 0 or
            result.get("different_executable_from_21_case_cohort") is not True):
        raise ValueError("strict manifest overclaims native approval or byte evidence")
    return {c["id"]: c for c in cases}


def verify_original_archives(strict: dict, capture_zip: Path, executable_zip: Path) -> dict:
    """Strong optional path: independently decode unchanged SDL P7/PNG and PE."""
    validate_strict(strict)
    original = archive.verify(capture_zip, SOURCE, PE)
    captures = original.get("captures")
    if not isinstance(captures, list) or len(captures) != 4:
        raise ValueError("strict original archive must contain exactly four captures")
    names = set()
    for cap in captures:
        cid = next((name for name, row in STRICT.items() if row[0] == cap["id"]), None)
        if cid is None or cid in names:
            raise ValueError("unexpected or duplicate original native capture in archive")
        names.add(cid)
        folder, route, dims, canvas, root, png, p7, source_p7, fnv = STRICT[cid]
        if (cap["native_semantic_route"] != route or
                cap["pixels"] != list(dims) or
                cap["native_source_canvas_at_capture"] != list(canvas) or
                cap["png_sha256"] != png or cap["p7_sha256"] != p7 or
                cap["source_sha"] != SOURCE or cap["exe_sha256"] != PE or
                cap["human_approved"] is not False or cap["release_gate_credit"] != 0):
            raise ValueError("original native P7/log/exe case substitution: " + cid)
        if root is not None and cap["native_root_geometry_at_capture"] != list(root):
            raise ValueError("original native root geometry mismatch: " + cid)
        if source_p7 is not None:
            title = cap["verified_native_title_source"]
            if (not isinstance(title, dict) or
                    title.get("title_native_source_sha256") != source_p7 or
                    title.get("title_native_source_rgba_fnv1a64") != fnv):
                raise ValueError("original captured title source raster mismatch: " + cid)
    # An asset ZIP alone is not proof of the exact executable. Independently
    # re-read PE bytes and its actual AMD64 image header from the other ZIP.
    with zipfile.ZipFile(executable_zip) as z:
        if z.namelist() != ["UniracersSNESRecomp.exe"]:
            raise ValueError("unexpected executable ZIP contents")
        info = z.getinfo("UniracersSNESRecomp.exe")
        if info.file_size != 20441088:
            raise ValueError("incorrect original Win32 executable length")
        data = z.read(info)
    if hashlib.sha256(data).hexdigest() != PE or data[:2] != b"MZ":
        raise ValueError("original Windows PE bytes/hash mismatch")
    pe_offset = int.from_bytes(data[0x3c:0x40], "little")
    if (pe_offset >= len(data) - 26 or data[pe_offset:pe_offset+4] != b"PE" + bytes((0, 0)) or
            int.from_bytes(data[pe_offset+4:pe_offset+6], "little") != 0x8664 or
            int.from_bytes(data[pe_offset+24:pe_offset+26], "little") != 0x20b):
        raise ValueError("original executable is not AMD64 PE32+")
    return {"capture_count":4, "executable_sha256":PE,
            "original_zip_pixel_transport_verified":True,
            "human_visual_approved":False, "hardware_approved":False,
            "release_gate_credit":0}


def expected_index(matrix: dict, old: dict, strict: dict) -> dict:
    # Old independent 21-image summary has its own frozen SHA/route validator.
    qualified = legacy.reconcile(matrix, old)
    new = validate_strict(strict)
    rows = []
    for case in matrix["cases"]:
        cid = case["id"]
        evidence = []
        oldrow = next(x for x in qualified["cases"] if x["id"] == cid)
        if oldrow["technical_candidate"]:
            capture = oldrow["source_capture_ids"][0]
            evidence.append({
                "native_run":old["run"]["id"],
                "source_checkout":old["run"]["merge_checkout_sha"],
                "pe_sha256":old["run"]["executable"]["sha256"],
                "capture":capture,
                "correspondence":"close geometry and semantic route only",
                "unproven":"physical input, visual finish and source/game parity",
            })
        elif oldrow.get("related_evidence_only"):
            evidence.append({
                "native_run":old["run"]["id"],
                "source_checkout":old["run"]["merge_checkout_sha"],
                "correspondence":"related partial only",
                "unproven":"case-specific input, display dimensions, guest state or navigation differs",
            })
        if cid in new:
            evidence.append({
                "native_run":RUN, "source_checkout":SOURCE, "pe_sha256":PE,
                "artifact_id":ARTIFACT, "capture":cid,
                "correspondence":"exact output pixels and native source stage only",
                "unproven":"physical P1 input, human visual assessment and whole game",
            })
        rows.append({
            "id":cid, "required_screen":case["screen"],
            "required_mode":case["mode"], "required_pixels":case["pixels"],
            "required_aspect":case["aspect"], "required_input":case["input"],
            "required_state":case["state"], "review_target":case["review_target"],
            "independent_historical_evidence":evidence, "acceptance":"HOLD",
            "visual_accepted":False, "human_approved":False,
            "hardware_approved":False, "release_gate_credit":0,
        })
    counts = {
        "canonical_cases":len(rows),
        "old_run_21_close":sum(any(e["correspondence"].startswith("close")
                                   for e in x["independent_historical_evidence"]) for x in rows),
        "old_run_21_partial":sum(any(e["correspondence"].startswith("related")
                                     for e in x["independent_historical_evidence"]) for x in rows),
        "separate_strict_output_cases":len(new),
        "without_ANY_related_capture_across_both_epochs":sum(
            not x["independent_historical_evidence"] for x in rows),
        "formally_accepted":0,
    }
    return {"counts":counts, "cases":rows}


def reconcile(matrix: dict, old: dict, strict: dict, stored: dict) -> dict:
    expected = expected_index(matrix, old, strict)
    if (stored.get("schema_version") != 1 or
            stored.get("counts") != expected["counts"] or
            stored.get("cases") != expected["cases"]):
        raise ValueError("stored cross-epoch matrix differs from qualified source cases")
    if expected["counts"] != {
        "canonical_cases":25, "old_run_21_close":5,
        "old_run_21_partial":9, "separate_strict_output_cases":4,
        "without_ANY_related_capture_across_both_epochs":8, "formally_accepted":0
    }:
        raise ValueError("historical native evidence counts changed")
    return {
        "source_epochs":[legacy.FROZEN_CHECKOUT_SHA,SOURCE],
        "physical_windows_executables":[legacy.FROZEN_PE_SHA256,PE],
        "same_executable":False, "historical_native_cases":25,
        "formally_accepted":0, "human_approved":False,
        "hardware_approved":False, "release_gate_credit":0,
        "counts":expected["counts"],
        "raw_capture_ZIPs_rechecked_this_run":False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--matrix",type=Path,default=Path("analysis/modern-visual-acceptance-matrix.json"))
    ap.add_argument("--old",type=Path,default=Path("analysis/evidence/modern-visual-integrated-final-sdl-21cases-20261021.json"))
    ap.add_argument("--strict",type=Path,default=Path("analysis/evidence/modern-visual-strict-480p-1080p-zip-recheck-20261020.json"))
    ap.add_argument("--stored",type=Path,default=Path("analysis/evidence/modern-visual-25case-independent-epoch-matrix-20261020.json"))
    ap.add_argument("--strict-zip",type=Path)
    ap.add_argument("--strict-executable-zip",type=Path)
    args=ap.parse_args()
    documents=[json.loads(p.read_text()) for p in (args.matrix,args.old,args.strict,args.stored)]
    result=reconcile(*documents)
    if bool(args.strict_zip) != bool(args.strict_executable_zip):
        ap.error("original strict capture and executable ZIPs must both be supplied")
    if args.strict_zip:
        result["original_zip_check"]=verify_original_archives(documents[2],args.strict_zip,args.strict_executable_zip)
        result["raw_capture_ZIPs_rechecked_this_run"]=True
    print(json.dumps(result,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
