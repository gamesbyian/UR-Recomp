from tools.correlate_audio_blocks_spc import best_trimmed_match


def test_best_trimmed_match_finds_exact_payload():
    payload = b"abcdefghijklmnopqrstuvwxyz0123456789"
    ram = b"xx" + payload + b"yy"
    row = best_trimmed_match(payload, ram, min_match=8)
    assert row["apu_offset"] == 2
    assert row["matched_length"] == len(payload)
    assert row["leading_trim"] == 0
    assert row["trailing_trim"] == 0


def test_best_trimmed_match_can_strip_transfer_framing():
    core = b"0123456789abcdefghijklmnopqrstuvwxyz"
    payload = b"HEAD" + core + b"TAIL"
    ram = b"zz" + core + b"qq"
    row = best_trimmed_match(
        payload,
        ram,
        max_leading_trim=4,
        max_trailing_trim=4,
        min_match=8,
    )
    assert row["apu_offset"] == 2
    assert row["matched_length"] == len(core)
    assert row["leading_trim"] == 4
    assert row["trailing_trim"] == 4


def test_best_trimmed_match_returns_none_without_substantial_match():
    assert best_trimmed_match(b"abcdefgh", b"xxxx", min_match=4) is None
