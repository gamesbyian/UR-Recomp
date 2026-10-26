#!/usr/bin/env python3
"""Independently audit downloaded public ROM-free Windows smoke artifact ZIPs.

Uses actual member bytes, not Actions success labels. Never opens the private
full playable ZIP, executes the PE, authenticates its source or grants QA credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
try:
    from .audit_windows_smoke_artifact import _open_transport
except ImportError:
    from audit_windows_smoke_artifact import _open_transport

HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
PREFIX = "windows-romfree-binary/"
EXE = PREFIX + "UniracersSNESRecomp.exe"
BINDING = PREFIX + "binding.json"
MANIFEST = "UR-Recomp-Windows-x64/PACKAGE-MANIFEST.json"
SIDECAR = "UR-Recomp-Windows-x64.zip.sha256"
REQUIRED = {EXE, BINDING, MANIFEST, SIDECAR}
MAX_ARTIFACT_BYTES = 128_000_000
MAX_PE_BYTES = 128_000_000
MAX_TOTAL_UNPACKED = 300_000_000
MAX_MEMBERS = 500


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pe_header(data):
    require(64 <= len(data) <= MAX_PE_BYTES and data[:2] == b"MZ",
            "missing MZ executable")
    offset = struct.unpack_from("<I", data, 0x3c)[0]
    require(64 <= offset <= 1024 * 1024 and offset + 26 <= len(data),
            "invalid PE offset")
    require(data[offset:offset + 4] == b"PE\x00\x00"
            and struct.unpack_from("<H", data, offset + 4)[0] == 0x8664
            and struct.unpack_from("<H", data, offset + 24)[0] == 0x20b,
            "not AMD64 PE32+")
    return offset


def audit(path):
    """One ROM-free smoke ZIP. Only fixed, small source-binding fields exit."""
    require(path.is_file() and not path.is_symlink(), "missing or redirected archive")
    require(path.stat().st_size <= MAX_ARTIFACT_BYTES, "outer artifact too large")
    outer = sha(path.read_bytes())
    with _open_transport(path) as archive:
        infos = archive.infolist()
        require(len(infos) <= MAX_MEMBERS, "too many artifact members")
        names = [i.filename for i in infos]
        require(len(names) == len(set(names)), "duplicate archive member")
        require(len(names) == len({n.casefold() for n in names}),
                "Windows-alias artifact members")
        require(all(
            not n.startswith("/") and "\\" not in n
            and not PurePosixPath(n).is_absolute()
            and ".." not in PurePosixPath(n).parts
            and n != ""
            for n in names
        ), "unsafe artifact member path")
        require(sum(i.file_size for i in infos) <= MAX_TOTAL_UNPACKED,
                "artifact expands too far")
        require(all(i.file_size <= MAX_PE_BYTES for i in infos),
                "oversized artifact member")
        require(REQUIRED.issubset(set(names)), "missing ROM-free audit membership")
        require(not any(n.lower().endswith((".sfc", ".smc", ".swc", ".fig"))
                        for n in names), "ROM content named in public artifact")
        exe = archive.read(EXE)
        require(len(exe) <= MAX_PE_BYTES, "oversized PE")
        offset = pe_header(exe)
        binding_raw = archive.read(BINDING)
        manifest_raw = archive.read(MANIFEST)
        require(len(binding_raw) <= 65536 and len(manifest_raw) <= 8_000_000,
                "oversized provenance JSON")
        binding = json.loads(binding_raw)
        manifest = json.loads(manifest_raw)
        require(isinstance(binding, dict) and isinstance(manifest, dict),
                "invalid manifest or binding")
        require(binding.get("schema") == "ur-windows-smoke-romfree-pe-binding/1",
                "unknown binding schema")
        source = binding.get("source_commit")
        require(isinstance(source, str) and bool(HEX40.fullmatch(source)),
                "unbound source commit")
        orig_zip = binding.get("original_portable_zip_sha256")
        require(isinstance(orig_zip, str) and bool(HEX64.fullmatch(orig_zip)),
                "missing inner ZIP SHA256 claim")
        require(binding.get("release_gate_credit") == 0
                and binding.get("physical_windows_accepted") is False
                and binding.get("original_zip_uploaded") is False
                and binding.get("rom_or_player_data_uploaded") is False,
                "binding claims inadmissible public release content")
        require(manifest.get("source_revision") == source
                and binding.get("original_manifest_sha256") == sha(manifest_raw),
                "manifest provenance mismatch")
        require(binding.get("executable_bytes") == len(exe)
                and binding.get("executable_sha256") == sha(exe),
                "staged executable content mismatch")
        matching = [v for v in manifest.get("files", [])
                    if isinstance(v, dict)
                    and v.get("path") == "UniracersSNESRecomp.exe"]
        require(len(matching) == 1
                and matching[0].get("size") == len(exe)
                and matching[0].get("sha256") == sha(exe),
                "private manifest does not bind staged executable")
        require(archive.read(SIDECAR) ==
                (orig_zip + "  UR-Recomp-Windows-x64.zip\n").encode("ascii"),
                "private full-ZIP sidecar disagrees with binding")
        sram_snapshots = sorted(n for n in names if n.lower().endswith(".sram.bin"))
        return ({
            "outer_artifact_sha256": outer,
            "source_commit_claim": source,
            "staged_exe_sha256": sha(exe),
            "staged_exe_bytes": len(exe),
            "private_portable_zip_sha256_claim": orig_zip,
            "manifest_sha256": sha(manifest_raw),
            "member_count": len(names),
            "raw_sram_snapshot_count": len(sram_snapshots),
            "contains_raw_game_state": bool(sram_snapshots),
            "contains_named_rom_file": False,
            "private_zip_bytes_inspected": False,
            "release_gate_credit": 0,
        }, exe, offset)


def compare(paths, *, expected_source=None, expected_zip=None):
    require(1 <= len(paths) <= 8, "one to eight artifacts required")
    if expected_source is not None:
        require(bool(HEX40.fullmatch(expected_source)), "invalid expected source")
    if expected_zip is not None:
        require(bool(HEX64.fullmatch(expected_zip)), "invalid expected private ZIP")
    rows, binaries = [], []
    for path in paths:
        row, pe, pe_offset = audit(path)
        rows.append(row)
        binaries.append((pe, pe_offset))
    source_set = {r["source_commit_claim"] for r in rows}
    pe_set = {r["staged_exe_sha256"] for r in rows}
    zip_set = {r["private_portable_zip_sha256_claim"] for r in rows}
    pairwise = []
    for i, (left, left_offset) in enumerate(binaries):
        for j in range(i + 1, len(binaries)):
            right, right_offset = binaries[j]
            # Compare in constant auxiliary memory: never retain every
            # differing byte position from an untrusted 128 MiB PE.
            length_matches = len(left) == len(right)
            diff_count = sum(a != b for a, b in zip(left, right))
            diff_count += abs(len(left) - len(right))
            time_fields = (
                bool(diff_count) and length_matches
                and left_offset == right_offset
                and left[:left_offset + 8] == right[:right_offset + 8]
                and left[left_offset + 12:] == right[right_offset + 12:]
            )
            pairwise.append({
                "left": i, "right": j,
                "different_byte_count": diff_count,
                "same_executable_bytes": left == right,
                "only_coff_timestamp_bytes_differ": time_fields,
                "same_private_zip_sha256_claim": (
                    rows[i]["private_portable_zip_sha256_claim"] ==
                    rows[j]["private_portable_zip_sha256_claim"]),
            })
    return {
        "schema": "UR-INDEPENDENT-WINDOWS-ROMFREE-ARTIFACT-AUDIT/1",
        "authority": "bounded_public_artifact_bytes_only_no_release_admission",
        "artifacts": rows,
        "all_source_claims_identical": len(source_set) == 1,
        "all_exe_sha256_identical": len(pe_set) == 1,
        "all_private_zip_sha256_claims_identical": len(zip_set) == 1,
        "source_matches_expected": (None if expected_source is None
                                    else source_set == {expected_source}),
        "private_zip_claim_matches_expected": (None if expected_zip is None
                                             else zip_set == {expected_zip}),
        "pairwise": pairwise,
        "upload_privacy_review_required": any(r["contains_raw_game_state"] for r in rows),
        "release_gate_credit": 0,
        "limits": [
            "ZIP sidecar, private ZIP hash and source are producer-supplied claims.",
            "This audit independently rehashes retained public PE, manifest and binding bytes only.",
            "Raw SRAM snapshots may contain game state; no user-data absence claim is made.",
            "Source-identical PE builds may differ in COFF timestamp and private ZIP identity.",
            "No private playable ZIP, gameplay parity, physical Windows device or legal rights review.",
        ],
    }


def markdown(result):
    lines = ["# Independent ROM-free Windows audit", "",
             "Read-only byte audit; release gate credit = 0.",
             "Same source claim: " + str(result["all_source_claims_identical"]),
             "Same executable digest: " + str(result["all_exe_sha256_identical"]),
             "Same private ZIP digest claim: " + str(result["all_private_zip_sha256_claims_identical"]),
             "Expected source: " + str(result["source_matches_expected"]),
             "Expected private ZIP: " + str(result["private_zip_claim_matches_expected"]),
             "Saved-game snapshot privacy review required: "
             + str(result["upload_privacy_review_required"]), ""]
    for i, item in enumerate(result["artifacts"]):
        lines.append(f"- Artifact {i}: source {item['source_commit_claim']}, "
                     f"PE {item['staged_exe_sha256']}, "
                     f"private ZIP SHA256 claim {item['private_portable_zip_sha256_claim']}, "
                     f"SRAM snapshots {item['raw_sram_snapshot_count']}")
    for item in result["pairwise"]:
        lines.append(f"- Pair {item['left']}/{item['right']}: "
                     f"{item['different_byte_count']} differing PE bytes; "
                     f"timestamp-only {item['only_coff_timestamp_bytes_differ']}")
    lines.extend(["", "No release, source parity or hardware acceptance follows from this audit."])
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifacts", nargs="+", type=Path)
    p.add_argument("--expected-source")
    p.add_argument("--expected-private-zip")
    p.add_argument("--json-out", type=Path)
    p.add_argument("--markdown-out", type=Path)
    args = p.parse_args()
    result = compare(args.artifacts, expected_source=args.expected_source,
                     expected_zip=args.expected_private_zip)
    view = markdown(result)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(view)
    print(view, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
