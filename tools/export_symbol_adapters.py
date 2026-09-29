#!/usr/bin/env python3
"""Project canonical symbols into external-tool seed formats."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "analysis" / "generated" / "symbols.json"
SNES2ASM_OUT = ROOT / "analysis" / "generated" / "snes2asm-symbols.yml"
MESEN_OUT = ROOT / "analysis" / "generated" / "mesen-symbols.mlb"
GHIDRA_OUT = ROOT / "analysis" / "generated" / "ghidra-symbols.json"
DA65_DIR = ROOT / "analysis" / "generated"
CPU_RE = re.compile(r"([0-9A-Fa-f]{2}):([0-9A-Fa-f]{4})")
SAFE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_symbols() -> list[dict]:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported symbols.json schema")
    return data.get("entries", [])


def cpu_address(raw: str) -> tuple[int, int] | None:
    match = CPU_RE.search((raw or "").replace(chr(96), ""))
    if not match:
        return None
    return int(match.group(1), 16), int(match.group(2), 16)


def lorom_offset(bank: int, addr: int) -> int | None:
    bank &= 0x7F
    if addr < 0x8000:
        return None
    return bank * 0x8000 + (addr - 0x8000)


def name_of(entry: dict) -> str | None:
    name = str(entry.get("name", "")).strip().strip(chr(96))
    return name if SAFE_NAME_RE.fullmatch(name) else None


def render_snes2asm(entries: list[dict]) -> str:
    labels: list[tuple[str, int]] = []
    memory: list[tuple[str, int]] = []
    for entry in entries:
        name = name_of(entry)
        parsed = cpu_address(str(entry.get("address", "")))
        if not name or parsed is None:
            continue
        bank, addr = parsed
        if entry.get("kind") == "function":
            off = lorom_offset(bank, addr)
            if off is not None:
                labels.append((name, off))
        elif entry.get("kind") == "ram":
            memory.append((name, (bank << 16) | addr))

    lines = [
        "# Generated from analysis/generated/symbols.json.",
        "# Add structural decoders separately; this file only seeds known labels/memory.",
        "labels:",
    ]
    for name, off in sorted(labels, key=lambda x: (x[1], x[0])):
        lines.append(f"  {name}: 0x{off:X}")
    lines.append("memory:")
    for name, addr in sorted(memory, key=lambda x: (x[1], x[0])):
        lines.append(f"  {name}: 0x{addr:X}")
    return "\n".join(lines) + "\n"


def comment_of(entry: dict) -> str:
    raw = entry.get("notes")
    if raw is None:
        raw = entry.get("evidence_/_notes")
    if raw is None:
        return ""
    return str(raw).replace("\\r\\n", "\\n").replace("\\r", "\\n").replace("\\n", "\\\\n").strip()


def render_mesen(entries: list[dict]) -> str:
    labels: list[tuple[str, int, str, str]] = []
    for entry in entries:
        name = name_of(entry)
        parsed = cpu_address(str(entry.get("address", "")))
        if not name or parsed is None:
            continue
        bank, addr = parsed
        comment = comment_of(entry)
        if entry.get("kind") == "function":
            off = lorom_offset(bank, addr)
            if off is not None:
                labels.append(("SnesPrgRom", off, name, comment))
        elif entry.get("kind") == "ram" and bank in {0x7E, 0x7F}:
            wram = (bank - 0x7E) * 0x10000 + addr
            labels.append(("SnesWorkRam", wram, name, comment))

    lines = [
        "# Generated from analysis/generated/symbols.json for pinned MesenCE.",
        "# Native syntax: MemoryType:HEX_ADDRESS:Label[:Comment].",
    ]
    for memory_type, address, name, comment in sorted(
        labels, key=lambda x: (x[0], x[1], x[2])
    ):
        line = f"{memory_type}:{address:04X}:{name}"
        if comment:
            line += ":" + comment
        lines.append(line)
    return "\n".join(lines) + "\n"


def ghidra_lorom_address(bank: int, addr: int) -> int | None:
    if addr < 0x8000:
        return None
    if bank <= 0x7D:
        bank |= 0x80
    return (bank << 16) | addr


def render_ghidra(entries: list[dict]) -> str:
    labels: list[dict] = []
    for entry in entries:
        name = name_of(entry)
        parsed = cpu_address(str(entry.get("address", "")))
        if not name or parsed is None:
            continue
        bank, addr = parsed
        if entry.get("kind") == "function":
            target = ghidra_lorom_address(bank, addr)
            if target is None:
                continue
        elif entry.get("kind") == "ram" and bank in {0x7E, 0x7F}:
            target = (bank << 16) | addr
        else:
            continue
        labels.append({
            "address": f"{target:06X}",
            "name": name,
            "kind": entry.get("kind"),
            "comment": comment_of(entry),
        })
    labels.sort(key=lambda row: (row["address"], row["name"]))
    return json.dumps({
        "schema_version": 1,
        "target": "ghidra-snes",
        "target_revision": "d33ce5dbfbc3645f00449be1c7ca1c1c65e81756",
        "address_model": "ghidra-snes canonical 24-bit SNES CPU space; LoROM ROM banks canonicalized to 80-FF; WRAM remains 7E-7F",
        "entries": labels,
    }, indent=2, ensure_ascii=False) + "\n"


def render_da65(entries: list[dict]) -> dict[int, str]:
    by_bank: dict[int, list[tuple[int, str]]] = {}
    for entry in entries:
        if entry.get("kind") != "function":
            continue
        name = name_of(entry)
        parsed = cpu_address(str(entry.get("address", "")))
        if not name or parsed is None:
            continue
        bank, addr = parsed
        if addr < 0x8000:
            continue
        by_bank.setdefault(bank & 0x7F, []).append((addr, name))

    rendered: dict[int, str] = {}
    for bank, labels in by_bank.items():
        lines = [
            "# Generated labels only. Add RANGE/ADDRMODE from dynamic trace/CDL evidence.",
            "GLOBAL {",
            '    CPU "65816";',
            "    STARTADDR $8000;",
            "};",
            f'SEGMENT {{ START $8000; END $FFFF; NAME "bank_{bank:02X}"; }};',
            "",
        ]
        for addr, name in sorted(labels):
            lines.append(f'LABEL {{ NAME "{name}"; ADDR ${addr:04X}; }};')
        rendered[bank] = "\n".join(lines) + "\n"
    return rendered


def expected_outputs() -> dict[Path, str]:
    entries = load_symbols()
    outputs = {
        SNES2ASM_OUT: render_snes2asm(entries),
        MESEN_OUT: render_mesen(entries),
        GHIDRA_OUT: render_ghidra(entries),
    }
    for bank, content in render_da65(entries).items():
        outputs[DA65_DIR / f"da65-symbols-bank-{bank:02X}.info"] = content
    return outputs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    outputs = expected_outputs()
    existing_da65 = set(DA65_DIR.glob("da65-symbols-bank-*.info"))
    expected_da65 = {p for p in outputs if p.name.startswith("da65-symbols-bank-")}

    if args.check:
        stale = []
        for path, content in outputs.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                stale.append(path.relative_to(ROOT).as_posix())
        for path in sorted(existing_da65 - expected_da65):
            stale.append(path.relative_to(ROOT).as_posix())
        if stale:
            print("stale symbol adapter output(s): " + ", ".join(stale), file=sys.stderr)
            return 1
        print(f"symbol adapter outputs current ({len(outputs)} files)")
        return 0

    for path in existing_da65 - expected_da65:
        path.unlink()
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
