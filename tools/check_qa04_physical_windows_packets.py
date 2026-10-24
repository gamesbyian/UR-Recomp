#!/usr/bin/env python3
"""Independent preflight of PRIVATE, human-authored Windows hardware witness packets.

Verifies source/package identity, three dissimilar installations and hashed
supporting files. Never certifies that observations are genuine or admits a
release gate. The QA-04 ledger and independent physical reviewers own that.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
import re
import unicodedata

from validate_release_quality_ledger import qa04_physical_coverage

SHA = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
KINDS = frozenset(("portable-verifier", "startup-log", "controller-p1",
                   "controller-p2", "audio-output", "visible-display",
                   "played-journey"))
REQUIRED_PHYSICAL = KINDS
REQUIRED_VM = frozenset(("portable-verifier", "startup-log", "played-journey"))
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
RECEIPT_FIELDS = frozenset((
    "schema", "layer", "source_commit", "artifact_sha256",
    "tested_executable_sha256", "zip_sha256_before_launch",
    "zip_sha256_after_launch", "pe_sha256_before_launch",
    "pe_sha256_after_launch", "package_unchanged_after_launch",
    "independent_review_completed", "operator_notes", "hardware",
    "attachments",
))
HARDWARE_FIELDS = frozenset((
    "setup_id", "environment", "clean_environment", "windows_version",
    "gpu", "display", "controller", "audio", "physical_controller_observed",
    "audible_output_observed", "visible_display_observed",
))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError("QA04_PACKET_REJECTED: " + message)


def unique_json_fields(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bound_sha256(path: Path, root: Path, expected_size: int) -> str:
    """Hash an attachment through ONE opened handle and refuse if it moved.

    Closes the check-then-read gap in ``safe_member``: the file is opened
    without following a leaf symlink, validated with ``fstat`` (regular file,
    single link, expected size), hashed from that same handle, and the path
    plus every ancestor up to ``root`` must still name the same filesystem
    objects afterwards. This detects a swap during the read on every host; it
    is not a Windows directory-handle walk and gives no proof against a writer
    that restores the original objects before the final check.
    """
    chain = [path]
    while chain[-1] != root:
        require(chain[-1].parent != chain[-1], "evidence path escaped packet root")
        chain.append(chain[-1].parent)

    def identity(item: Path) -> tuple[int, int]:
        info = os.lstat(item)
        return info.st_dev, info.st_ino

    try:
        before = [identity(item) for item in chain]
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                     | getattr(os, "O_BINARY", 0))
    except OSError:
        require(False, "evidence file missing or redirected")
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                and info.st_size == expected_size
                and (info.st_dev, info.st_ino) == before[0],
                "attached original source bytes changed or oversized")
        digest = hashlib.sha256()
        remaining = expected_size
        while remaining:
            chunk = stream.read(min(remaining, 1024 * 1024))
            require(bool(chunk), "attached original source bytes changed or oversized")
            digest.update(chunk)
            remaining -= len(chunk)
        require(stream.read(1) == b"",
                "attached original source bytes changed or oversized")
    try:
        after = [identity(item) for item in chain]
    except OSError:
        require(False, "evidence path changed while being read")
    require(after == before, "evidence path changed while being read")
    return digest.hexdigest()


def safe_member(root: Path, name: object) -> Path:
    require(type(name) is str and bool(name) and "\\" not in name
            and not name.startswith("/") and "\x00" not in name
            and ":" not in name and not any(ch in name for ch in "*?<>|"),
            "invalid evidence relative path")
    parts = name.split("/")
    require(len(parts) <= 6 and all(p not in ("", ".", "..") for p in parts)
            and not name.endswith("/") and PurePosixPath(name).parts == tuple(parts),
            "evidence path traversal or alias")
    # Refuse aliases that Linux accepts but Win32 cannot reopen faithfully.
    for part in (root.name, *parts):
        stem = part.split('.', 1)[0].upper().translate(str.maketrans('¹²³', '123'))
        # CLOCK$ is a legacy DOS device alias. Keep private witness paths
        # conservative across Windows versions and reviewers' filesystems.
        reserved = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
, 'CONOUT
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
, 'CLOCK
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
}
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
, 'CONOUT        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
, 'CONOUT
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
, 'CLOCK
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
}
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
, 'CLOCK        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
, 'CONOUT
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
, 'CLOCK
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
}
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
}
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
, 'CONOUT
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
, 'CLOCK
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
}
        reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
        # Reject invalid Unicode before UTF-16 encoding, so malformed
        # surrogate evidence is a controlled QA04 refusal on every host.
        require(bool(part) and not part.endswith((' ', '.'))
                and unicodedata.normalize('NFC', part) == part
                and not any(unicodedata.category(ch) in ('Cc', 'Cf', 'Cs')
                            or ch in '<>:"|?*\\/' for ch in part)
                and len(part.encode('utf-16-le')) // 2 <= 255
                and stem == stem.strip(' ')
                and stem not in reserved,
                "nonportable Win32 attachment or packet root name")
    # Refuse symlinked receipt roots and any redirected ancestor, not just
    # symlinks below an otherwise trusted root. This is a path preflight,
    # not an atomic descriptor proof against a concurrent filesystem writer.
    require(root.is_dir() and root.resolve(strict=True) == root.absolute(),
            "symlinked/noncanonical evidence packet root or ancestor")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "symlinked evidence file or directory")
    require(path.is_file() and not path.is_symlink(),
            "evidence file missing or redirected")
    # A hardlink has distinct path identity but shared mutable bytes.
    # Fail closed instead of treating it as independent local evidence.
    require(path.stat().st_nlink == 1,
            "hardlinked evidence attachment lacks independent file identity")
    return path


def inspect_packet(path: Path, *, commit: str, zip_sha: str,
                   pe_sha: str) -> tuple[dict, dict]:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_nlink == 1
            and 0 < path.stat().st_size <= 1024 * 1024,
            "missing/unsafe or hardlinked receipt JSON")
    receipt = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json_fields)
    require(type(receipt) is dict
            and receipt.get("schema") == "ur-windows-physical-witness/1",
            "unrecognized witness receipt")
    require(not any(key in receipt for key in (
        "release_gate_credit", "gate_passed", "physical_hardware_verified",
        "independently_accepted", "release_decision")),
        "producer may not self-admit release gates")
    require(set(receipt) == RECEIPT_FIELDS,
            "receipt has missing, extra or forbidden metadata fields")
    require(receipt.get("layer") == "L5",
            "hardware source evidence must be recorded at L5")
    for key, expected in (("source_commit", commit),
                          ("artifact_sha256", zip_sha),
                          ("tested_executable_sha256", pe_sha)):
        require(receipt.get(key) == expected, "stale/mixed candidate: " + key)
    require(receipt.get("package_unchanged_after_launch") is True,
            "no immutable package-after-launch observation")
    require(receipt.get("zip_sha256_before_launch") == zip_sha
            and receipt.get("zip_sha256_after_launch") == zip_sha
            and receipt.get("pe_sha256_before_launch") == pe_sha
            and receipt.get("pe_sha256_after_launch") == pe_sha,
            "inconsistent before/after package hashes")
    hw = receipt.get("hardware")
    require(type(hw) is dict and set(hw) == HARDWARE_FIELDS,
            "hardware metadata fields must be explicit and privacy-bounded")
    require(type(hw.get("setup_id")) is str
            and bool(hw["setup_id"].strip())
            and type(hw.get("environment")) is str
            and hw["environment"] in ("physical", "isolated-clean-vm")
            and type(hw.get("clean_environment")) is bool,
            "unidentified setup/environment/clean status")
    require(all(type(hw.get(k)) is str and hw[k].strip()
                for k in ("windows_version", "gpu", "display", "controller", "audio")),
            "missing recorded OS, graphics, display, controller or audio identity")
    for flag in ("physical_controller_observed", "audible_output_observed",
                 "visible_display_observed"):
        require(type(hw.get(flag)) is bool, "nonboolean observation: " + flag)
    # No automated probe can prove a real device was operated. Human-authored
    # observations must remain separately reviewable, and cannot be signed off
    # by data submitted by the same machine.
    require(type(receipt.get("operator_notes")) is str
            and bool(receipt["operator_notes"].strip())
            and receipt.get("independent_review_completed") is False,
            "missing operator notes or improper reviewer signoff")
    attachments = receipt.get("attachments")
    require(type(attachments) is list and attachments,
            "missing original, local supporting evidence")
    observed_kinds, observed_files, total = set(), set(), 0
    for item in attachments:
        require(type(item) is dict and set(item) == {"path", "sha256", "bytes", "kind"},
                "unrecognized/partial evidence attachment")
        kind, digest, size = item["kind"], item["sha256"], item["bytes"]
        require(kind in KINDS and kind not in observed_kinds,
                "duplicate/unrecognized evidence kind")
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0 < size <= MAX_FILE_BYTES,
                "invalid attachment hash or bounded size")
        filename = item["path"]
        require(type(filename) is str, "evidence path must be a relative filename")
        require(filename.casefold() not in observed_files,
                "duplicated or Windows-case-alias evidence path")
        observed_kinds.add(kind)
        observed_files.add(filename.casefold())
        original = safe_member(path.parent, filename)
        require(str(original.resolve()).casefold() not in observed_files,
                "aliased evidence source file")
        observed_files.add(str(original.resolve()).casefold())
        total += size
        require(total <= MAX_TOTAL_BYTES, "attached original source bytes changed or oversized")
        require(bound_sha256(original, path.parent, size) == digest,
                "attached original source bytes changed or oversized")
    needed = REQUIRED_PHYSICAL if hw["environment"] == "physical" else REQUIRED_VM
    require(needed <= observed_kinds, "missing independent observations: " +
            ",".join(sorted(needed - observed_kinds)))
    if hw["environment"] == "physical":
        require(all(hw[flag] is True for flag in (
            "physical_controller_observed", "audible_output_observed",
            "visible_display_observed")),
            "the physical tester has not observed all three device classes")
    else:
        require(hw["clean_environment"] is True,
                "isolated VM must be a clean installation")
    return receipt, {"setup_id": hw["setup_id"], "environment": hw["environment"],
                     "attachment_count": len(attachments),
                     "attachment_bytes": total,
                     "attached_kind_names": sorted(observed_kinds),
                     "attachment_digest_by_kind": {
                         item["kind"]: item["sha256"] for item in attachments
                     },
                     "local_attachment_sha256_verified": True}


def audit(paths: list[Path], *, source_sha: str,
          portable_zip_sha: str, executable_sha: str) -> dict:
    require(type(source_sha) is str and COMMIT.fullmatch(source_sha) is not None
            and type(portable_zip_sha) is str and SHA.fullmatch(portable_zip_sha) is not None
            and type(executable_sha) is str and SHA.fullmatch(executable_sha) is not None,
            "exact independent source/ZIP/PE pins required")
    require(len(paths) == 3 and len({str(p.resolve()) for p in paths}) == 3,
            "exactly three separate packet paths required")
    receipts, summaries = [], []
    for path in paths:
        witness, summary = inspect_packet(path, commit=source_sha,
                                           zip_sha=portable_zip_sha,
                                           pe_sha=executable_sha)
        receipts.append(witness)
        summaries.append(summary)
    all_attachment_digests = [
        digest for summary in summaries
        for digest in summary["attachment_digest_by_kind"].values()
    ]
    require(len(set(all_attachment_digests)) == len(all_attachment_digests),
            "same original evidence bytes reused across independent setups")
    require(qa04_physical_coverage(receipts),
            "not three dissimilar source-bound L5 physical/clean-machine setups")
    return {
        "schema": "ur-qa04-packet-preflight/1",
        "exact_source_sha": source_sha,
        "exact_playable_zip_sha256": portable_zip_sha,
        "exact_executable_sha256": executable_sha,
        "original_private_attachments_hash_verified": True,
        "structural_three_setup_coverage": True,
        "setups": summaries,
        "independent_hardware_observation_certified_by_tool": False,
        "original_native_course_fidelity_certified_by_tool": False,
        "release_gate_credit": 0,
        "next_step": "Separate human reviewers must observe the devices, "
                     "inspect logs/screenshots and adjudicate QA-04 on the ledger",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipts", nargs=3, type=Path,
                   help="exactly three PRIVATE per-setup receipt JSON files")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--portable-zip-sha256", required=True)
    p.add_argument("--executable-sha256", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.receipts, source_sha=args.source_sha,
                           portable_zip_sha=args.portable_zip_sha256,
                           executable_sha=args.executable_sha256), indent=2,
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
