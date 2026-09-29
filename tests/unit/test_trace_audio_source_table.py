from tools.trace_audio_source_table import (
    byte_before_block,
    lorom_file_offset,
    pointer_before_block,
    transfer_seed_events,
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


def test_transfer_seed_events_require_exact_word_write_at_83():
    writers = {
        "addresses": {
            "0x0083": {
                "writes": [
                    {"f": 920, "adr": "0x00083", "val": "0x00C123", "w": 2, "bi": 44, "func": "interp@$8282A9", "parent": ""},
                    {"f": 921, "adr": "0x00082", "val": "0x001234", "w": 2, "bi": 45, "func": "other", "parent": ""},
                    {"f": 850, "adr": "0x00083", "val": "0x00D000", "w": 2, "bi": 46, "func": "old", "parent": ""},
                ]
            }
        }
    }
    rows = transfer_seed_events(writers)
    assert len(rows) == 1
    assert rows[0]["x_value"] == "0xC123"
    assert rows[0]["source_pointer_03x"] == "0x03C123"
    assert rows[0]["source_file_offset"] == "0x01C123"
