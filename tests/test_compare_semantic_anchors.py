#!/usr/bin/env python3
"""Regression tests for relocation-tolerant semantic anchor matching."""
from tools.compare_semantic_anchors import Anchor, score_candidates


def test_relocated_semantic_match_beats_stale_same_offset():
    anchor = Anchor(
        "synthetic",
        "80:8000",
        64,
        (0x0411, 0x04B7, 0x11CD),
        "synthetic relocation test",
    )

    source = bytearray(range(64))
    source[8:10] = (0x0411).to_bytes(2, "little")
    source[24:26] = (0x04B7).to_bytes(2, "little")
    source[40:42] = (0x11CD).to_bytes(2, "little")

    usa = bytes(source) + bytes(256)

    target = bytearray([0x55] * 512)
    moved = 160
    target[moved:moved + 64] = source

    # Simulate relocation/build edits without destroying the semantic signature.
    target[moved + 3] ^= 0x7F
    target[moved + 18] ^= 0x22
    target[moved + 52] ^= 0x11

    matches = score_candidates(
        anchor,
        usa,
        bytes(target),
        top=5,
        k=6,
        stride=3,
    )

    assert matches, "expected at least one correspondence candidate"
    assert matches[0]["file_offset"] == moved
    assert not matches[0]["same_offset_as_usa"]
    assert matches[0]["semantic_reference_recall"] == 1.0


if __name__ == "__main__":
    test_relocated_semantic_match_beats_stale_same_offset()
    print("ok")
