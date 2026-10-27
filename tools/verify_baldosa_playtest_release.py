#!/usr/bin/env python3
"""Verify a provisional, ROM-free Windows playtest ZIP from hosted acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

import audit_baldosa_romless_candidate as audit
import bind_baldosa_candidate_receipt as binding

ZIP = "UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip"
SIDECAR = ZIP + ".sha256"
EXE = "UniracersSNESRecomp.exe"
FIXTURE = "ur-baldosa-modern-profile-fixture.exe"
EXPORT_NAMES = {EXE, FIXTURE, ZIP, "SHA256SUMS", "source-commit.txt"}
CANDIDATE_NAMES = {ZIP, SIDECAR}
BINDING_NAMES = {"candidate-binding.json"}
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError("UNSAFE_PLAYTEST_EXPORT: " + message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fixed_files(directory: Path, names: set[str]) -> dict[str, Path]:
    require(directory.is_dir() and not directory.is_symlink(),
            "expected existing artifact directory")
    require({entry.name for entry in directory.iterdir()} == names,
            "artifact file population mismatch")
    for name in names:
        file = directory / name
        require(file.is_file() and not file.is_symlink(),
                "missing or redirected artifact: " + name)
    return {name: directory / name for name in names}


def parse_sums(text: str) -> dict[str, str]:
    result = {}
    for line in text.splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})\s+[*]?([A-Za-z0-9._-]+)", line)
        require(match is not None, "malformed SHA256SUMS")
        name = match[2]
        require(name not in result, "repeated SHA256SUMS member")
        result[name] = match[1]
    require(set(result) == {EXE, FIXTURE, ZIP},
            "incomplete/unexpected SHA256SUMS population")
    return result


def prepare(*, exported: Path, candidate: Path, binding_root: Path,
            expected_sha: str, out: Path) -> dict:
    require(SHA_PATTERN.fullmatch(expected_sha) is not None,
            "source must be exact lowercase 40-character commit SHA")
    require(not out.exists() and not out.is_symlink(),
            "release output directory must not already exist")
    source_files = fixed_files(exported, EXPORT_NAMES)
    candidate_files = fixed_files(candidate, CANDIDATE_NAMES)
    receipt_file = fixed_files(binding_root, BINDING_NAMES)["candidate-binding.json"]
    require(source_files["source-commit.txt"].read_text(encoding="ascii") ==
            expected_sha + "\n", "shared build source revision differs from checkout")

    sums = parse_sums(source_files["SHA256SUMS"].read_text(encoding="ascii"))
    for name, value in sums.items():
        require(sha256(source_files[name]) == value,
                "exported source-bound artifact bytes differ: " + name)
    require(sha256(candidate_files[ZIP]) == sums[ZIP] and
            candidate_files[ZIP].read_bytes() == source_files[ZIP].read_bytes(),
            "candidate artifact differs from reusable Windows export")
    # GitHub's Windows runner emits GNU sha256sum's binary-mode '*name'
    # marker; Linux text-mode ' name' is equally canonical. Compare RAW
    # bytes to exactly those two fixed-basename, single-line encodings.
    # The ZIP was already rehashed above; neither a changed basename,
    # digest nor additional whitespace/newline is admitted.
    sidecar = candidate_files[SIDECAR].read_bytes()
    require(sidecar in (
        (sums[ZIP] + "  " + ZIP + "\n").encode("ascii"),
        (sums[ZIP] + " *" + ZIP + "\n").encode("ascii"),
    ), "candidate SHA256 sidecar is noncanonical")

    original_receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    authoritative = binding.bind(source_files[EXE], source_files[ZIP],
                                 candidate_files[SIDECAR], expected_sha)
    require(original_receipt == authoritative,
            "hosted Windows journey-to-ZIP binding receipt differs")
    contents = audit.inspect(candidate_files[ZIP], expected_revision=expected_sha,
                             expected_zip_sha256=sums[ZIP])
    require(contents["rom_bundled"] is False and
            contents["profile_data_bundled"] is False and
            contents["all_immutable_members_verified"] is True,
            "unsafe or incomplete ROM-free candidate")

    release = {
        "schema": "ur-windows-romfree-playtest-provenance/1",
        "source_commit": expected_sha,
        "zip_sha256": sums[ZIP],
        "tested_and_packaged_executable_sha256": sums[EXE],
        "fixture_sha256": sums[FIXTURE],
        "github_release_tag": "playtest-" + expected_sha[:12],
        "accepted_original_native_complete_events": 0,
        "independent_release_gates_accepted": 0,
        "physical_gamepad_or_audio_verified": False,
        "release_gate_credit": 0,
        "candidate_only": True,
        "not_a_certified_beta": True,
    }
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(candidate_files[ZIP], out / ZIP)
    shutil.copyfile(candidate_files[SIDECAR], out / SIDECAR)
    (out / "PLAYTEST-PROVENANCE.json").write_text(
        json.dumps(release, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tick = chr(96)
    (out / "RELEASE-NOTES.md").write_text(
        "# Uniracers native Windows ROM-free developer playtest\n\n"
        "This is a **provisional technical playtest**, not an accepted remaster, "
        "complete beta, stable release, or substitute for physical-controller testing.\n\n"
        "The ZIP contains **no copyrighted game ROM, save file or player data**. "
        "Supply your own legally obtained, exact USA Uniracers ROM dump "
        f"({tick}Uniracers_USA.sfc{tick}) inside the extracted folder, then launch "
        f"{tick}run-baldosa-modern.cmd{tick} on Windows x64.\n\n"
        "Verified in GitHub Actions: the compiled executable, ZIP manifest and "
        "the binary used by the original 1P/2P scripted Windows acceptance "
        "journeys have matching source and SHA-256 identities. "
        "This does **not** verify physical controllers, audio output, all courses, "
        "every Modern destination or crash/power-loss recovery.\n\n"
        f"**Exact source SHA:** {tick}{expected_sha}{tick}  \n"
        f"**ZIP SHA-256:** {tick}{sums[ZIP]}{tick}  \n"
        f"**Executable SHA-256:** {tick}{sums[EXE]}{tick}\n\n"
        "Review PLAYTEST-PROVENANCE.json and the accompanying .sha256 before testing. "
        "Progress and stored results are provisional; use a fresh/disposable "
        "user-data root for feedback.\n\n"
        "No original/native complete-course event or independent release-quality "
        "gate is accepted merely by publishing this preview.\n\n"
        "## Current physical test sequence (use one source and one unchanged ZIP)\n\n"
        "1. Record the exact source/ZIP/EXE SHA-256 values above. On Windows PowerShell "
        "5.1, run `Get-FileHash -Algorithm SHA256 "
        ".\\UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip` before extraction; compare "
        "to PLAYTEST-PROVENANCE.json and the adjacent .sha256. After extraction, hash "
        "UniracersSNESRecomp.exe and compare to the same provenance. Stop on any "
        "identity disagreement. The downloaded Actions wrapper ZIP has a different "
        "hash from this playable ZIP.\n\n"
        "2. Extract into a NEW folder, supply your own exact USA ROM locally, and "
        "run the packaged CMD from File Explorer or cmd.exe. Set a fresh disposable "
        "UR_RECOMP_USER_DATA_ROOT outside the extracted folder for recovery tests. "
        "Never bypass ROM validation or reuse the only copy of a personal save.\n\n"
        "3. On actual hardware: let title idle into original attract and wake; use "
        "one physical controller to enter all five Modern destinations and Back; "
        "finish a real 1P race, inspect Records/Next Event, exit and cold-reopen; "
        "connect TWO distinct controllers, finish a 2P race and revisit both "
        "players' results; test Options, physical audio and display/4K if present. "
        "Record not-run cases rather than claiming they passed.\n\n"
        "4. Rehash the same portable ZIP and extracted EXE after play. For a defect, "
        "report source, ZIP and EXE SHA-256, test step, controller/Windows/GPU/audio "
        "context, steps to reproduce, expected and observed result and scrubbed "
        "logs/screenshots. Do not send ROMs, SRAM, private profile data or "
        "identifying machine details.\n\n"
        "Full current-build instructions and criterion mapping: "
        "https://github.com/gamesbyian/UR-Recomp/blob/main/docs/"
        "WINDOWS-PLAYTEST-INSTRUCTIONS.md\n\n"
        "Copy the single-candidate H01-H07 results sheet before the session: "
        "https://github.com/gamesbyian/UR-Recomp/blob/main/docs/"
        "WINDOWS-PLAYTEST-RESULTS-TEMPLATE.md\n\n"
        "This provisional preview does not independently certify any of the "
        "12 formal release gates or 45 original/native event matches.\n",
        encoding="utf-8",
    )
    return release


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exported", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--binding-root", type=Path, required=True)
    p.add_argument("--expected-sha", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = prepare(exported=args.exported, candidate=args.candidate,
                     binding_root=args.binding_root, expected_sha=args.expected_sha,
                     out=args.out)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
