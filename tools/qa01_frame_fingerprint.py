#!/usr/bin/env python3
"""QA01 read-only continuous paired WRAM/SRAM capture audit and raw retention.

Reads existing genuine full-memory frame dumps. It does not instrument, boot,
retime or certify either emulator. A digest proves equality only at the named
observation phase; source identity and actual frame acknowledgments need an
independent producer attestation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

WRAM = 131072
SRAM = 8192
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SCHEMA = "ur-qa01-frame-fingerprint/1"


def must(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_identity(data: dict) -> None:
    must(type(data) is dict and
         type(data.get("source_sha")) is str and HEX40.fullmatch(data["source_sha"]) and
         all(type(data.get(x)) is str and HEX64.fullmatch(data[x])
             for x in ("rom_sha256", "movie_sha256", "input_sha256")) and
         type(data.get("observation_phase")) is str and data["observation_phase"].strip(),
         "missing source/ROM/movie/input identity or observation phase")
    must(all(type(data.get(x)) is int and data[x] >= 0
             for x in ("original_frame_origin", "native_frame_origin")),
         "distinct actual guest frame origins required")
    must(data.get("masked_wram_bytes") == 0 and data.get("masked_sram_bytes") == 0,
         "unmasked full-memory observation required")


def snapshot_path(root: Path, frame: int, kind: str) -> Path:
    return root / f"frame_{frame:06d}_{kind}.bin"


def raw(path: Path, expected: int) -> bytes:
    must(path.is_file() and not path.is_symlink(), "missing/symlinked raw image: " + str(path))
    data = path.read_bytes()
    must(len(data) == expected, "truncated/oversized raw image: " + str(path))
    return data


def audit(identity: dict, original_root: Path, native_root: Path,
          start: int, end: int, retained: Path | None = None,
          max_retained: int = 200) -> dict:
    validate_identity(identity)
    must(type(start) is int and type(end) is int and 0 <= start <= end and
         end - start < 20000, "invalid or unbounded frame interval")
    must(type(max_retained) is int and max_retained > 0, "invalid raw retention limit")
    must(original_root.resolve() != native_root.resolve(),
         "reference/native raw image roots cannot be identical")
    counts = {"wram": 0, "sram": 0}
    first_diff = {"wram": None, "sram": None}
    rows, selected = [], []
    sha_total = hashlib.sha256()
    for relative in range(start, end + 1):
        hosts = {
            "original": identity["original_frame_origin"] + relative,
            "native": identity["native_frame_origin"] + relative,
        }
        pair = {}
        row = {"relative_frame": relative, "original_actual_host_frame": hosts["original"],
               "native_actual_host_frame": hosts["native"], "types": {}}
        changed = False
        for kind, size in (("wram", WRAM), ("sram", SRAM)):
            left = snapshot_path(original_root, hosts["original"], kind)
            right = snapshot_path(native_root, hosts["native"], kind)
            a, b = raw(left, size), raw(right, size)
            pair[kind] = (left, right)
            na, nb = digest(a), digest(b)
            sha_total.update(bytes.fromhex(na))
            sha_total.update(bytes.fromhex(nb))
            difference = sum(u != v for u, v in zip(a, b)) if na != nb else 0
            # A SHA mismatch with identical bytes would be a broken hash
            # implementation, not acceptable proof of a guest divergence.
            must(na == nb or difference > 0, "digest and byte comparison disagree")
            counts[kind] += difference
            if difference and first_diff[kind] is None:
                first_diff[kind] = relative
            changed |= bool(difference)
            row["types"][kind] = {
                "original_sha256": na,
                "native_sha256": nb,
                "unmasked_differing_byte_count": difference,
                "full_image_bytes_per_guest": size,
            }
        rows.append(row)
        if changed or relative in (start, end):
            selected.append((relative, hosts, pair))
    must(retained is None or len(selected) <= max_retained,
         "raw evidence retention cap exceeded; raise cap explicitly or narrow case")
    retained_manifest = []
    if retained is not None:
        must(not retained.exists() or (retained.is_dir() and not any(retained.iterdir())),
             "raw evidence output directory must be new or empty")
        retained.mkdir(parents=True, exist_ok=True)
        for rel, hosts, pair in selected:
            for kind, paths in pair.items():
                for guest, path in zip(("original", "native"), paths):
                    destination = retained / f"{guest}-relative-{rel:06d}-{kind}.bin"
                    shutil.copyfile(path, destination)
                    expected = rows[rel - start]["types"][kind][guest + "_sha256"]
                    must(digest(raw(destination, WRAM if kind == "wram" else SRAM)) == expected,
                         "copied genuine raw evidence hash changed")
                    retained_manifest.append({
                        "member": destination.name, "guest": guest, "kind": kind,
                        "relative_frame": rel, "actual_host_frame": hosts[guest],
                        "sha256": expected,
                    })
    return {
        "schema": SCHEMA,
        "source_identity": identity,
        "coverage": {"start": start, "end": end, "required_frames": end - start + 1,
                     "observed_original_frames": len(rows),
                     "observed_native_frames": len(rows),
                     "continuous_at_declared_frame_phase": True,
                     "between_frame_opcode_semantics_proven": False},
        "full_unmasked_differing_byte_occurrences": counts,
        "first_differing_relative_frame": first_diff,
        "frame_pair_digest_chain_sha256": sha_total.hexdigest(),
        "rows": rows,
        "raw_retained_members": retained_manifest,
        "raw_retained_scope": ("all differing frames plus first and final pair"
                               if retained is not None else "none; digest-only report"),
        "producer_binary_and_executed_input_independently_verified": False,
        "windows_disk_persistence_proven": False,
        "accepted_USA_events": 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--identity", type=Path, required=True)
    ap.add_argument("--original-root", type=Path, required=True)
    ap.add_argument("--native-root", type=Path, required=True)
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--end", type=int, required=True)
    ap.add_argument("--retain-raw", type=Path)
    ap.add_argument("--max-retained", type=int, default=200)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    r = audit(json.loads(args.identity.read_text()), args.original_root,
              args.native_root, args.start, args.end,
              retained=args.retain_raw, max_retained=args.max_retained)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(r, sort_keys=True, indent=2) + "\n")
    print("QA01 complete captured-frame audit: diagnostic only, 0/45")


if __name__ == "__main__":
    main()
