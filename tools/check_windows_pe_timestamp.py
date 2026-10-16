#!/usr/bin/env python3
"""Read-only admission of deterministic PE/COFF linker timestamps on Windows.

Only the exact original linked executable is inspected. No post-link bytes are
patched: the SOURCE_DATE_EPOCH-based linker build must itself be reproducible.
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

DEBUG_DIRECTORY_ENTRY_SIZE = 28
PE32PLUS_MAGIC = 0x20B
AMD64 = 0x8664
DEBUG_DIRECTORY_INDEX = 6
DATA_DIRECTORY64_OFFSET = 112


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError("WIN32_PE_TIMESTAMP_INVALID: " + reason)


def inspect(image: bytes, expected_epoch: int) -> dict:
    require(isinstance(expected_epoch, int) and
            not isinstance(expected_epoch, bool) and
            1 <= expected_epoch < (1 << 32), "invalid source epoch")
    require(len(image) >= 512 and image[:2] == b"MZ",
            "missing or truncated DOS header")
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    require(pe >= 64 and pe + 24 <= len(image) and
            image[pe:pe + 4] == b"PE\x00\x00", "missing valid PE signature")
    machine, sections = struct.unpack_from("<HH", image, pe + 4)
    require(machine == AMD64 and 1 <= sections <= 96, "not real AMD64 PE")
    linked_epoch = struct.unpack_from("<I", image, pe + 8)[0]
    require(linked_epoch == expected_epoch,
            "COFF TimeDateStamp does not equal immutable source epoch")

    opt_size = struct.unpack_from("<H", image, pe + 20)[0]
    opt = pe + 24
    directory_at = opt + DATA_DIRECTORY64_OFFSET + 8 * DEBUG_DIRECTORY_INDEX
    require(opt_size >= DATA_DIRECTORY64_OFFSET + 8 * (DEBUG_DIRECTORY_INDEX + 1)
            and opt + opt_size + sections * 40 <= len(image),
            "truncated optional header or section table")
    require(struct.unpack_from("<H", image, opt)[0] == PE32PLUS_MAGIC,
            "not PE32+")
    debug_rva, debug_size = struct.unpack_from("<II", image, directory_at)
    require(debug_rva != 0 and
            DEBUG_DIRECTORY_ENTRY_SIZE <= debug_size <= DEBUG_DIRECTORY_ENTRY_SIZE * 16
            and debug_size % DEBUG_DIRECTORY_ENTRY_SIZE == 0,
            "missing or noncanonical debug directory")

    file_offset = None
    for i in range(sections):
        start = opt + opt_size + i * 40
        virtual_size, virtual_addr, raw_size, raw_ptr = struct.unpack_from(
            "<IIII", image, start + 8)
        if virtual_addr <= debug_rva < virtual_addr + max(virtual_size, raw_size):
            delta = debug_rva - virtual_addr
            require(delta + debug_size <= raw_size and
                    raw_ptr + delta + debug_size <= len(image),
                    "debug directory extends beyond mapped section")
            file_offset = raw_ptr + delta
            break
    require(file_offset is not None,
            "debug directory RVA not mapped to a real section")

    timestamps = []
    for i in range(debug_size // DEBUG_DIRECTORY_ENTRY_SIZE):
        entry = file_offset + i * DEBUG_DIRECTORY_ENTRY_SIZE
        timestamp = struct.unpack_from("<I", image, entry + 4)[0]
        require(timestamp == expected_epoch,
                "debug-directory TimeDateStamp does not equal source epoch")
        timestamps.append({"file_offset": entry + 4, "value": timestamp})
    return {
        "schema": "ur-windows-source-epoch-coff-link/1",
        "exe_bytes": len(image),
        "source_date_epoch": expected_epoch,
        "coff_timestamp_file_offset": pe + 8,
        "coff_timestamp": linked_epoch,
        "debug_timestamps": timestamps,
        "real_pe32plus_amd64": True,
        "post_link_bytes_modified": False,
        "release_gate_credit": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--source-epoch", type=int, required=True)
    args = parser.parse_args()
    require(args.exe.is_file() and not args.exe.is_symlink(),
            "missing or redirected Windows executable")
    require(65536 < args.exe.stat().st_size < (256 << 20),
            "out-of-bounds executable size")
    print(json.dumps(inspect(args.exe.read_bytes(), args.source_epoch),
                     sort_keys=True))


if __name__ == "__main__":
    main()
