#!/usr/bin/env python3
"""Replay the independent temporal atlas from a pinned *genuine* Zoo A/B ZIP.

The original nine-frame A/B archive lacks raw +5039 and all four guest
execution logs. Those omissions are explicit unknowns, not reconstructed data.
This script does not run an emulator or accept any USA event.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path

import qa01_frame_delta_atlas as delta
import qa01_independent_zoo_capture_ab_archive as authentic


def audit(archive: Path, expected_sha: str = authentic.PINNED_SHA) -> dict:
    # Mandatory independent ZIP SHA, CRC, source/movie/input, binary *claims*,
    # unchanged A/B semantics, raw manifest and image-byte verification FIRST.
    verified = authentic.verify(archive, expected_sha=expected_sha)
    with zipfile.ZipFile(archive) as z, tempfile.TemporaryDirectory(
            prefix="qa01-zoo-authentic-delta-") as temp:
        manifest = json.loads(z.read(authentic.DOC["frames"]))
        root = Path(temp)
        prefix = authentic.RAW + "retained/"
        for entry in manifest["raw_retained_members"]:
            name = entry["member"]
            # The authentic verifier already requires no foreign raw members;
            # never permit nested path escapes or substituted filenames.
            delta.frames.must(Path(name).name == name,
                              "retained source raw image member path is not flat")
            (root / name).write_bytes(z.read(prefix + name))
        result = delta.atlas(manifest, root)
    delta.frames.must(
        result["full_original_native_raw_frame_pairs_independently_reopened"] ==
        verified["retained_raw_files_independently_reopened"] // 4 and
        len(result["equal_digest_only_frame_pairs_not_independently_reopened"]) ==
        verified["digest_only_frames_not_reopened"] and
        result["unmasked_original_native_byte_occurrences"] ==
        verified["actual_unmasked_byte_differences"],
        "independent archive and temporally reopened raw counts disagree")
    # These describe only original/native WRAM/SRAM at the same named dump
    # phase, not original movie CPU reads or next-Bowl transition causality.
    return {
        "schema": "ur-qa01-source-authentic-zoo-frame-delta-atlas/1",
        "source_zip_sha256": verified["source_zip_sha256"],
        "independent_original_native_archive_adjudication":
            verified["adjudication"],
        "independent_original_native_archive_gameplay_HOLD": True,
        "atlas": result,
        "original_guest_execution_stdout_logs_reopened": False,
        "genuinely_consumed_CPU_or_SPC_divergence_proven": False,
        "accepted_USA_events": 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    delta.frames.must(not args.output.exists(),
                      "refuse overwrite of source-authentic timeline")
    result = audit(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("Real 2014 Zoom Zoo WRAM/SRAM frame atlas: source-bound HOLD; 0/45")


if __name__ == "__main__":
    main()
