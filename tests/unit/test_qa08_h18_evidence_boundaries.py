"""H18 QA08 archive/observation boundary regressions, not native pixel parity."""
import io
import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa08_brightness_discriminator as audit


def archive_bytes():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        for name in ("status.json", "on-source.log", "on-guest-crc.txt",
                     "off-source.log", "off-guest-crc.txt"):
            z.writestr(name, b"x")
    return stream.getvalue()


class H18EvidenceBoundaries(unittest.TestCase):
    def test_canonical_archive_envelope(self):
        data = archive_bytes()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            audit._strict_zip_envelope(data, z)

    def test_trailer_and_comment_refused(self):
        plain = archive_bytes()
        altered = (plain + b"UNINDEXED_TRAILER",
                   plain[:-2] + b"\x03\x00abc")
        for data in altered:
            with self.subTest(data=data[-18:]), zipfile.ZipFile(io.BytesIO(data)) as z:
                with self.assertRaisesRegex(ValueError, "trailer|comment"):
                    audit._strict_zip_envelope(data, z)

    def test_unindexed_prefix_refused(self):
        data = b"PRELUDE" + archive_bytes()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            with self.assertRaisesRegex(ValueError, "prefix|central-directory"):
                audit._strict_zip_envelope(data, z)

    def test_canonical_observation_requires_full_source_schema(self):
        fields = dict(frame="5176", x="53", logical_y="41", ppu_line="42",
                      sub="0", layer="0", directcolor="0", index="6c",
                      selected_rgb555="4210", cgram_index_word="4210",
                      cgram6c="4210", cgram6d="56b5", cgram6e="4a52",
                      cgram6f="4631", inidisp="0e", cgadsub="7f", cgwsel="02")
        audit._canonical_observation(fields, "UR_QA08_LATE_PPU_SOURCE")
        for key, value in (("index", "6C"), ("frame", "05176"),
                           ("selected_rgb555", "4210x")):
            changed = dict(fields, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                audit._canonical_observation(changed, "UR_QA08_LATE_PPU_SOURCE")

    def test_source_crlf_envelope_cannot_alias_other_linebreaks(self):
        with self.assertRaisesRegex(ValueError, "CRLF envelope"):
            audit._canonical_source_rows(b"x\n" * 264)
        with self.assertRaises(ValueError):
            audit._canonical_source_rows(b"x\r\n" * 263 + b"x\v\r\n")


if __name__ == "__main__":
    unittest.main()
