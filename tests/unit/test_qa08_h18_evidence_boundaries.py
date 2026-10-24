"""H18 QA08 archive/observation boundary regressions, not native pixel parity."""
import io
import hashlib
import struct
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa08_brightness_discriminator as audit


def canonical_info(name, **overrides):
    """ZipInfo shaped like the pinned archive: Unix creator, version 45."""
    info = zipfile.ZipInfo(name, date_time=(2026, 10, 19, 12, 0, 0))
    info.create_system = 3
    info.create_version = 45
    info.extract_version = 45
    info.external_attr = 0o100644 << 16
    for key, value in overrides.items():
        setattr(info, key, value)
    return info


def archive_bytes(**overrides):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        for name in ("status.json", "on-source.log", "on-guest-crc.txt",
                     "off-source.log", "off-guest-crc.txt"):
            z.writestr(canonical_info(name, **overrides), b"x")
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

    def test_unindexed_gap_between_local_members_is_rejected(self):
        original = archive_bytes()
        with zipfile.ZipFile(io.BytesIO(original)) as zipfile_reader:
            members = zipfile_reader.infolist()
            insertion = members[1].header_offset
            central = zipfile_reader.start_dir
        padding = b"UNINDEXED-HIDDEN-BYTES"
        patched = bytearray(original[:insertion] + padding + original[insertion:])
        shifted = central + len(padding)
        eocd = patched.rfind(b"PK\x05\x06")
        self.assertGreaterEqual(eocd, 0)
        struct.pack_into("<I", patched, eocd + 16, shifted)
        cursor = shifted
        for _ in range(5):
            self.assertEqual(patched[cursor:cursor+4], b"PK\x01\x02")
            old_offset = struct.unpack_from("<I", patched, cursor+42)[0]
            if old_offset >= insertion:
                struct.pack_into("<I", patched, cursor+42, old_offset+len(padding))
            name_len, extra_len, comment_len = struct.unpack_from("<HHH", patched, cursor+28)
            cursor += 46+name_len+extra_len+comment_len
        with zipfile.ZipFile(io.BytesIO(patched)) as z:
            self.assertIsNone(z.testzip())
            with self.assertRaisesRegex(ValueError, "unindexed|gap"):
                audit._strict_zip_envelope(bytes(patched), z)

    def test_central_directory_creator_version_and_comment_refused(self):
        for overrides in ({"create_system": 0}, {"create_version": 20},
                          {"internal_attr": 1}, {"comment": b"note"}):
            data = archive_bytes(**overrides)
            with self.subTest(overrides=overrides), zipfile.ZipFile(io.BytesIO(data)) as z:
                with self.assertRaisesRegex(
                        ValueError, "comment is not canonical|creator/version/attribute"):
                    audit._strict_zip_envelope(data, z)

    def test_local_header_must_agree_with_central_directory(self):
        data = bytearray(archive_bytes())
        # Corrupt the first local header's extract version (offset 4).
        struct.pack_into("<H", data, 4, 20)
        with zipfile.ZipFile(io.BytesIO(bytes(data))) as z:
            with self.assertRaisesRegex(ValueError, "local member header contradiction"):
                audit._strict_zip_envelope(bytes(data), z)
        # Corrupt the first local header's DOS time (offset 10).
        data = bytearray(archive_bytes())
        struct.pack_into("<H", data, 10, 0x1234)
        with zipfile.ZipFile(io.BytesIO(bytes(data))) as z:
            with self.assertRaisesRegex(ValueError, "local member header contradiction"):
                audit._strict_zip_envelope(bytes(data), z)

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


PALETTE = ("4210", "4631", "4a52", "56b5")


def observer_rows(slot_for=lambda frame, ordinal: ordinal % 4):
    """Synthetic 264-row transcript in observer order (0, 1, final per anchor)."""
    anchors = sorted(audit.ANCHORS, key=lambda xy: (xy[1], xy[0]))
    rows = []
    for frame in sorted(audit.FRAMES):
        for ordinal, (x, y) in enumerate(anchors):
            slot = slot_for(frame, ordinal)
            word = PALETTE[slot]
            common = dict(frame=str(frame), x=str(x), logical_y=str(y),
                          ppu_line=str(y + 1))
            cgram = dict(cgram6c=PALETTE[0], cgram6d=PALETTE[1],
                         cgram6e=PALETTE[2], cgram6f=PALETTE[3])
            main = dict(common, sub="0", layer="0", directcolor="0",
                        index=f"{0x6c + slot:02x}", selected_rgb555=word,
                        cgram_index_word=word, inidisp="0e", cgadsub="7f",
                        cgwsel="02", **cgram)
            sub = dict(common, sub="1", layer="5", directcolor="0", index="00",
                       selected_rgb555="39ce", cgram_index_word="39ce",
                       inidisp="0e", cgadsub="7f", cgwsel="02", **cgram)
            final = dict(common, RGB8=",".join(map(str, audit.expected_rgb(word, 14))),
                         inidisp="0e", fixed="0000", tm="13", ts="10")
            for prefix, fields in (("UR_QA08_LATE_PPU_SOURCE", main),
                                   ("UR_QA08_LATE_PPU_SOURCE", sub),
                                   ("UR_QA08_LATE_PPU_FINAL", final)):
                rows.append(prefix + " " + " ".join(f"{k}={v}" for k, v in fields.items()))
    return rows


def crlf_blob(rows):
    return b"".join(row.encode("ascii") + b"\r\n" for row in rows)


class SourceTranscriptCensus(unittest.TestCase):
    def test_observer_order_transcript_parses(self):
        rows = observer_rows()
        self.assertEqual(len(rows), 264)
        self.assertEqual(audit._chronological_source_rows(crlf_blob(rows)), rows)
        result = audit.parse(rows)
        self.assertEqual(result["observed_counts"], {w: 22 for w in PALETTE})

    def test_each_frame_must_sample_each_class_twice(self):
        # Frame 5176 takes one extra 4210 and one fewer 56b5; frame 5177 the
        # opposite, so the global histogram is unchanged but both frames lie.
        def moved(frame, ordinal):
            base = ordinal % 4
            if frame == 5176 and ordinal == 3:
                return 0
            if frame == 5177 and ordinal == 0:
                return 3
            return base
        with self.assertRaisesRegex(ValueError, "per-frame four-class raster census"):
            audit.parse(observer_rows(moved))

    def test_permuted_but_individually_valid_rows_are_refused(self):
        rows = observer_rows()
        rows[0], rows[1] = rows[1], rows[0]
        with self.assertRaisesRegex(ValueError, "chronological stage order"):
            audit._chronological_source_rows(crlf_blob(rows))
        rows = observer_rows()
        rows[3:6], rows[6:9] = rows[6:9], rows[3:6]
        with self.assertRaisesRegex(ValueError, "chronological stage order"):
            audit._chronological_source_rows(crlf_blob(rows))


if __name__ == "__main__":
    unittest.main()
