import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import probe_track_records_sram as tr  # noqa: E402


def clean_image() -> bytearray:
    s = bytearray(0x2000)
    for rank in range(3):
        for tour in range(10):
            for track in range(5):
                i = tr.index(rank, tour, track)
                v = 0 if track == tr.STUNT_TRACK else tr.NO_TIME
                s[tr.RECORDS + 2 * i], s[tr.RECORDS + 2 * i + 1] = v & 0xFF, v >> 8
                s[tr.HOLDERS + i] = tr.NOBODY
    c = tr.checksum(s)
    s[tr.CHECKSUM], s[tr.CHECKSUM + 1] = c & 0xFF, c >> 8
    return s


class TrackRecordsTests(unittest.TestCase):
    def test_index_layout(self) -> None:
        self.assertEqual(tr.index(0, 0, 0), 0)
        self.assertEqual(tr.index(1, 0, 0), 50)
        self.assertEqual(tr.index(0, 1, 2), 7)
        self.assertEqual(tr.RECORDS + 2 * (tr.COUNT - 1), 0x054C)
        self.assertEqual(tr.HOLDERS + tr.COUNT - 1, 0x05E5)

    def test_decode_clean_and_one_record(self) -> None:
        s = clean_image()
        self.assertTrue(all(r["empty"] for r in tr.decode(bytes(s))))
        i = tr.index(0, 0, 0)
        s[tr.RECORDS + 2 * i], s[tr.RECORDS + 2 * i + 1] = 2856 & 0xFF, 2856 >> 8
        s[tr.HOLDERS + i] = 0
        rec = [r for r in tr.decode(bytes(s), ["mike"] + ["x"] * 20) if not r["empty"]]
        self.assertEqual([(r["value"], r["holder_name"], r["kind"]) for r in rec], [(2856, "MIKE", "time_cs")])


if __name__ == "__main__":
    unittest.main()
