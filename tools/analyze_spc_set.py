#!/usr/bin/env python3
"""Analyze SNES SPC snapshots as reverse-engineering evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

MAGIC = b"SNES-SPC700 Sound File Data"
HEADER = 0x100
RAM_SIZE = 0x10000
DSP_SIZE = 0x80


@dataclass(frozen=True)
class Snapshot:
    name: str
    data_sha256: str
    size: int
    ram: bytes
    dsp: bytes
    pc: int
    title: str
    game: str
    dumper: str


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _text(data: bytes, offset: int, length: int) -> str:
    return data[offset : offset + length].split(b"\x00", 1)[0].decode(
        "latin-1", "replace"
    ).rstrip()


def parse_spc(name: str, data: bytes) -> Snapshot:
    if not data.startswith(MAGIC):
        raise ValueError(f"not an SPC file: {name}")
    if len(data) < HEADER + RAM_SIZE + DSP_SIZE:
        raise ValueError(f"truncated SPC file: {name} ({len(data)} bytes)")
    ram = data[HEADER : HEADER + RAM_SIZE]
    dsp = data[HEADER + RAM_SIZE : HEADER + RAM_SIZE + DSP_SIZE]
    return Snapshot(
        name=name,
        data_sha256=sha256(data),
        size=len(data),
        ram=ram,
        dsp=dsp,
        pc=int.from_bytes(data[0x25:0x27], "little"),
        title=_text(data, 0x2E, 32),
        game=_text(data, 0x4E, 32),
        dumper=_text(data, 0x6E, 16),
    )


def load_snapshots(source: Path) -> tuple[list[Snapshot], dict]:
    rows: list[tuple[str, bytes]] = []
    meta: dict = {"source": str(source)}
    if source.is_dir():
        meta["kind"] = "directory"
        for path in sorted(source.rglob("*.spc")):
            rows.append((str(path.relative_to(source)), path.read_bytes()))
    elif zipfile.is_zipfile(source):
        raw = source.read_bytes()
        meta.update(
            {"kind": "zip", "archive_size": len(raw), "archive_sha256": sha256(raw)}
        )
        with zipfile.ZipFile(source) as archive:
            for info in sorted(archive.infolist(), key=lambda item: item.filename):
                if not info.is_dir() and info.filename.lower().endswith(".spc"):
                    rows.append((info.filename, archive.read(info)))
    else:
        raise ValueError(f"source must be a directory or ZIP archive: {source}")
    snapshots = [parse_spc(name, data) for name, data in rows]
    if not snapshots:
        raise ValueError(f"no SPC files found in {source}")
    return snapshots, meta


def common_ranges(snapshots: list[Snapshot], min_length: int = 16) -> list[dict]:
    if not snapshots:
        return []
    out: list[dict] = []
    start: int | None = None
    for index in range(RAM_SIZE):
        same = all(
            snapshot.ram[index] == snapshots[0].ram[index]
            for snapshot in snapshots[1:]
        )
        if same and start is None:
            start = index
        if (not same or index == RAM_SIZE - 1) and start is not None:
            end = index if not same else index + 1
            if end - start >= min_length:
                blob = snapshots[0].ram[start:end]
                out.append(
                    {
                        "start": start,
                        "start_hex": f"0x{start:04X}",
                        "end_exclusive": end,
                        "end_exclusive_hex": f"0x{end:04X}",
                        "length": end - start,
                        "sha256": sha256(blob),
                        "unique_byte_count": len(set(blob)),
                    }
                )
            start = None
    return sorted(out, key=lambda row: (-row["length"], row["start"]))


def brr_samples(snapshot: Snapshot, max_entries: int = 64) -> dict[int, dict]:
    directory = snapshot.dsp[0x5D] * 0x100
    out: dict[int, dict] = {}
    for sample_index in range(max_entries):
        entry = directory + sample_index * 4
        if entry + 4 > RAM_SIZE:
            break
        start = int.from_bytes(snapshot.ram[entry : entry + 2], "little")
        loop = int.from_bytes(snapshot.ram[entry + 2 : entry + 4], "little")
        if start in (0, 0xFFFF) or start >= RAM_SIZE:
            continue
        cursor = start
        blocks: list[bytes] = []
        complete = False
        while cursor + 9 <= RAM_SIZE and len(blocks) < 4096:
            block = snapshot.ram[cursor : cursor + 9]
            blocks.append(block)
            cursor += 9
            if block[0] & 1:
                complete = True
                break
        if not complete:
            continue
        payload = b"".join(blocks)
        out[sample_index] = {
            "start": start,
            "start_hex": f"0x{start:04X}",
            "loop": loop,
            "loop_hex": f"0x{loop:04X}",
            "size": len(payload),
            "sha256": sha256(payload),
        }
    return out


def pairwise_similarity(snapshots: list[Snapshot]) -> list[dict]:
    out = []
    for index, left in enumerate(snapshots):
        for right in snapshots[index + 1 :]:
            equal = sum(a == b for a, b in zip(left.ram, right.ram))
            out.append(
                {
                    "left": left.name,
                    "right": right.name,
                    "equal_bytes": equal,
                    "equal_fraction": round(equal / RAM_SIZE, 6),
                }
            )
    return sorted(
        out, key=lambda row: (-row["equal_fraction"], row["left"], row["right"])
    )


def analyze(source: Path, rom: bytes | None = None) -> dict:
    snapshots, meta = load_snapshots(source)
    samples = {snapshot.name: brr_samples(snapshot) for snapshot in snapshots}
    ranges = common_ranges(snapshots)

    if rom is not None:
        for row in ranges:
            row["canonical_rom_offsets"] = []
            if row["length"] < 64 or row["unique_byte_count"] <= 2:
                continue
            blob = snapshots[0].ram[row["start"] : row["end_exclusive"]]
            cursor = 0
            while True:
                found = rom.find(blob, cursor)
                if found < 0:
                    break
                row["canonical_rom_offsets"].append(found)
                cursor = found + 1

    same_index_all = []
    for sample_index in range(64):
        values = [samples[snapshot.name].get(sample_index) for snapshot in snapshots]
        if values[0] is None:
            continue
        fingerprint = (
            values[0]["start"],
            values[0]["loop"],
            values[0]["sha256"],
        )
        if all(
            value is not None
            and (value["start"], value["loop"], value["sha256"]) == fingerprint
            for value in values[1:]
        ):
            same_index_all.append(
                {
                    "sample_index": sample_index,
                    "start": values[0]["start"],
                    "start_hex": values[0]["start_hex"],
                    "loop": values[0]["loop"],
                    "loop_hex": values[0]["loop_hex"],
                    "size": values[0]["size"],
                    "sha256": values[0]["sha256"],
                }
            )

    sample_overlap = []
    for index, left in enumerate(snapshots):
        left_hashes = {row["sha256"] for row in samples[left.name].values()}
        for right in snapshots[index + 1 :]:
            right_hashes = {row["sha256"] for row in samples[right.name].values()}
            shared = len(left_hashes & right_hashes)
            union = len(left_hashes | right_hashes)
            sample_overlap.append(
                {
                    "left": left.name,
                    "right": right.name,
                    "left_samples": len(left_hashes),
                    "right_samples": len(right_hashes),
                    "shared_samples": shared,
                    "jaccard": round(shared / union, 6) if union else 1.0,
                }
            )

    stable = sum(
        all(
            snapshot.ram[index] == snapshots[0].ram[index]
            for snapshot in snapshots[1:]
        )
        for index in range(RAM_SIZE)
    )

    report = {
        "schema_version": 1,
        **meta,
        "spc_count": len(snapshots),
        "stable_apu_ram_bytes_all_tracks": stable,
        "stable_apu_ram_fraction_all_tracks": round(stable / RAM_SIZE, 6),
        "tracks": [
            {
                "path": snapshot.name,
                "title": snapshot.title,
                "game": snapshot.game,
                "dumper": snapshot.dumper,
                "size": snapshot.size,
                "sha256": snapshot.data_sha256,
                "apu_ram_sha256": sha256(snapshot.ram),
                "dsp_sha256": sha256(snapshot.dsp),
                "pc": snapshot.pc,
                "pc_hex": f"0x{snapshot.pc:04X}",
                "sample_directory": snapshot.dsp[0x5D] * 0x100,
                "sample_directory_hex": f"0x{snapshot.dsp[0x5D] * 0x100:04X}",
                "valid_brr_sample_count": len(samples[snapshot.name]),
                "brr_samples": samples[snapshot.name],
            }
            for snapshot in snapshots
        ],
        "common_apu_ranges_min_16": ranges,
        "same_index_brr_samples_all_tracks": same_index_all,
        "pairwise_apu_ram_similarity": pairwise_similarity(snapshots),
        "pairwise_brr_sample_overlap": sorted(
            sample_overlap,
            key=lambda row: (
                -row["jaccard"],
                -row["shared_samples"],
                row["left"],
                row["right"],
            ),
        ),
    }
    if rom is not None:
        report["canonical_rom_sha256"] = sha256(rom)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path, help="SPC directory or ZIP archive")
    ap.add_argument(
        "--rom", type=Path, help="optional ROM for exact common-range matching"
    )
    ap.add_argument("--output", type=Path, help="optional JSON report path")
    args = ap.parse_args()

    report = analyze(
        args.source, rom=args.rom.read_bytes() if args.rom is not None else None
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
