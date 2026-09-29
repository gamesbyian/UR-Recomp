from tools.trace_audio_source_table import (
    byte_before_block,
    lorom_file_offset,
    paired_dp83_values,
    pointer_before_block,
    static_ldx_seeds,
)


def test_lorom_file_offset_accepts_low_and_high_mirrors():
    assert lorom_file_offset(0x028298) == 0x010298
    assert lorom_file_offset(0x828298) == 0x010298


def test_lorom_file_offset_rejects_low_half_address():
    assert lorom_file_offset(0x020123) is None


def test_byte_before_block_uses_latest_prior_write():
    writes = [
        {"bi": 10, "val": "0x0011"},
        {"bi": 20, "val": "0x0022"},
        {"bi": 30, "val": "0x0033"},
    ]
    assert byte_before_block(writes, 9) is None
    assert byte_before_block(writes, 20) == 0x22
    assert byte_before_block(writes, 29) == 0x22


def test_pointer_before_block_reconstructs_three_bytes():
    writers = {
        "addresses": {
            "0x0000": {"writes": [{"bi": 10, "val": "0x0034"}]},
            "0x0001": {"writes": [{"bi": 11, "val": "0x00A2"}]},
            "0x0002": {"writes": [{"bi": 12, "val": "0x0085"}]},
        }
    }
    assert pointer_before_block(writers, 0, 12) == 0x85A234
    assert pointer_before_block(writers, 0, 11) is None


def test_paired_dp83_values_joins_byte_writes_by_block():
    writers = {
        "addresses": {
            "0x0083": {"writes": [{"f": 906, "bi": 100, "val": "0x55", "func": "lo"}]},
            "0x0084": {"writes": [{"f": 906, "bi": 100, "val": "0xFB", "func": "hi"}]},
        }
    }
    rows = paired_dp83_values(writers)
    assert rows[0]["x_value"] == "0xFB55"
    assert rows[0]["source_pointer_03x"] == "0x03FB55"


def test_static_ldx_seeds_reads_immediate_before_jsl():
    calls = {
        "patterns": {
            "JSL_8282A5": [{
                "rom_offset_hex": "0x00145C",
                "cpu_pc24": "0x80945C",
                "context_start_hex": "0x001450",
                "context_hex": "00 00 00 00 00 00 00 00 00 a2 55 fb 22 a5 82 82",
            }]
        }
    }
    rows = static_ldx_seeds(calls)
    assert rows[0]["x_seed"] == "0xFB55"
    assert rows[0]["source_pointer_03x"] == "0x03FB55"
    assert rows[0]["source_file_offset"] == "0x01FB55"
