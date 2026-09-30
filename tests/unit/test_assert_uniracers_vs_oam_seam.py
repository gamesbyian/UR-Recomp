import tempfile
from pathlib import Path

import pytest

from tools.assert_uniracers_vs_oam_seam import assert_vs_oam_seam, parse_ppuw


def test_parse_and_assert_canonical_vs_seam():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "race.ppuw.tsv"
        path.write_text(
            "1140\t0\t283\t2104\tA5\thdma\n"
            "1140\t112\t284\t2104\t5A\thdma\n"
            "1140\t229\t10\t2104\t44\tdma\n",
            encoding="utf-8",
        )
        rows = parse_ppuw(path)
        assert len(rows) == 3
        result = assert_vs_oam_seam([path])[0]
        assert result["v0_values"] == [0xA5]
        assert result["v112_values"] == [0x5A]


def test_missing_scanline_112_fails():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "bad.ppuw.tsv"
        path.write_text("1\t0\t10\t2104\tA5\thdma\n", encoding="utf-8")
        with pytest.raises(AssertionError):
            assert_vs_oam_seam([path])
