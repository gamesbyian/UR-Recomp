#!/usr/bin/env python3
"""Inventory and mechanically classify the recovered Canoe Uniracers IPS patch.

IPS parsing remains generic, while the semantic layer recognizes the concrete
65816/LoROM structures used by the recovered compatibility patch.  The goal is
to turn one-shot disassembly evidence into stable machine-readable assertions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


CANOE_PATCH_SHA256 = "35b695d9cc0667d09f950a05cb3066ada5f0078a50818bc04d348f5ef4f852cf"
CANOE_HANDLER_OFFSET = 0x1FFF00
CANOE_HANDLER_HDMA_ENTRY = 0x36


def parse_ips(data: bytes) -> list[dict]:
    if not data.startswith(b"PATCH"):
        raise ValueError("missing IPS PATCH header")
    pos = 5
    rows = []
    while True:
        if data[pos:pos + 3] == b"EOF":
            pos += 3
            break
        if pos + 5 > len(data):
            raise ValueError("truncated IPS record header")
        offset = int.from_bytes(data[pos:pos + 3], "big")
        size = int.from_bytes(data[pos + 3:pos + 5], "big")
        pos += 5
        if size == 0:
            if pos + 3 > len(data):
                raise ValueError("truncated IPS RLE record")
            run = int.from_bytes(data[pos:pos + 2], "big")
            value = data[pos + 2]
            pos += 3
            payload = bytes([value]) * run
            kind = "rle"
        else:
            if pos + size > len(data):
                raise ValueError("truncated IPS literal record")
            payload = data[pos:pos + size]
            pos += size
            kind = "literal"
        rows.append({
            "offset": offset,
            "offset_hex": f"0x{offset:06X}",
            "length": len(payload),
            "kind": kind,
            "data_hex": payload.hex(" "),
        })
    if pos != len(data):
        raise ValueError(f"unexpected {len(data)-pos} byte(s) after EOF")
    return rows


def lorom_cpu(offset: int) -> str:
    bank = (offset // 0x8000) & 0x7F
    addr = 0x8000 + (offset % 0x8000)
    return f"{bank:02X}:{addr:04X}"


def _cpu24(value: int) -> str:
    return f"{(value >> 16) & 0xFF:02X}:{value & 0xFFFF:04X}"


def _decode_jsl(payload: bytes) -> str | None:
    if len(payload) < 4 or payload[0] != 0x22:
        return None
    return _cpu24(int.from_bytes(payload[1:4], "little"))


def _decode_hdma_table(memory: dict[int, int], start: int, data_width: int) -> list[dict]:
    entries = []
    cursor = start
    while True:
        if cursor not in memory:
            raise ValueError(f"missing HDMA table byte at 0x{cursor:06X}")
        control = memory[cursor]
        cursor += 1
        if control == 0:
            entries.append({"control": 0, "terminator": True})
            break
        data = []
        for _ in range(data_width):
            if cursor not in memory:
                raise ValueError(f"missing HDMA payload byte at 0x{cursor:06X}")
            data.append(memory[cursor])
            cursor += 1
        entries.append({
            "control": control,
            "line_count": control & 0x7F,
            "repeat": bool(control & 0x80),
            "data_hex": bytes(data).hex(" "),
        })
    return entries


def _decode_hdma_setup(payload: bytes) -> dict:
    """Decode the immediate-load/store-only routine at injected +0x36."""
    pc = CANOE_HANDLER_HDMA_ENTRY
    acc: int | None = None
    x: int | None = None
    writes: list[dict] = []
    memory: dict[int, int] = {}

    while pc < len(payload):
        op = payload[pc]
        if op == 0xA9:  # LDA #imm8
            if pc + 1 >= len(payload):
                raise ValueError("truncated LDA immediate in Canoe HDMA setup")
            acc = payload[pc + 1]
            pc += 2
        elif op == 0xA2:  # LDX #imm16
            if pc + 2 >= len(payload):
                raise ValueError("truncated LDX immediate in Canoe HDMA setup")
            x = int.from_bytes(payload[pc + 1:pc + 3], "little")
            pc += 3
        elif op == 0x8D:  # STA abs
            if acc is None or pc + 2 >= len(payload):
                raise ValueError("STA abs without decoded A value")
            addr = int.from_bytes(payload[pc + 1:pc + 3], "little")
            writes.append({"kind": "STA", "address": f"{addr:04X}", "value": acc})
            pc += 3
        elif op == 0x8E:  # STX abs
            if x is None or pc + 2 >= len(payload):
                raise ValueError("STX abs without decoded X value")
            addr = int.from_bytes(payload[pc + 1:pc + 3], "little")
            writes.append({"kind": "STX", "address": f"{addr:04X}", "value": x})
            pc += 3
        elif op == 0x8F:  # STA long
            if acc is None or pc + 3 >= len(payload):
                raise ValueError("STA long without decoded A value")
            addr = int.from_bytes(payload[pc + 1:pc + 4], "little")
            writes.append({"kind": "STA-long", "address": _cpu24(addr), "value": acc})
            memory[addr] = acc
            pc += 4
        elif op == 0x6B:  # RTL
            pc += 1
            break
        else:
            raise ValueError(
                f"unexpected opcode 0x{op:02X} in Canoe HDMA setup at injected +0x{pc:02X}"
            )

    if pc != len(payload):
        raise ValueError(f"unexpected trailing bytes after Canoe HDMA setup: {len(payload)-pc}")

    def abs_write(address: str, kind: str = "STA") -> int:
        matches = [w["value"] for w in writes if w["kind"] == kind and w["address"] == address]
        if len(matches) != 1:
            raise ValueError(f"expected one {kind} write to {address}, got {len(matches)}")
        return matches[0]

    ch7_ptr = abs_write("4372", "STX")
    ch7_bank = abs_write("4374")
    ch1_ptr = abs_write("4312", "STX")
    ch1_bank = abs_write("4314")
    ch7_addr = (ch7_bank << 16) | ch7_ptr
    ch1_addr = (ch1_bank << 16) | ch1_ptr

    return {
        "entry": "BF:FF36",
        "mirror_entry": "3F:FF36",
        "writes": writes,
        "channel7": {
            "dmap": abs_write("4370"),
            "bbad": abs_write("4371"),
            "table_address": _cpu24(ch7_addr),
            "table": _decode_hdma_table(memory, ch7_addr, 4),
        },
        "channel1": {
            "dmap": abs_write("4310"),
            "bbad": "inherited",
            "table_address": _cpu24(ch1_addr),
            "table": _decode_hdma_table(memory, ch1_addr, 2),
        },
    }


def _decode_oam_handler(payload: bytes) -> dict:
    head = payload[:CANOE_HANDLER_HDMA_ENTRY]
    expected_prefix = bytes.fromhex(
        "AD DB 0D D0 08 AD 99 15 8D 04 21 80 23 "
        "AF A2 20 7E 29 F0 09 05 8F A2 20 7E 8F F1 FF 7F 8D 04 21 "
        "AF A3 20 7E 29 0F 09 50 8F A3 20 7E 8F F4 FF 7F "
        "A9 55 8D 04 21 6B"
    )
    if head != expected_prefix:
        raise ValueError("recovered Canoe OAM handler bytes no longer match decoded contract")
    return {
        "entry": "BF:FF00",
        "mirror_entry": "3F:FF00",
        "mode_selector": "7E:0DDB",
        "stock_oam_source": "7E:1599",
        "oamdata_register": "00:2104",
        "dynamic_sources": ["7E:20A2", "7E:20A3"],
        "dynamic_table_targets": ["7F:FFF1", "7F:FFF4"],
        "forced_nibbles": [
            "7E:20A2 = (7E:20A2 & F0) | 05",
            "7E:20A3 = (7E:20A3 & 0F) | 50",
        ],
        "common_final_oamdata": "55",
    }


def _semantic_summary(patch: bytes, rows: list[dict], rom: bytes | None) -> dict | None:
    sha = hashlib.sha256(patch).hexdigest()
    if sha != CANOE_PATCH_SHA256:
        return None
    if rom is None:
        return {
            "identified_patch": "recovered-uniracers-canoe",
            "requires_rom_for_full_decode": True,
        }

    by_offset = {row["offset"]: row for row in rows}
    expected_offsets = {
        0x007FDC, 0x01534C, 0x015714, 0x018B16,
        0x01E8D1, 0x01EA50, CANOE_HANDLER_OFFSET,
    }
    if set(by_offset) != expected_offsets:
        raise ValueError("known Canoe patch record layout changed")

    checksum = bytes.fromhex(by_offset[0x007FDC]["data_hex"])
    complement = int.from_bytes(checksum[:2], "little")
    value = int.from_bytes(checksum[2:], "little")
    if (complement + value) & 0xFFFF != 0xFFFF:
        raise ValueError("patched LoROM checksum/complement pair is invalid")

    hook_oam = bytes.fromhex(by_offset[0x01534C]["data_hex"])
    hook_hdma = bytes.fromhex(by_offset[0x015714]["data_hex"])
    if hook_oam[4:] != b"\x60":
        raise ValueError("expected OAM hook to end in RTS")
    if hook_hdma[4:] != b"\x80\x00":
        raise ValueError("expected HDMA hook to end in BRA +0")

    forced = by_offset[0x018B16]
    if rom[0x018B16] != 0xF0 or bytes.fromhex(forced["data_hex"]) != b"\x80":
        raise ValueError("expected Canoe branch patch BEQ -> BRA at 03:8B16")
    branch_disp = rom[0x018B17]

    redirects = []
    for off in (0x01E8D1, 0x01EA50):
        if rom[off - 1] != 0x8F:
            raise ValueError(f"expected STA-long opcode immediately before 0x{off:06X}")
        original = int.from_bytes(rom[off:off + 3], "little")
        patched = int.from_bytes(bytes.fromhex(by_offset[off]["data_hex"]), "little")
        redirects.append({
            "operand_offset": f"0x{off:06X}",
            "instruction": "STA-long",
            "original_target": _cpu24(original),
            "patched_target": _cpu24(patched),
        })

    handler = bytes.fromhex(by_offset[CANOE_HANDLER_OFFSET]["data_hex"])
    if len(handler) != 230:
        raise ValueError(f"expected 230-byte Canoe handler, got {len(handler)}")
    oam = _decode_oam_handler(handler)
    hdma = _decode_hdma_setup(handler)

    return {
        "identified_patch": "recovered-uniracers-canoe",
        "requires_rom_for_full_decode": False,
        "checksum": {
            "offset": "0x007FDC",
            "complement": f"{complement:04X}",
            "checksum": f"{value:04X}",
            "sum": "FFFF",
        },
        "hooks": [
            {
                "site": "02:D34C",
                "role": "replace stock OAMDATA write routine",
                "target": _decode_jsl(hook_oam),
                "post_call": "RTS",
            },
            {
                "site": "02:D714",
                "role": "replace stock HDMA source setup",
                "target": _decode_jsl(hook_hdma),
                "post_call": "BRA +0",
            },
        ],
        "forced_branch": {
            "site": "03:8B16",
            "original": f"BEQ +0x{branch_disp:02X}",
            "patched": f"BRA +0x{branch_disp:02X}",
        },
        "long_store_redirects": redirects,
        "injected_handler": {
            "rom_offset": "0x1FFF00",
            "size": len(handler),
            "oam_wrapper": oam,
            "hdma_setup": hdma,
            "cross_links": {
                "redirected_channel7_payload_bytes": [
                    r["patched_target"] for r in redirects
                ],
                "oam_wrapper_channel1_payload_bytes": oam["dynamic_table_targets"],
            },
        },
    }


def analyze(patch: bytes, rom: bytes | None = None, context: int = 8) -> dict:
    rows = parse_ips(patch)
    for row in rows:
        row["lorom_cpu"] = lorom_cpu(row["offset"])
        if rom is not None:
            start = row["offset"]
            end = start + row["length"]
            if end > len(rom):
                raise ValueError(f"record {row['offset_hex']} extends past ROM")
            row["original_hex"] = rom[start:end].hex(" ")
            a = max(0, start - context)
            b = min(len(rom), end + context)
            row["context_start_hex"] = f"0x{a:06X}"
            row["original_context_hex"] = rom[a:b].hex(" ")

    report = {
        "schema_version": 2,
        "patch_size": len(patch),
        "patch_sha256": hashlib.sha256(patch).hexdigest(),
        "record_count": len(rows),
        "records": rows,
    }
    semantic = _semantic_summary(patch, rows, rom)
    if semantic is not None:
        report["semantic_summary"] = semantic
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("patch", type=Path)
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--context", type=int, default=8)
    args = ap.parse_args()
    report = analyze(
        args.patch.read_bytes(),
        args.rom.read_bytes() if args.rom else None,
        context=args.context,
    )
    print(f"records={report['record_count']} patch_sha256={report['patch_sha256']}")
    for row in report["records"]:
        before = f" original={row['original_hex']}" if "original_hex" in row else ""
        context = (
            f" context@{row['context_start_hex']}={row['original_context_hex']}"
            if "original_context_hex" in row else ""
        )
        print(
            f"{row['offset_hex']} {row['lorom_cpu']} len={row['length']} "
            f"patched={row['data_hex']}{before}{context}"
        )
    if "semantic_summary" in report:
        print("semantic_summary=" + json.dumps(report["semantic_summary"], sort_keys=True))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
