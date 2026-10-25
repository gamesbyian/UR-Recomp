#!/usr/bin/env python3
"""Geometry/focus/safe-area evidence for a retained native SDL capture ZIP.

Reuses (does not duplicate) `qa_modern_visual_actions_archive.verify`, which
independently proves transport and provenance of each capture: successful
Windows SDL3 process, exact log, P7 == PNG bytes, route stage, PE/source SHA.
On top of a verified ZIP this adds, per capture:

* `witnessed-source-width`: the logical width inferred from the pixels alone
  (`detect_logical`) must equal the native source canvas the host itself
  logged (256 for fixed Modern menu scenes, 342 for qualified wide-world
  scenes), an independent cross-check;
* for captures the frozen coverage map ties to an acceptance case, the full
  `qa_modern_visual_case_checks.evaluate` (output size, logical width,
  action-safe, single focus bar where applicable).

Measurement only: it never converts a capture into human art approval,
hardware acceptance or original-game parity, and release_gate_credit is 0.
A ZIP that fails provenance yields no geometry verdict at all.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import zipfile

try:
    from tools import qa_modern_visual_actions_archive as archive
    from tools import qa_modern_visual_case_checks as cases
    from tools import qa_modern_visual_case_coverage as coverage
    from tools import qa_modern_visual_diagnostics as d
except ModuleNotFoundError:  # direct CLI use
    import qa_modern_visual_actions_archive as archive
    import qa_modern_visual_case_checks as cases
    import qa_modern_visual_case_coverage as coverage
    import qa_modern_visual_diagnostics as d

# (route, output pixels) -> acceptance case, from the frozen coverage map.
ROUTE_CASE = {(route, tuple(pixels)): case
              for case, (route, pixels, _) in coverage.CASE_MAP.items()}
# The same plain root capture at the other root sizes the matrix names; the
# frozen coverage map only covers the sizes of its historical cohort.
ROUTE_CASE.update({("root-quit", (1920, 1080)): "root-wide-1080",
                   ("root-quit", (3840, 2160)): "root-wide-4k-virtual",
                   ("root-quit", (640, 480)): "root-43-480"})


def _png_member(names, capture_id):
    wanted = [n for n in names
              if n.rsplit("/", 2)[-2:] == [capture_id, "actual-sdl-drawable.png"]
              or n.endswith("/" + capture_id + "/actual-sdl-drawable.png")]
    if len(wanted) != 1:
        raise ValueError(f"expected one PNG for capture {capture_id}: {wanted}")
    return wanted[0]


def analyse(zip_path: Path, verified: dict, matrix: dict | None = None,
            require_ring: bool = False) -> dict:
    matrix = matrix if matrix is not None else cases.load_cases()
    out = []
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        for cap in verified["captures"]:
            png = z.read(_png_member(names, cap["id"]))
            frame = d.Frame(png)
            if cap["png_sha256"] != frame.sha256:
                raise ValueError("verified PNG hash differs from retained PNG: "
                                 + cap["id"])
            checks = []
            witnessed = cap["native_source_canvas_at_capture"][0]
            det = d.detect_logical(frame, (256, 342))
            checks.append({"check": "witnessed-source-width",
                           "pass": det["consistent_widths"] == [witnessed],
                           "detail": {"witnessed": witnessed,
                                      "nonuniform": det["nonuniform_fraction"]}})
            case_id = ROUTE_CASE.get((cap["native_semantic_route"],
                                      tuple(cap["pixels"])))
            case_report = None
            if case_id:
                # The source SHA is independently bound by archive.verify,
                # unlike directory-mode receipts. Preserve that distinction
                # when evaluating an explicitly source-qualified scene.
                case_report = cases.evaluate(
                    matrix[case_id], frame, require_ring,
                    observed_source_sha=cap["source_sha"])
                checks += case_report["checks"]
            out.append({"capture": cap["id"], "route": cap["native_semantic_route"],
                        "pixels": cap["pixels"], "png_sha256": frame.sha256,
                        "case": case_id, "checks": checks,
                        "pass": all(c["pass"] for c in checks)})
    return {"schema": "ur-modern-visual-archive-cases-v1",
            "artifact": Path(zip_path).name,
            "exe_sha256": verified["captures"][0]["exe_sha256"],
            "source_sha": verified["captures"][0]["source_sha"],
            "captures": out, "pass": bool(out) and all(c["pass"] for c in out),
            "human_visual_approved": False, "physical_monitor_approved": False,
            "original_guest_equivalence_approved": False,
            "release_gate_credit": 0}


def analyse_dirs(dirs, matrix: dict | None = None,
                 require_ring: bool = False) -> dict:
    """Same checks on capture directories (`actual-sdl-drawable.png` +
    `readback-receipt.json`) as the capture driver leaves them on the runner.

    There is no independent archive verification here (the directory is the
    producing run's own output), so provenance is limited to the receipt's PNG
    hash and output size; the host-witnessed source width is not available
    and is replaced by "exactly one logical width explains the pixels".
    """
    matrix = matrix if matrix is not None else cases.load_cases()
    out = []
    for directory in dirs:
        directory = Path(directory)
        receipt = json.loads((directory / "readback-receipt.json").read_text())
        data = (directory / "actual-sdl-drawable.png").read_bytes()
        frame = d.Frame(data)
        if receipt.get("png_sha256") != frame.sha256:
            raise ValueError("receipt PNG hash differs from retained PNG: "
                             + directory.name)
        pixels = tuple(receipt["actual_sdl_renderer_output"])
        if pixels != (frame.width, frame.height):
            raise ValueError("receipt output size differs from PNG: " + directory.name)
        route = receipt.get("native_semantic_route")
        det = d.detect_logical(frame, (256, 342))
        checks = [{"check": "one-logical-width", "pass": det["pass"],
                   "detail": {"nonuniform": det["nonuniform_fraction"],
                              "consistent_widths": det["consistent_widths"]}}]
        if not det["pass"]:
            # Nothing standard explains this frame: say what (if anything) does.
            checks[0]["detail"]["explain"] = d.explain_mapping(frame, top=3)
        case_id = ROUTE_CASE.get((route, pixels))
        if case_id:
            checks += cases.evaluate(matrix[case_id], frame, require_ring)["checks"]
        out.append({"capture": directory.name, "route": route,
                    "pixels": list(pixels), "png_sha256": frame.sha256,
                    "case": case_id, "checks": checks,
                    "pass": all(c["pass"] for c in checks)})
    return {"schema": "ur-modern-visual-archive-cases-v1", "artifact": "directories",
            "exe_sha256": "n/a", "source_sha": "n/a",
            "captures": out, "pass": bool(out) and all(c["pass"] for c in out),
            "human_visual_approved": False, "physical_monitor_approved": False,
            "original_guest_equivalence_approved": False,
            "release_gate_credit": 0}


def markdown(report: dict) -> str:
    lines = [f"### Modern capture geometry: **{'pass' if report['pass'] else 'FAIL'}**",
             f"`{report['artifact']}` · PE `{report['exe_sha256'][:12]}` · "
             f"source `{report['source_sha'][:12]}`", "",
             "| capture | route | case | checks |", "|---|---|---|---|"]
    for c in report["captures"]:
        def cell(k):
            state = "ok" if k["pass"] else "FAIL"
            widths = k["detail"].get("consistent_widths")
            if k["check"] == "one-logical-width" and widths:
                state += f"({widths[0]})" if len(widths) == 1 else f"({'/'.join(map(str, widths))})"
            return f"{k['check']}={state}"
        detail = ", ".join(cell(k) for k in c["checks"])
        lines.append(f"| {c['capture']} | {c['route']} | {c['case'] or '-'} | {detail} |")
    lines += ["", "_Geometry/colour measurement of verified native captures; no human, "
              "physical or parity approval._"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifact", type=Path)
    ap.add_argument("--dir", type=Path, action="append",
                    help="capture directory (repeatable); instead of --artifact")
    ap.add_argument("--expected-source-sha")
    ap.add_argument("--expected-exe-sha")
    ap.add_argument("--require-ring", action="store_true",
                    help="fail focus-bar captures lacking the shared two-tone ring")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--summary", type=Path)
    a = ap.parse_args(argv)
    try:
        if bool(a.artifact) == bool(a.dir):
            raise ValueError("pass exactly one of --artifact or --dir")
        if a.artifact:
            verified = archive.verify(a.artifact, a.expected_source_sha,
                                      a.expected_exe_sha)
            report = analyse(a.artifact, verified, require_ring=a.require_ring)
        else:
            report = analyse_dirs(a.dir, require_ring=a.require_ring)
    except (archive.AuditError, ValueError, OSError, KeyError,
            zipfile.BadZipFile) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(report, indent=2)
    if a.json:
        a.json.write_text(text + "\n")
    else:
        print(text)
    if a.json or a.summary:
        # The step summary is not reachable from job logs or the API; always
        # leave the human-readable table (and failing checks) in the log too.
        print(markdown(report))
        for cap in report["captures"]:
            for chk in cap["checks"]:
                if not chk["pass"]:
                    print(f"FAILED {cap['capture']} {chk['check']} "
                          f"{json.dumps(chk['detail'])}")
    if a.summary:
        with a.summary.open("a") as handle:
            handle.write(markdown(report))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
