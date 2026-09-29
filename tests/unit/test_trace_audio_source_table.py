from tools.trace_audio_source_table import byte_before_block, lorom_file_offset, pointer_before_block


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
