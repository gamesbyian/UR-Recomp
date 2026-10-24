#!/usr/bin/env python3
"""Read-only consistency audit for two *previously built* Windows Actions ZIPs.

No ROM or raw log is extracted to the evidence output. A successful audit
means only the two stored artifact wrappers agree with a canonical inner
portable ZIP. It cannot authenticate GitHub Actions provenance, independent
release nomination, guest event parity, or Windows physical-device behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import tempfile
import zipfile
from pathlib import Path

try:
    from tools import assemble_windows_package as package
    from tools.evidence_contract import assertion, make_envelope
except ModuleNotFoundError:
    import assemble_windows_package as package
    from evidence_contract import assertion, make_envelope

PORTABLE_MEMBERS = {
    "UR-Recomp-Windows-x64.zip",
    "UR-Recomp-Windows-x64.zip.sha256",
    "Test-URRecompPortable.ps1",
}
SMOKE_MANIFEST = f"{package.ARCHIVE_ROOT}/{package.MANIFEST_NAME}"
MAX_TRANSPORT_BYTES = 256 * 1024 * 1024


def _read(archive: zipfile.ZipFile, member: str, *, limit: int) -> bytes:
    try:
        info = archive.getinfo(member)
    except KeyError as exc:
        raise ValueError(f"missing archived evidence member: {member}") from exc
    if info.file_size > limit:
        raise ValueError(f"oversized archived evidence member: {member}")
    return archive.read(info)


def _check_indexed_local_records(path: Path, archive: zipfile.ZipFile) -> None:
    """Reject local ZIP data not included in the central member inventory.

    This is bounded by the already-limited 250 transport members and reads
    only local headers/names/descriptors, not compressed file payloads.
    A ZIP's central directory can omit a complete local-only record while
    every indexed member still passes CRC and name checks.
    """
    cursor = 0
    with path.open("rb") as stream:
        for info in sorted(archive.infolist(), key=lambda item: item.header_offset):
            if info.header_offset != cursor:
                raise ValueError("noncanonical transport ZIP local member layout")
            stream.seek(cursor)
            header = stream.read(30)
            if len(header) != 30 or header[:4] != b"PK\x03\x04":
                raise ValueError("noncanonical transport ZIP local member header")
            flags, method = struct.unpack_from("<HH", header, 6)
            name_len, extra_len = struct.unpack_from("<HH", header, 26)
            if flags != info.flag_bits or method != info.compress_type:
                raise ValueError("noncanonical transport ZIP local member metadata")
            name = stream.read(name_len)
            if name.decode("utf-8" if flags & 0x800 else "cp437") != info.filename:
                raise ValueError("noncanonical transport ZIP local member name")
            cursor += 30 + name_len + extra_len + info.compress_size
            if flags & 8:
                stream.seek(cursor)
                has_signature = stream.read(4) == b"PK\x07\x08"
                if has_signature:
                    cursor += 4
                stream.seek(cursor)
                suffix = stream.read(20)
                expected = (info.CRC, info.compress_size, info.file_size)
                if len(suffix) >= 12 and struct.unpack_from("<III", suffix) == expected:
                    cursor += 12
                elif len(suffix) == 20 and struct.unpack_from("<IQQ", suffix) == expected:
                    cursor += 20
                else:
                    raise ValueError("noncanonical transport ZIP data descriptor")
        if cursor != archive.start_dir:
            raise ValueError("noncanonical transport ZIP unindexed local bytes")


def _open_transport(path: Path, *, exactly: set[str] | None = None) -> zipfile.ZipFile:
    if not path.is_file() or not 22 <= path.stat().st_size <= MAX_TRANSPORT_BYTES:
        raise ValueError("missing or oversized transport artifact")
    # A ZIP central directory can describe an apparently exact member set
    # even when the file has a self-extracting prefix, unindexed local
    # records, a comment or an opaque trailer. Windows Actions evidence
    # wrappers have no reason to carry any of these additional bytes.
    with path.open("rb") as source:
        first = source.read(4)
        source.seek(-22, 2)
        end = source.read(22)
    if (first != b"PK\x03\x04" or end[:4] != b"PK\x05\x06" or
            end[-2:] != b"\x00\x00"):
        raise ValueError("noncanonical transport ZIP envelope")
    archive = zipfile.ZipFile(path)
    names = archive.namelist()
    if len(names) > 250 or len(names) != len(set(names)) or not names or (
        exactly is not None and set(names) != exactly
    ):
        archive.close()
        raise ValueError("duplicate, excessive or unexpected transport members")
    try:
        _check_indexed_local_records(path, archive)
    except (ValueError, UnicodeError, struct.error):
        archive.close()
        raise
    return archive


def audit(
    portable_artifact: Path, smoke_artifact: Path,
    *, expected_source: str | None = None, expected_zip_sha256: str | None = None,
) -> dict:
    """Cross-check archived portable bytes and emit *inconclusive* evidence."""
    if (expected_source is None) != (expected_zip_sha256 is None):
        raise ValueError("both exact candidate pins must be supplied together")
    if expected_source is not None:
        if not re.fullmatch(r"[0-9a-f]{40}", expected_source):
            raise ValueError("candidate source pin must be 40 lowercase hex")
        if not re.fullmatch(r"[0-9a-f]{64}", expected_zip_sha256):
            raise ValueError("candidate ZIP pin must be 64 lowercase hex")
    with _open_transport(portable_artifact, exactly=PORTABLE_MEMBERS) as portable:
        inner = _read(portable, "UR-Recomp-Windows-x64.zip", limit=MAX_TRANSPORT_BYTES)
        sidecar = _read(portable, "UR-Recomp-Windows-x64.zip.sha256", limit=1024)
    inner_sha = hashlib.sha256(inner).hexdigest()
    if expected_zip_sha256 is not None and inner_sha != expected_zip_sha256:
        raise ValueError("archived inner ZIP differs from nominated candidate")
    if sidecar != f"{inner_sha}  UR-Recomp-Windows-x64.zip\n".encode("ascii"):
        raise ValueError("transport sidecar does not match inner portable ZIP")
    # Reuse the existing canonical producer/consumer archive oracle, not
    # a replacement package parser. No ROM is separately extracted.
    with tempfile.TemporaryDirectory(prefix="ur-smoke-archive-audit-") as temp:
        inner_path = Path(temp) / "UR-Recomp-Windows-x64.zip"
        inner_path.write_bytes(inner)
        manifest = package.verify_archive(inner_path)
    if expected_source is not None and manifest["source_revision"] != expected_source:
        raise ValueError("archived source differs from nominated candidate")
    with _open_transport(smoke_artifact) as smoke:
        another = _read(smoke, "UR-Recomp-Windows-x64.zip", limit=MAX_TRANSPORT_BYTES)
        another_sidecar = _read(smoke, "UR-Recomp-Windows-x64.zip.sha256", limit=1024)
        manifest_raw = _read(smoke, SMOKE_MANIFEST, limit=8 * 1024 * 1024)
        if another != inner or another_sidecar != sidecar:
            raise ValueError("smoke package bytes differ from the portable artifact")
        if json.loads(manifest_raw.decode("utf-8")) != manifest:
            raise ValueError("smoke manifest differs from inner portable ZIP")
        pad_log = _read(smoke, "qa09-root-win32.log", limit=5*1024*1024).decode("utf-8", "replace")
        race_log = _read(smoke, "package-race-result.log", limit=5*1024*1024).decode("utf-8", "replace")
        verify_log = _read(smoke, "standalone-windows-verifier.log", limit=5*1024*1024).decode("utf-8", "replace")
    pads = re.search(r"\[Gamepad\] SDL reports (\d+) joystick\(s\)", pad_log)
    audio = re.search(r"SDL init ok: video=([^\s]+) audio=([^\s]+)", pad_log)
    return make_envelope(
        evidence_type="archived-windows-smoke-artifact-consistency",
        producer="tools/audit_windows_smoke_artifact.py",
        subject={
            "unapproved_source_commit_claim": manifest["source_revision"],
            "inner_portable_zip_sha256": inner_sha,
        },
        inputs={
            "portable_transport_basename": portable_artifact.name,
            "smoke_transport_basename": smoke_artifact.name,
        },
        assertions=[
            assertion("inner-zip-checksum-equals-transport-sidecar", True),
            assertion("inner-shipping-archive-canonical", True),
            assertion("smoke-and-portable-zip-bytes-equal", True),
            assertion("smoke-and-portable-manifest-equal", True),
        ],
        outcome="inconclusive",
        metrics={
            "qa09_reported_joystick_count": int(pads.group(1)) if pads else None,
            "qa09_video_driver": audio.group(1) if audio else None,
            "qa09_audio_driver": audio.group(2) if audio else None,
            # The real Windows SDL name is uppercase and truncated to 16
            # visible bytes: "UR_CONTROLLER ... name=UR HOTPLUG ACCEPTA".
            # Do not silently misclassify actual synthetic-pad evidence.
            "qa09_synthetic_pad_label_observed": bool(re.search(
                r"(?im)^UR_CONTROLLER SEAT_CONNECTED seat=1 name=UR HOTPLUG ACCEPTA(?:\s|$)",
                pad_log,
            )),
            "logged_package_race_record_capture": "UR_RUN_RECORD CAPTURED" in race_log,
            "logged_standalone_manifest_verified": "UR_PORTABLE_MANIFEST_VERIFIED" in verify_log,
            "nominated_candidate_pins_matched": expected_source is not None,
            "independent_candidate_approved": False,
            "physical_hardware_verified": False,
            "current_native_1p_2p_journeys_verified": False,
        },
        provenance={"scope": "historical-archive-self-consistency-not-l4-or-l5"},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("portable_artifact", type=Path)
    parser.add_argument("smoke_artifact", type=Path)
    parser.add_argument("--expected-source", help="externally nominated 40-hex source commit (paired)")
    parser.add_argument("--expected-zip-sha256", help="externally nominated inner portable ZIP digest (paired)")
    parser.add_argument("--output", type=Path, help="write ROM-free structured evidence")
    args = parser.parse_args()
    try:
        report = audit(
            args.portable_artifact, args.smoke_artifact,
            expected_source=args.expected_source,
            expected_zip_sha256=args.expected_zip_sha256,
        )
    except (OSError, ValueError, KeyError, UnicodeError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    result = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
