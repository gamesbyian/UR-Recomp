#!/usr/bin/env python3
"""Check that two native runs of one route are bit-identical frame by frame.

The 4:3 regression gate: the shipping product with Widescreen off must leave
the authentic path untouched. A baseline built from the same generated
program without the Widescreen presentation layer and product host, and the
product in Original view, run the same deterministic route; every per-frame
framebuffer and WRAM image and every retained script dump must be identical.

Inputs are `--framedump` directories (frame_NNNNNN.{bmp,json,_wram.bin}) and,
optionally, `SNESRECOMP_DUMP_DIR` checkpoint directories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from tools.evidence_contract import assertion, make_envelope
except ModuleNotFoundError:
    from evidence_contract import assertion, make_envelope

FRAME_RE = re.compile(r"^frame_(\d{6})")


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _files(root: Path) -> dict[str, Path]:
    return {p.name: p for p in sorted(root.iterdir()) if p.is_file()}


def compare_dirs(baseline: Path, candidate: Path) -> dict[str, Any]:
    a = _files(baseline)
    b = _files(candidate)
    common = sorted(set(a) & set(b))
    differing = [name for name in common if _digest(a[name]) != _digest(b[name])]
    frames = {int(m.group(1)) for name in common if (m := FRAME_RE.match(name))}
    first_frame = None
    for name in differing:
        m = FRAME_RE.match(name)
        if m and (first_frame is None or int(m.group(1)) < first_frame):
            first_frame = int(m.group(1))
    return {
        "files_compared": len(common),
        "frames_compared": len(frames),
        "only_in_baseline": sorted(set(a) - set(b))[:16],
        "only_in_candidate": sorted(set(b) - set(a))[:16],
        "differing_files": len(differing),
        "first_differing": differing[:16],
        "first_differing_frame": first_frame,
    }


def check(route: str, frames: tuple[Path, Path], dumps: tuple[Path, Path] | None,
          min_frames: int) -> dict[str, Any]:
    metrics: dict[str, Any] = {"frames": compare_dirs(*frames)}
    f = metrics["frames"]
    checks = [
        assertion(f"{route}-frame-coverage", f["frames_compared"] >= min_frames,
                  {"frames_compared": f["frames_compared"], "min_frames": min_frames}),
        assertion(f"{route}-same-frame-set",
                  not f["only_in_baseline"] and not f["only_in_candidate"],
                  {"only_in_baseline": f["only_in_baseline"],
                   "only_in_candidate": f["only_in_candidate"]}),
        assertion(f"{route}-frames-bit-identical", f["differing_files"] == 0,
                  {"differing_files": f["differing_files"],
                   "first_differing": f["first_differing"],
                   "first_differing_frame": f["first_differing_frame"]}),
    ]
    if dumps is not None:
        d = metrics["dumps"] = compare_dirs(*dumps)
        checks.append(assertion(
            f"{route}-dumps-bit-identical",
            d["files_compared"] > 0 and d["differing_files"] == 0
            and not d["only_in_baseline"] and not d["only_in_candidate"],
            {k: d[k] for k in ("files_compared", "differing_files", "first_differing",
                               "only_in_baseline", "only_in_candidate")},
        ))
    return make_envelope(
        evidence_type="framedump-identity",
        producer="tools/check_framedump_identity.py",
        subject={"route": route},
        inputs={"min_frames": min_frames},
        metrics=metrics,
        assertions=checks,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", required=True)
    parser.add_argument("--baseline-frames", required=True, type=Path)
    parser.add_argument("--candidate-frames", required=True, type=Path)
    parser.add_argument("--baseline-dumps", type=Path)
    parser.add_argument("--candidate-dumps", type=Path)
    parser.add_argument("--min-frames", type=int, default=1)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if (args.baseline_dumps is None) != (args.candidate_dumps is None):
        parser.error("--baseline-dumps and --candidate-dumps go together")
    dumps = (args.baseline_dumps, args.candidate_dumps) if args.baseline_dumps else None
    envelope = check(args.route, (args.baseline_frames, args.candidate_frames),
                     dumps, args.min_frames)
    rendered = json.dumps(envelope, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0 if envelope["outcome"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
