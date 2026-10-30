#!/usr/bin/env python3
"""Rehydrate a ROM-bearing Windows QA package *locally* from ROM-free evidence.

The producer retained only a PE, a canonical package manifest, and a binding
to the exact never-uploaded ZIP. A trusted Windows test runner has the canonical
ROM in its own checkout. This tool reconstructs the package only when the
result's manifest AND whole ZIP hashes equal the producer's original hashes.
It never uploads, downloads, or logs any ROM bytes or audio PCM.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path

from tools import assemble_windows_package as package

BINDING_SCHEMA = "ur-windows-smoke-romfree-pe-binding/1"
# The verified Windows package currently contains exactly one inert mod
# placeholder. Do not synthesize executable mods or guess unknown assets.
CURRENT_INERT_MOD = "mods/preloaded/packages/.gitkeep"
EXPECTED_FILES = frozenset({
    CURRENT_INERT_MOD,
    package.EXE_NAME,
    package.ROM_NAME,
    package.ROM_CONFIG_NAME,
    package.LAUNCHER_NAME,
    package.README_NAME,
})


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError(f"missing or oversized source metadata: {path.name}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"invalid metadata object: {path.name}")
    return obj


def rehydrate(
    artifact_root: Path, canonical_rom: Path, output_zip: Path,
    expected_source: str,
) -> dict:
    """Fail closed unless output ZIP is byte-identical to its original producer."""
    if not re.fullmatch(r"[0-9a-f]{40}", expected_source):
        raise ValueError("exact first-party producer source SHA is required")
    artifact_root = artifact_root.resolve()
    canonical_rom = canonical_rom.resolve()
    output_zip = output_zip.resolve()
    if not canonical_rom.is_file():
        raise ValueError("trusted runner's canonical ROM is missing")
    if output_zip.is_relative_to(artifact_root) and output_zip.name != (
        package.ARCHIVE_ROOT + ".zip"
    ):
        raise ValueError("unexpected output archive name")
    if not artifact_root.is_dir():
        raise ValueError("ROM-free source artifact directory is missing")
    exe = artifact_root / "windows-romfree-binary" / package.EXE_NAME
    binding_path = artifact_root / "windows-romfree-binary" / "binding.json"
    original_manifest_path = artifact_root / package.ARCHIVE_ROOT / package.MANIFEST_NAME
    original_sidecar = artifact_root / (package.ARCHIVE_ROOT + ".zip.sha256")
    binding = _read_object(binding_path)
    manifest = _read_object(original_manifest_path)

    if binding.get("schema") != BINDING_SCHEMA:
        raise ValueError("unknown Windows ROM-free executable binding schema")
    if binding.get("source_commit") != expected_source:
        raise ValueError("ROM-free executable source differs from selected main run")
    if manifest.get("source_revision") != expected_source:
        raise ValueError("original package manifest differs from producer SHA")
    if binding.get("original_zip_uploaded") is not False or (
        binding.get("rom_or_player_data_uploaded") is not False
    ):
        raise ValueError("source violates the ROM-free evidence contract")
    if not exe.is_file() or exe.stat().st_size != binding.get("executable_bytes"):
        raise ValueError("retained Windows PE size does not match binding")
    if _sha(exe) != binding.get("executable_sha256"):
        raise ValueError("retained Windows PE does not match producer SHA-256")
    if _sha(original_manifest_path) != binding.get("original_manifest_sha256"):
        raise ValueError("retained original package manifest does not match binding")

    original_zip_sha = binding.get("original_portable_zip_sha256")
    if not isinstance(original_zip_sha, str) or not re.fullmatch(
        r"[0-9a-f]{64}", original_zip_sha
    ):
        raise ValueError("original exact ZIP digest is missing or malformed")
    if original_sidecar.read_bytes() != (
        f"{original_zip_sha}  {package.ARCHIVE_ROOT}.zip\n".encode("ascii")
    ):
        raise ValueError("original ZIP checksum sidecar and binding disagree")
    entries = manifest.get("files")
    if not isinstance(entries, list) or {
        e.get("path") for e in entries if isinstance(e, dict)
    } != EXPECTED_FILES or len(entries) != len(EXPECTED_FILES):
        raise ValueError("unsupported producer assets; cannot infer unknown mods")
    mod_entry = next(e for e in entries if e["path"] == CURRENT_INERT_MOD)
    if mod_entry.get("size") != 0 or mod_entry.get("sha256") != hashlib.sha256(b"").hexdigest():
        raise ValueError("original mod placeholder is not inert")
    rom_entry = next(e for e in entries if e["path"] == package.ROM_NAME)
    if rom_entry.get("size") != canonical_rom.stat().st_size or (
        rom_entry.get("sha256") != _sha(canonical_rom)
    ):
        raise ValueError("runner's verified ROM differs from original producer")
    # Never replace an existing output before all source inputs are validated.
    if output_zip.exists():
        raise ValueError("output archive already exists")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ur-audio-rehydrate-", dir=output_zip.parent) as tmp:
        root = Path(tmp)
        inputs = root / "inputs"
        inputs.mkdir()
        shutil.copy2(exe, inputs / package.EXE_NAME)
        (inputs / package.ROM_CONFIG_NAME).write_bytes(package.ROM_CONFIG_BYTES)
        mod = inputs / CURRENT_INERT_MOD
        mod.parent.mkdir(parents=True)
        mod.write_bytes(b"")
        result = root / package.ARCHIVE_ROOT
        package.assemble(inputs, canonical_rom, result, expected_source)
        if (result / package.MANIFEST_NAME).read_bytes() != original_manifest_path.read_bytes():
            raise ValueError("reconstructed package manifest differs from producer")
        package.verify(result)
        staging_archive = root / (package.ARCHIVE_ROOT + ".zip")
        package.create_archive(result, staging_archive)
        package.verify_archive(staging_archive)
        if _sha(staging_archive) != original_zip_sha:
            raise ValueError("reconstructed ZIP differs from exact original producer")
        shutil.copy2(staging_archive, output_zip)
    return {
        "source_sha": expected_source,
        "archive_sha256": original_zip_sha,
        "executable_sha256": binding["executable_sha256"],
        "producer_exact_archive_match": True,
        "qa_credit": "none_pending_actual_execution",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--expected-source", required=True)
    args = parser.parse_args()
    result = rehydrate(
        args.artifact_root, args.rom, args.archive, args.expected_source
    )
    print("WINDOWS_AUDIO_REHYDRATE exact_zip_sha256=" +
          result["archive_sha256"] + " source_sha=" + result["source_sha"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
