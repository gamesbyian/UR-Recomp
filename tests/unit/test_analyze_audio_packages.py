from tools.analyze_audio_packages import (
    scan_direct_callers,
    scan_raw_seed_references,
    table_relationships,
)


def test_scan_direct_callers_requires_exact_ldx_jsl_pattern():
    rom = bytearray(b"\x00" * 0x200)
    # Known table seed FAD5.
    rom[0x20:0x27] = bytes.fromhex("A2 D5 FA 22 A5 82 82")
    # Same immediate but wrong call target.
    rom[0x40:0x47] = bytes.fromhex("A2 D5 FA 22 A9 82 82")
    # Known other table seed FB55.
    rom[0x60:0x67] = bytes.fromhex("A2 55 FB 22 A5 82 82")

    rows = scan_direct_callers(bytes(rom), table_cpus=(0x03FAD5, 0x03FB55))
    assert [r["table_seed"] for r in rows] == ["0xFAD5", "0xFB55"]
    assert all(r["pattern"] == "LDX #imm16 ; JSL $82:82A5" for r in rows)


def test_raw_seed_references_are_broader_than_direct_callers():
    rom = bytearray(b"\x00" * 0x80)
    rom[0x10:0x12] = bytes.fromhex("95 FB")
    rom[0x30:0x37] = bytes.fromhex("A2 95 FB 22 A5 82 82")
    rows = scan_raw_seed_references(bytes(rom), table_cpus=(0x03FB95,))
    assert [r["rom_offset"] for r in rows] == [0x10, 0x31]


def test_table_relationships_preserve_slots_and_subset_structure():
    a = bytes([0x01, 0xFF, 0x07, 0x15, 0x29] + [0xFF] * 59)
    b = bytes([0x01, 0xFF, 0xFF, 0xFF, 0xFF] + [0xFF] * 59)
    rows = [
        {"cpu_address": "0x03FAD5", "bytes_hex": a.hex(" ")},
        {"cpu_address": "0x03FB95", "bytes_hex": b.hex(" ")},
    ]
    rel = table_relationships(rows)[0]
    assert rel["different_slots"] == 3
    assert rel["a_only_ids"] == ["0x07", "0x15", "0x29"]
    assert rel["b_only_ids"] == []
    assert rel["b_is_subset_of_a"] is True
    assert rel["same_relative_slots_for_shared_ids"] is True
