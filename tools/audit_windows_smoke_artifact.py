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


def _open_transport(path: Path, *, exactly: set[str] | None = None) -> zipfile.ZipFile:
    if not path.is_file() or path.stat().st_size > MAX_TRANSPORT_BYTES:
        raise ValueError("missing or oversized transport artifact")
    archive = zipfile.ZipFile(path)
    names = archive.namelist()
    if len(names) > 250 or len(names) != len(set(names)) or (
        exactly is not None and set(names) != exactly
    ):
        archive.close()
        raise ValueError("duplicate, excessive or unexpected transport members")
    return archive


def audit(portable_artifact: Path, smoke_artifact: Path) -> dict:
    """Cross-check archived portable bytes and emit *inconclusive* evidence."""
    with _open_transport(portable_artifact, exactly=PORTABLE_MEMBERS) as portable:
        inner = _read(portable, "UR-Recomp-Windows-x64.zip", limit=MAX_TRANSPORT_BYTES)
        sidecar = _read(portable, "UR-Recomp-Windows-x64.zip.sha256", limit=1024)
    inner_sha = hashlib.sha256(inner).hexdigest()
    if sidecar != f"{inner_sha}  UR-Recomp-Windows-x64.zip\n".encode("ascii"):
        raise ValueError("transport sidecar does not match inner portable ZIP")
    # Reuse the existing canonical producer/consumer archive oracle, not
    # a replacement package parser. No ROM is separately extracted.
    with tempfile.TemporaryDirectory(prefix="ur-smoke-archive-audit-") as temp:
        inner_path = Path(temp) / "UR-Recomp-Windows-x64.zip"
        inner_path.write_bytes(inner)
        manifest = package.verify_archive(inner_path)
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
            "qa09_synthetic_pad_label_observed": "UR hotplug acceptance pad" in pad_log,
            "logged_package_race_record_capture": "UR_RUN_RECORD CAPTURED" in race_log,
            "logged_standalone_manifest_verified": "UR_PORTABLE_MANIFEST_VERIFIED" in verify_log,
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
    parser.add_argument("--output", type=Path, help="write ROM-free structured evidence")
    args = parser.parse_args()
    try:
        report = audit(args.portable_artifact, args.smoke_artifact)
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
