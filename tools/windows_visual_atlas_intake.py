#!/usr/bin/env python3
"""Discover reusable Windows SDL screenshots in other first-party Actions artifacts.

Never accept a PNG on filename alone. Evidence must be source-bound, complete,
single-case and corroborated by the original P7 readback and process log.
Source integration is checked against the actual main history, not a claim in
the producer's metadata. Unrecognized material goes to a review report only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

try:
    from tools import windows_visual_atlas as atlas
except ModuleNotFoundError:
    import windows_visual_atlas as atlas

SOURCE_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_CASES = 256
MAX_SCREEN = 3840 * 2160 * 4 + 1024 * 1024
# Only source-owned genuine SDL capture pipelines may yield auto-eligible bytes.
PRODUCERS = {
    "Modern visual QA native SDL baseline",
    "Windows Visual Atlas (sharded opt-in capture)",
}
# Changes to these files can alter a screen without changing the capture
# route. Other code changes cannot establish visual stability on their own.
VISUAL_PATHS = (
    "native/product", "native/presentation", "native/title",
    "tools/baldosa_native_modern_root.cpp",
    "tools/baldosa_modern_profile_activation_spike.py",
    "tools/qa_modern_visual_sdl_capture.py",
    "tools/qa_modern_visual_win32_capture_driver.py",
    "third_party",
)


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, check=False, timeout=30)


def code_state(source: str, repo: Path, main: str) -> str:
    """Source must be a real ancestor; UI-impacting changes require review."""
    if not SOURCE_RE.fullmatch(source) or not SOURCE_RE.fullmatch(main):
        return "unknown"
    if run_git(repo, "cat-file", "-e", source + "^{commit}").returncode:
        return "unknown"
    if run_git(repo, "cat-file", "-e", main + "^{commit}").returncode:
        return "unknown"
    if run_git(repo, "merge-base", "--is-ancestor", source, main).returncode:
        return "unmerged"
    changed = run_git(repo, "diff", "--quiet", source, main, "--", *VISUAL_PATHS)
    return "integrated-current-visual" if changed.returncode == 0 else (
        "integrated-changed-visual" if changed.returncode == 1 else "unknown"
    )


def witness(receipt: dict, folder: Path) -> bool:
    """Authenticate retained P7 and final SDL log via receipt digest.

    A directory may contain two probe folders. Select by content hashes,
    never by a guessed stage name or first matching filename.
    """
    if (receipt.get("schema_version") != 1 or
            type(receipt.get("native_process_exit")) is not int or
            receipt["native_process_exit"] != 0 or
            receipt.get("authentic_isolation_approved") is not False):
        return False
    expected_p7 = receipt.get("p7_sha256")
    expected_log = receipt.get("native_process_log_sha256")
    if not isinstance(expected_p7, str) or not DIGEST_RE.fullmatch(expected_p7):
        return False
    if not isinstance(expected_log, str) or not DIGEST_RE.fullmatch(expected_log):
        return False
    dims = receipt.get("actual_sdl_renderer_output")
    if not isinstance(dims, list) or len(dims) != 2:
        return False
    matches = 0
    for name in ("probe_first", "capture_observed"):
        raw = folder / name / "actual-sdl-drawable.pam"
        log = folder / name / "native-process.log"
        if not raw.is_file() or not log.is_file() or raw.is_symlink() or log.is_symlink():
            continue
        if raw.stat().st_size > MAX_SCREEN or log.stat().st_size > 2_000_000:
            continue
        if atlas.sha256(raw) != expected_p7 or atlas.sha256(log) != expected_log:
            continue
        marker = f"output={dims[0]}x{dims[1]} source=SDL_RenderReadPixels"
        text = log.read_text(encoding="utf-8", errors="replace")
        if ("UR_MODERN_VISUAL_SDL_CAPTURE status=saved" not in text or marker not in text):
            continue
        # Re-run the existing no-resampling conversion, independently tying
        # the observed native P7 pixel bytes to the candidate PNG bytes.
        try:
            from tools.qa_modern_visual_pam_png import convert
        except ModuleNotFoundError:
            from qa_modern_visual_pam_png import convert
        try:
            with tempfile.TemporaryDirectory() as tmp:
                regenerated = Path(tmp) / "from-observed-p7.png"
                convert(raw, regenerated, (dims[0], dims[1]))
                if atlas.sha256(regenerated) != receipt.get("png_sha256"):
                    continue
        except (OSError, ValueError):
            continue
        matches += 1
    return matches == 1


def discover(roots: Path, output: Path, *, repo: Path, main: str,
             workflow: str, run_id: int, run_head: str) -> dict:
    """Read-only discovery; never create a trusted capture from a loose PNG."""
    if output.exists() or output.is_symlink():
        raise ValueError("Intake output already exists")
    if not roots.is_dir() or roots.is_symlink():
        raise ValueError("Missing safe intake artifact directory")
    if run_id < 1 or not SOURCE_RE.fullmatch(run_head):
        raise ValueError("Missing trusted producer run identity")
    entries = atlas.validate(atlas.load_catalog())
    by_route = {}
    for entry in entries:
        cap = entry.get("capture")
        if cap:
            by_route.setdefault((cap["route"], cap["size"]), []).append(entry)
    receipts = sorted(roots.rglob("readback-receipt.json"))
    if len(receipts) > MAX_CASES:
        raise ValueError("Intake too large; review bounded artifact selection")
    output.mkdir(parents=True)
    selected = output / "approved" / "captures"
    selected.mkdir(parents=True)
    rows = []
    seen_ids = set()
    for file in receipts:
        folder = file.parent
        row = {"artifact_path": str(file.relative_to(roots)), "state": "review",
               "producer_workflow": workflow, "producer_run": run_id}
        try:
            if file.is_symlink() or file.stat().st_size > 65536:
                raise ValueError("unsafe receipt")
            receipt = json.loads(file.read_text(encoding="utf-8"))
            if not isinstance(receipt, dict):
                raise ValueError("malformed receipt")
            route = receipt.get("native_semantic_route")
            dims = receipt.get("actual_sdl_renderer_output")
            if not isinstance(dims, list) or len(dims) != 2 or not all(type(x) is int for x in dims):
                raise ValueError("missing real SDL dimensions")
            ids = by_route.get((route, f"{dims[0]}x{dims[1]}"), [])
            if len(ids) != 1:
                raise ValueError("No unique explicit visual atlas mapping")
            entry = ids[0]
            row["id"] = entry["id"]
            if row["id"] in seen_ids:
                raise ValueError("Multiple candidates for one ID: independent selection needed")
            seen_ids.add(row["id"])
            src = receipt.get("source_sha", "")
            row["source_sha"] = src
            row["code_state"] = code_state(src, repo, main)
            if not SOURCE_RE.fullmatch(src):
                raise ValueError("source SHA invalid")
            # PR synthetic merge commits and SHA discrepancies require separate
            # verification. Never accept a different source merely because it
            # names the same route or comes from a successful GitHub run.
            if src != run_head:
                raise ValueError("capture source differs from producer run head")
            png = folder / "actual-sdl-drawable.png"
            if png.stat().st_size > MAX_SCREEN or png.is_symlink():
                raise ValueError("oversized or redirected PNG")
            atlas.valid_receipt(entry, folder, src, None)
            if not witness(receipt, folder):
                raise ValueError("missing P7 / real SDL process log witness")
            row["png_sha256"] = receipt["png_sha256"]
            row["exe_sha256"] = receipt["exe_sha256"]
            # Integration of source code permits an engineering reference, not
            # visual approval. Only allowlisted genuine producer + unchanged
            # visual code may be automatically staged for review/assembly.
            if workflow not in PRODUCERS:
                raise ValueError("unrecognized workflow origin")
            if row["code_state"] != "integrated-current-visual":
                raise ValueError("capture source not current with approved visual code")
            dest = selected / entry["id"]
            dest.mkdir()
            for name in ("actual-sdl-drawable.png", "readback-receipt.json"):
                shutil.copyfile(folder / name, dest / name)
            approval = {
                "schema_version": 1, "atlas_id": entry["id"],
                "source_sha": src, "approved_main_sha": main,
                "exe_sha256": receipt["exe_sha256"],
                "png_sha256": receipt["png_sha256"],
                "producer_workflow": workflow, "producer_run": run_id,
                "code_integrated_at_scan": True,
                "independent_visual_approval": False, "release_gate_credit": 0,
                "display_class": "source-verified-engineering-reference",
            }
            (dest / "intake-approval.json").write_text(json.dumps(approval, indent=2) + "\n")
            row["state"] = "eligible"
        except (KeyError, ValueError, OSError, TypeError, json.JSONDecodeError) as exc:
            row["reason"] = str(exc)[:350]
        rows.append(row)
    counts = {status: sum(r["state"] == status for r in rows)
              for status in ("eligible", "review")}
    report = {"schema_version": 1, "producer_workflow": workflow, "producer_run": run_id,
              "source_head": run_head, "evaluated_main": main,
              "counts": counts, "candidates": rows,
              "note": "Eligible means source-integrated genuine capture, not human artwork or hardware approval."}
    (output / "intake-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def stage(review: Path, destination: Path) -> dict:
    """Queue qualifying screenshots as reviewable GitHub changes.

    An existing representative is never overwritten automatically, even if a
    newer capture is authentic. Keep alternatives content-addressed for an
    intentional replacement review.
    """
    candidates = review / "approved" / "captures"
    if not candidates.is_dir() or candidates.is_symlink():
        raise ValueError("No admitted screenshots in intake packet")
    results = {"new": 0, "existing": 0, "alternative": 0}
    for case in sorted(candidates.iterdir()):
        if not case.is_dir() or case.is_symlink() or not atlas.ID.fullmatch(case.name):
            raise ValueError("Unsafe staged capture name")
        approval = json.loads((case / "intake-approval.json").read_text(encoding="utf-8"))
        if approval.get("atlas_id") != case.name:
            raise ValueError("Staged capture ID mismatch")
        receipt, _ = atlas.valid_receipt(
            next(e for e in atlas.validate(atlas.load_catalog()) if e["id"] == case.name),
            case, approval["source_sha"], approval["exe_sha256"])
        if receipt["png_sha256"] != approval.get("png_sha256"):
            raise ValueError("Staged image bytes differ from approval")
        current = destination / "approved" / case.name
        if current.exists():
            other = current / "actual-sdl-drawable.png"
            if other.is_file() and atlas.sha256(other) == approval["png_sha256"]:
                results["existing"] += 1
                continue
            selected = (destination / "alternatives" / case.name /
                        approval["png_sha256"])
            results["alternative"] += 1
        else:
            selected = current
            results["new"] += 1
        if selected.exists() or selected.is_symlink():
            continue
        selected.mkdir(parents=True)
        for name in ("actual-sdl-drawable.png", "readback-receipt.json", "intake-approval.json"):
            shutil.copyfile(case / name, selected / name)
    return results


def main_cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("discover")
    p.add_argument("--artifacts", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--repo", type=Path, default=atlas.ROOT)
    p.add_argument("--main-sha", required=True)
    p.add_argument("--workflow", required=True)
    p.add_argument("--run-id", required=True, type=int)
    p.add_argument("--run-head-sha", required=True)
    s = sub.add_parser("stage")
    s.add_argument("--intake", required=True, type=Path)
    s.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.action == "stage":
            print(json.dumps(stage(args.intake, args.destination), indent=2))
            return 0
        report = discover(args.artifacts, args.out, repo=args.repo,
                          main=args.main_sha, workflow=args.workflow,
                          run_id=args.run_id, run_head=args.run_head_sha)
        print(json.dumps(report["counts"], indent=2))
        return 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print("ATLAS_INTAKE_REJECTED:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main_cli())
