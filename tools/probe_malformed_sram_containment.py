#!/usr/bin/env python3
"""Classify stock-guest boot behaviour for malformed battery SRAM.

Decision served: WORK-QUEUE expert-edge item (f). A Modern profile carries an
exact 8 KiB stock-SRAM mirror and installs it into the framework save
namespace. If that mirror (or the installed ``save.srm``) is malformed, does
the stock guest reformat it, partially reset it, or accept it? The answer
decides whether the host profile layer may keep treating the bytes as opaque
guest-owned state, and which stock predicate a live (boot-bypassing) install
must reproduce.

Discriminator: one cold boot per malformed class to the settled main menu
(``7E:009F = D7``), then compare live SRAM with what the framework loaded and
with the fresh-format image the same build writes when no ``save.srm`` exists.
Stop condition: every class is classified in Authentic (stock oracle) and in
the Modern profile-root path.

All fixtures are synthesized from the canonical clean stock image at run
time; no malformed binary is committed. ``synthesize``/``classify`` are pure
and unit-tested; ``main`` drives an already-built native candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN_SRAM = ROOT / "reference/imported/reverse-engineering/dessyreqt/SRAM/Clean.srm"
SRAM_BYTES = 8192

HEADER = (0x0000, 0x000C)  # "ASJIver3.30" + 0xFF, compared by 80:8C4E
RECORDS, RECORD_WORDS, RECORD_CHECKSUM = 0x0422, 150, 0x054E
RECORD_HOLDERS = 0x0550
MEDAL_BLOCK, MEDAL_WORDS, MEDAL_CHECKSUM = 0x05E8, 170, 0x073C
MEDAL_MIKE_CRAWLER = 0x069C
TOUR_FLAGS, TOUR_FLAG_COUNT = 0x1075, 50
PLAY_MODE = 0x10AD

# Seeded but checksum-valid "progressed" base, so that a reformat is visible.
BASE_MEDAL = 2  # MIKE holds Crawler silver
BASE_RECORD_INDEX = 0  # rank 0, Crawler, Dragster
BASE_RECORD_VALUE = 3000  # 30.00 s
BASE_RECORD_HOLDER = 0  # MIKE

REGIONS = {
    "header": HEADER,
    "records": (RECORDS, RECORD_CHECKSUM + 2),
    "record_holders": (RECORD_HOLDERS, RECORD_HOLDERS + RECORD_WORDS),
    "medal_block": (MEDAL_BLOCK, MEDAL_CHECKSUM + 2),
    "tour_flags": (TOUR_FLAGS, TOUR_FLAGS + TOUR_FLAG_COUNT),
    "play_mode": (PLAY_MODE, PLAY_MODE + 1),
}

MALFORMED_CLASSES = (
    "truncated_half",
    "empty_file",
    "oversized",
    "medal_checksum_mismatch",
    "records_checksum_mismatch",
    "medal_value_out_of_range",
    "record_value_out_of_range",
    "tour_flag_out_of_range",
    "play_mode_out_of_range",
    "header_signature_damaged",
)

# Bytes every non-formatting stock boot rewrites (static decode, bank 80/83
# listings): 83:8AF7 probes SRAM mirroring by storing word 0x3456 at 0x1FFF
# (0x2000 mirrors 0x0000, which it restores); 83:8B23 zeroes 0x0400-0x041F,
# the play mode 0x10AD and the tier mirror 0x10FD-0x110C.
STOCK_BOOT_WRITES = frozenset(
    {0x1FFF, PLAY_MODE, *range(0x0400, 0x0420), *range(0x10FD, 0x110D)}
)


def word(data: bytes | bytearray, offset: int) -> int:
    return data[offset] | data[offset + 1] << 8


def put_word(data: bytearray, offset: int, value: int) -> None:
    data[offset] = value & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF


def medal_checksum(data: bytes | bytearray) -> int:
    return sum(word(data, MEDAL_BLOCK + 2 * i) for i in range(MEDAL_WORDS)) & 0xFFFF


def records_checksum(data: bytes | bytearray) -> int:
    return sum(word(data, RECORDS + 2 * i) for i in range(RECORD_WORDS)) & 0xFFFF


def fix_checksums(data: bytearray) -> bytearray:
    put_word(data, MEDAL_CHECKSUM, medal_checksum(data))
    put_word(data, RECORD_CHECKSUM, records_checksum(data))
    return data


def checksums_valid(data: bytes | bytearray) -> dict[str, bool]:
    if len(data) != SRAM_BYTES:
        return {"medal": False, "records": False}
    return {
        "medal": word(data, MEDAL_CHECKSUM) == medal_checksum(data),
        "records": word(data, RECORD_CHECKSUM) == records_checksum(data),
    }


def progressed_base(clean: bytes) -> bytes:
    if len(clean) != SRAM_BYTES:
        raise ValueError(f"clean SRAM must be {SRAM_BYTES} bytes, got {len(clean)}")
    data = bytearray(clean)
    data[MEDAL_MIKE_CRAWLER] = BASE_MEDAL
    put_word(data, RECORDS + 2 * BASE_RECORD_INDEX, BASE_RECORD_VALUE)
    data[RECORD_HOLDERS + BASE_RECORD_INDEX] = BASE_RECORD_HOLDER
    return bytes(fix_checksums(data))


def synthesize(clean: bytes) -> dict[str, bytes]:
    """Return the checksum-valid base plus one image per malformed class."""
    base = progressed_base(clean)
    out: dict[str, bytes] = {"valid_progressed_control": base}

    out["truncated_half"] = base[: SRAM_BYTES // 2]
    out["empty_file"] = b""
    out["oversized"] = base + b"\xA5" * 16

    data = bytearray(base)
    put_word(data, MEDAL_CHECKSUM, word(base, MEDAL_CHECKSUM) ^ 0x0001)
    out["medal_checksum_mismatch"] = bytes(data)

    data = bytearray(base)
    put_word(data, RECORD_CHECKSUM, word(base, RECORD_CHECKSUM) ^ 0x0001)
    out["records_checksum_mismatch"] = bytes(data)

    data = bytearray(base)
    data[MEDAL_MIKE_CRAWLER] = 0x07  # the results writer saturates at 3
    out["medal_value_out_of_range"] = bytes(fix_checksums(data))

    data = bytearray(base)
    put_word(data, RECORDS + 2 * BASE_RECORD_INDEX, 0xFFFF)  # above NO TIME (60000)
    data[RECORD_HOLDERS + BASE_RECORD_INDEX] = 0xFF  # no rider/placeholder 0xFF
    out["record_value_out_of_range"] = bytes(fix_checksums(data))

    data = bytearray(base)
    data[TOUR_FLAGS] = 0xFF  # stock writes only 0/1
    data[TOUR_FLAGS + 1] = 0x01
    out["tour_flag_out_of_range"] = bytes(data)

    data = bytearray(base)
    data[PLAY_MODE] = 0x7F  # stock writes 0 (frontend), 1 (tour), 2 (VS)
    out["play_mode_out_of_range"] = bytes(data)

    data = bytearray(base)
    data[0] ^= 0x01  # 'A' -> '@' in the ASJIver3.30 signature
    out["header_signature_damaged"] = bytes(data)

    assert set(out) == {"valid_progressed_control", *MALFORMED_CLASSES}
    return out


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def changed_regions(a: bytes, b: bytes) -> list[str]:
    names = [name for name, (lo, hi) in REGIONS.items() if a[lo:hi] != b[lo:hi]]
    covered = set()
    for lo, hi in REGIONS.values():
        covered.update(range(lo, hi))
    if any(a[i] != b[i] for i in range(SRAM_BYTES) if i not in covered):
        names.append("other")
    return names


def framework_load(image: bytes) -> bytes:
    """What the framework hands the guest: fread() of up to 8 KiB over zeroed cart RAM."""
    return image[:SRAM_BYTES] + bytes(max(0, SRAM_BYTES - len(image)))


def offsets_differing(a: bytes, b: bytes) -> list[int]:
    return [i for i in range(SRAM_BYTES) if a[i] != b[i]]


def classify(input_image: bytes, after: bytes, fresh: bytes) -> dict:
    """Classify one boot. ``fresh`` is the no-file fresh-format image."""
    if len(after) != SRAM_BYTES or len(fresh) != SRAM_BYTES:
        raise ValueError("live SRAM dumps must be 8 KiB")
    loaded = framework_load(input_image)
    diff = offsets_differing(loaded, after)
    if after == fresh and loaded != fresh:
        outcome = "reformatted_to_fresh_image"
    elif set(diff) <= STOCK_BOOT_WRITES:
        outcome = "accepted_with_stock_boot_writes"
    else:
        outcome = "partial_or_other"
    return {
        "guest_outcome": outcome,
        "after_sha256": sha256(after),
        "after_checksums_valid": checksums_valid(after),
        "offsets_changed_by_boot": [f"0x{i:04X}" for i in diff][:32],
        "offsets_changed_by_boot_count": len(diff),
        "regions_differing_from_fresh": changed_regions(after, fresh),
        # Seeded medal cell and rank-0 record still hold the loaded values.
        "input_progress_kept": (
            after[MEDAL_MIKE_CRAWLER] == loaded[MEDAL_MIKE_CRAWLER]
            and word(after, RECORDS) == word(loaded, RECORDS)
        ),
        "after_values": {
            "medal_mike_crawler": after[MEDAL_MIKE_CRAWLER],
            "record0": word(after, RECORDS),
            "record0_holder": after[RECORD_HOLDERS],
            "tour_flags_0_1": list(after[TOUR_FLAGS:TOUR_FLAGS + 2]),
            "play_mode": after[PLAY_MODE],
        },
    }


SAVE_ROOT_LIMIT = 96  # snesrecomp common_rtl.c: static char s_save_root[96]
BOOT_SCRIPT = "until 009F == D7 3600\nwait 30\ndump boot\nquit\n"
PROFILE_ID = "malformed.probe"


def boot(exe: Path, rom: Path, image: bytes | None, work: Path, mode: str) -> dict:
    """Cold-boot once to MAIN_MENU and return live SRAM plus persisted files.

    Authentic uses the framework's exe-anchored ``saves/`` root (moved aside and
    restored around the run). Modern uses an isolated profile root with no
    host-profile.txt, so the host is read-only and leaves SRAM to the guest.
    """
    work.mkdir(parents=True, exist_ok=True)
    dumps = work / "dumps"
    shutil.rmtree(dumps, ignore_errors=True)
    dumps.mkdir()
    script = work / "boot.script"
    script.write_text(BOOT_SCRIPT)
    user_data = work / "user-data"
    user_data.mkdir(exist_ok=True)
    env = dict(
        os.environ,
        SDL_AUDIODRIVER="dummy",
        SNESRECOMP_DUMP_DIR=str(dumps),
        UR_RECOMP_USER_DATA_ROOT=str(user_data),
        UR_PRODUCT_DIAGNOSTICS="1",
    )
    backup = None
    if mode == "authentic":
        root = exe.parent / "saves"
        if root.exists():
            backup = exe.parent / "saves.malformed-sram-probe-backup"
            if backup.exists():
                raise RuntimeError(f"stale probe backup exists: {backup}")
            root.rename(backup)
        env["UR_EXECUTION_MODE"] = "authentic"
    else:
        # The framework stores its save root in a 96-byte buffer and silently
        # truncates longer paths, so keep the isolated profile root short.
        root = Path(tempfile.mkdtemp(prefix="ur-sram-")) / "profile"
        if len(str(root).encode()) >= SAVE_ROOT_LIMIT:
            raise RuntimeError(f"profile save root too long for the framework: {root}")
        (user_data / "onboarding-v1.seen").write_text("seen-v1\n")
        state = work / "host-state.txt"
        state.write_text(
            f"UR-HOST-STATE/6\nprofile={PROFILE_ID}\npause_on_focus_loss=0\nvibration_enabled=1\n"
        )
        env.update(
            UR_EXECUTION_MODE="modern",
            UR_HOST_STATE_PATH=str(state),
            UR_PROFILE_SAVE_ROOT=str(root),
        )
    try:
        root.mkdir(parents=True, exist_ok=True)
        if image is not None:
            (root / "save.srm").write_bytes(image)
        proc = subprocess.run(
            ["xvfb-run", "-a", str(exe), str(rom), "--script", str(script)],
            env=env, capture_output=True, text=True, timeout=180,
        )
        log = proc.stdout + proc.stderr
        (work / "run.log").write_text(log)
        live = dumps / "boot.sram.bin"
        if proc.returncode != 0 or not live.exists():
            raise RuntimeError(f"native boot failed rc={proc.returncode}\n{log[-4000:]}")
        if mode == "modern" and f"UR_PROFILE_SAVE_ROOT APPLIED profile={PROFILE_ID} root={root}\n" not in log:
            raise RuntimeError(f"Modern run did not apply the isolated save root {root}\n{log[-4000:]}")
        persisted = root / "save.srm"
        bak = root / "save.srm.bak"
        return {
            "live": live.read_bytes(),
            "persisted": persisted.read_bytes() if persisted.exists() else None,
            "bak": bak.read_bytes() if bak.exists() else None,
            "log": log,
            "host_profile_created": (root / "host-profile.txt").exists(),
        }
    finally:
        if mode == "authentic":
            shutil.rmtree(root, ignore_errors=True)
            if backup is not None:
                backup.rename(root)
        else:
            shutil.rmtree(root.parent, ignore_errors=True)


def run_case(exe: Path, rom: Path, image: bytes, work: Path, mode: str,
             fresh: bytes) -> dict:
    run = boot(exe, rom, image, work, mode)
    result = classify(image, run["live"], fresh)
    result["persisted_on_exit_equals_live"] = run["persisted"] == run["live"]
    result["previous_file_kept_as_bak"] = run["bak"] == image
    result["framework_short_read_reported"] = "Error reading" in run["log"]
    if mode == "modern":
        result["host_profile_read_only"] = "UR_PROFILE_STATE MISSING_READ_ONLY" in run["log"]
        result["host_profile_created"] = run["host_profile_created"]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--work", type=Path)
    parser.add_argument("--modes", default="authentic,modern")
    args = parser.parse_args(argv)

    modes = [m for m in args.modes.split(",") if m]
    if not modes or not set(modes) <= {"authentic", "modern"}:
        parser.error("--modes accepts authentic and/or modern")
    clean = CLEAN_SRAM.read_bytes()
    images = synthesize(clean)
    base = images["valid_progressed_control"]
    work = args.work or Path(tempfile.mkdtemp(prefix="malformed-sram-"))

    fresh_runs = {m: boot(args.exe, args.rom, None, work / m / "no-file", m) for m in modes}
    fresh = fresh_runs[modes[0]]["live"]
    cases = {}
    for name, image in images.items():
        entry: dict = {
            "input_bytes": len(image),
            "input_sha256": sha256(image),
            "input_checksums_valid": checksums_valid(image),
        }
        for mode in modes:
            entry[mode] = run_case(args.exe, args.rom, image, work / mode / name, mode, fresh)
            print(f"{mode:9s} {name}: {entry[mode]['guest_outcome']}"
                  f" input_progress_kept={entry[mode]['input_progress_kept']}")
        cases[name] = entry

    report = {
        "schema": "ur-recomp-malformed-sram-containment-v1",
        "question": "WORK-QUEUE expert-edge (f): stock guest boot outcome per malformed SRAM class",
        "method": (
            "native cold boot to MAIN_MENU 7E:009F=D7 and live SRAM dump; Authentic via the "
            "exe-anchored saves/ root, Modern via an isolated profile root with no host-profile.txt; "
            "fixtures synthesized from Clean.srm by synthesize()"
        ),
        "clean_sram_sha256": sha256(clean),
        "fresh_format": {
            mode: {
                "sha256": sha256(run["live"]),
                "equals_clean_stock_sram": run["live"] == clean,
                "persisted_on_exit_equals_live": run["persisted"] == run["live"],
            }
            for mode, run in fresh_runs.items()
        },
        "stock_boot_writes": [f"0x{i:04X}" for i in sorted(STOCK_BOOT_WRITES)],
        "base": {
            "description": (
                "Clean.srm + MIKE Crawler silver (0x069C=2) + Crawler/Dragster rank-0 record "
                "30.00 s held by MIKE, both checksums valid"
            ),
            "sha256": sha256(base),
        },
        "cases": cases,
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
