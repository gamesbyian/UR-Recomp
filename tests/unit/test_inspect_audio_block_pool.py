from tools.inspect_audio_block_pool import (
    build_report,
    file_to_cpu,
    lorom_file_offset,
    parse_block_pool,
    parse_selector_table,
)


def test_lorom_roundtrip_high_half():
    for off in (0, 0x7FFF, 0x8000, 0x81234):
        assert lorom_file_offset(file_to_cpu(off)) == off


def test_parse_block_pool_walks_length_prefixed_records():
    rom = bytearray(0x10000)
    start = 0x8000
    rom[start:start + 5] = b"\x05\x00abc"
    rom[start + 5:start + 9] = b"\x04\x00de"
    pool = parse_block_pool(bytes(rom), pool_cpu=0x018000, count=2)
    assert pool["blocks"][0]["payload_length"] == 3
    assert pool["blocks"][1]["file_offset"] == "0x008005"
    assert pool["pool_byte_length"] == 9


def test_selector_table_uses_ff_as_skip_and_sums_payloads():
    rom = bytearray(0x10000)
    # two blocks at file 0x8000
    rom[0x8000:0x8005] = b"\x05\x00abc"
    rom[0x8005:0x8009] = b"\x04\x00de"
    pool = parse_block_pool(bytes(rom), pool_cpu=0x018000, count=2)
    table_off = 0x9000
    raw = bytes([0, 0xFF, 1] + [0xFF] * 61)
    rom[table_off:table_off + 64] = raw
    row = parse_selector_table(bytes(rom), file_to_cpu(table_off), pool["blocks"])
    assert row["block_ids"] == [0, 1]
    assert row["non_ff_count"] == 2
    assert row["selected_payload_bytes"] == 5
    assert row["expected_port3_bytes_including_64_selectors"] == 69


def test_build_report_unions_selector_ids():
    rom = bytearray(0x20000)
    rom[0x8000:0x8004] = b"\x04\x00aa"
    rom[0x8004:0x8008] = b"\x04\x00bb"
    for off, vals in ((0x10000, [0]), (0x10040, [1])):
        rom[off:off + 64] = bytes(vals + [0xFF] * (64 - len(vals)))
    report = build_report(
        bytes(rom),
        pool_cpu=0x018000,
        count=2,
        table_cpus=(file_to_cpu(0x10000), file_to_cpu(0x10040)),
    )
    assert report["selector_id_union"] == [0, 1]
