#!/usr/bin/env python3
"""Independent fail-closed archive proof: RF062 only added three dump commands.

A replay command-script digest may legitimately change with extra *observer*
dumps. This audit checks both authentic ZIP bytes, the full script and both
original/native input files. It does not execute Snes9x/native games and
does not grant cold-record qualification, original/native frame equivalence,
or an accepted USA event.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

SCHEMA = "ur-qa01-independent-rf062-dump-only-script-identity/1"
BASE_ZIP_SHA = "239d606436f47631e146fe8b7e66b2284f366f9321099711b0c0244af01cb927"
CANDIDATE_ZIP_SHA = "85b8585539001210e4a9d2b22e5484034679fbda5d40808300d221e1ec583aed"
SCRIPT = "work/zoom-zoo/replay/complete.script"
SOURCE_INPUTS = (
    "work/zoom-zoo/replay/ref.input",
    "work/zoom-zoo/replay/pinned-baldosa.input",
)
OLD_SCRIPT_SHA = "1eb3e8416b7fa40935d097c78d281ca98537c9a555e23f1906a99912dcdb2c52"
NEW_SCRIPT_SHA = "92012c94af3a27c54144e34c9d1d7a6cdb97ddf3e519d3f24c375c7c76bf6bc2"
BASE_SEGMENT = ("dump scene-05100", "wait 20", "dump scene-05120")
CANDIDATE_SEGMENT = (
    "dump scene-05100",
    "wait 5", "dump qa01-frame-005105",
    "wait 1", "dump qa01-frame-005106",
    "wait 1", "dump qa01-frame-005107",
    "wait 13", "dump scene-05120",
)
ADDED_DUMPS = tuple(x.split(" ", 1)[1] for x in CANDIDATE_SEGMENT
                    if x.startswith("dump qa01-frame-"))


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lines(data: bytes) -> list[str]:
    try:
        text = data.decode("ascii")
    except UnicodeError as error:
        raise ValueError("replay script is not authentic ASCII") from error
    require(text.endswith("\n") and "\r" not in text
            and not any(not line or line.strip() != line
                        for line in text.splitlines()),
            "replay command-script line structure changed")
    return text.splitlines()


def command_timeline(rows: list[str]) -> tuple:
    """Retain every real command and cumulative 'wait' before it.

    A newly added dump is deliberately ignored only for this *timeline*.
    The separate exact full-script segment check ensures no new commands,
    changes to wait order, altered controller actions, or extra dumps.
    """
    elapsed = 0
    result = []
    for row in rows:
        tokens = row.split(" ")
        if tokens[0] == "wait":
            require(len(tokens) == 2 and tokens[1].isdigit()
                    and int(tokens[1]) > 0,
                    "invalid guest replay wait command")
            elapsed += int(tokens[1])
        else:
            require(tokens[0] in ("dump", "until", "press", "quit"),
                    "unknown guest replay command")
            result.append((elapsed, row))
    return tuple(result), elapsed


def equivalent_scripts(old_bytes: bytes, new_bytes: bytes) -> dict:
    old, new = lines(old_bytes), lines(new_bytes)
    require(old.count(BASE_SEGMENT[0]) == old.count(BASE_SEGMENT[-1]) == 1,
            "original frozen source script boundary missing")
    require(new.count(CANDIDATE_SEGMENT[0]) ==
            new.count(CANDIDATE_SEGMENT[-1]) == 1,
            "candidate source script boundary missing")
    i = old.index(BASE_SEGMENT[0])
    j = new.index(CANDIDATE_SEGMENT[0])
    require(tuple(old[i:i + len(BASE_SEGMENT)]) == BASE_SEGMENT and
            tuple(new[j:j + len(CANDIDATE_SEGMENT)]) == CANDIDATE_SEGMENT and
            old[:i] == new[:j] and
            old[i + len(BASE_SEGMENT):] ==
            new[j + len(CANDIDATE_SEGMENT):],
            "script changed beyond the exact three dump insertions and wait split")
    # Compare *timeline* without the new read-only dumps; their presence is
    # constrained byte-for-byte by the above exact contiguous segment proof.
    significant_old, elapsed_old = command_timeline(old)
    significant_new, elapsed_new = command_timeline([
        row for row in new if row not in
        {f"dump {name}" for name in ADDED_DUMPS}])
    require(significant_old == significant_new and
            elapsed_old == elapsed_new,
            "controller commands or source-script wait-frame schedule changed")
    require(sum(int(row.split()[1]) for row in
                CANDIDATE_SEGMENT if row.startswith("wait ")) == 20,
            "source 20-frame wait budget changed")
    return {
        "unchanged_source_controller_and_standard_dump_command_timeline": True,
        "unchanged_wait_frame_budget": elapsed_old,
        "exact_new_observer_dumps": list(ADDED_DUMPS),
        "observer_dump_positions_are_source_relative_after_5100": [5105, 5106, 5107],
        "actual_original_script_sha256": sha(old_bytes),
        "actual_new_script_sha256": sha(new_bytes),
        "ordinary_dump_wait_and_controller_commands_unchanged": True,
    }


def open_zip(path: Path, digest: str) -> zipfile.ZipFile:
    require(sha(path.read_bytes()) == digest, "source archive SHA256 is not pinned")
    zipped = zipfile.ZipFile(path)
    files = zipped.infolist()
    require(len(files) <= 1000
            and len(files) == len({item.filename for item in files})
            and all(not item.is_dir() and not item.filename.startswith("/")
                    and ".." not in Path(item.filename).parts
                    and item.file_size <= 2_000_000 for item in files)
            and zipped.testzip() is None,
            "original/native source ZIP corrupt, duplicate or unsafe")
    return zipped


def audit(original_zip: Path, dump_zip: Path) -> dict:
    with open_zip(original_zip, BASE_ZIP_SHA) as before, \
         open_zip(dump_zip, CANDIDATE_ZIP_SHA) as after:
        a, b = before.read(SCRIPT), after.read(SCRIPT)
        require(sha(a) == OLD_SCRIPT_SHA and sha(b) == NEW_SCRIPT_SHA,
                "pinned original replay command scripts changed")
        result = equivalent_scripts(a, b)
        inputs = {}
        for key in SOURCE_INPUTS:
            left, right = before.read(key), after.read(key)
            require(len(left) > 0 and left == right,
                    "original/native actual supplied controller input changed: " + key)
            inputs[Path(key).name] = {"bytes": len(left), "sha256": sha(left)}
        old_p, new_p = (json.loads(z.read("producer-report.json"))
                        for z in (before, after))
        stable = ("rom_sha256", "original_movie_sha256",
                  "original_movie_window_sha256", "source_sram_sha256",
                  "native_executable_sha256", "reference_entry", "native_entry",
                  "comparison", "zoo_race_mesh", "zoo_next_bowl_handoff")
        require(all(old_p.get(k) == new_p.get(k) for k in stable),
                "source input or observed bounded game controls changed")
        require(old_p.get("input_sha256") == OLD_SCRIPT_SHA and
                new_p.get("input_sha256") == NEW_SCRIPT_SHA and
                old_p.get("reference_script_sha256") == OLD_SCRIPT_SHA and
                new_p.get("reference_script_sha256") == NEW_SCRIPT_SHA,
                "command-script SHA is being confused with actual controller input")
        return {
            "schema": SCHEMA,
            "baseline_zip_sha256": BASE_ZIP_SHA,
            "candidate_zip_sha256": CANDIDATE_ZIP_SHA,
            **result,
            "exact_same_original_native_controller_input_file_bytes": inputs,
            "original_native_bounded_game_controls_unchanged": True,
            "original_core_build_identity_also_unchanged": False,
            "added_dump_directives_noninterfering_in_actual_CPU_execution_proven": False,
            "new_cold_record_approved": False,
            "first_consumed_original_native_divergent_byte_proven": False,
            "accepted_USA_events": 0,
            "release_QA_gates": 0,
            "adjudication": "SOURCE_SCRIPT_DELTA_ONLY_COLD_PROOF_HOLD",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.baseline, args.candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("RF062 dump-script-only provenance exact; cold proof HOLD, 0/45")


if __name__ == "__main__":
    main()
