from tools.scan_audio_setup_selectors import (
    scan_setup_calls,
    scan_setup_package_pairs,
)


def test_setup_call_scanner_finds_exact_807e_pattern():
    rom = bytearray(bytes([0]) * 0x100)
    rom[0x20:0x27] = bytes.fromhex("A2 3B 00 22 7E 80 82")
    rom[0x40:0x47] = bytes.fromhex("A2 3D 00 22 A5 82 82")
    rows = scan_setup_calls(bytes(rom))
    assert [(r["caller_cpu"], r["selector_hex"]) for r in rows] == [
        ("00:8020", "0x003B")
    ]


def test_setup_package_pair_binds_selector_to_known_table():
    rom = bytearray(bytes([0]) * 0x100)
    rom[0x20:0x2E] = bytes.fromhex(
        "A2 3B 00 22 7E 80 82 A2 95 FB 22 A5 82 82"
    )
    rows = scan_setup_package_pairs(bytes(rom), table_cpus=(0x03FB95,))
    assert len(rows) == 1
    assert rows[0]["selector_hex"] == "0x003B"
    assert rows[0]["table_cpu"] == "0x03FB95"
