from __future__ import annotations

import gzip
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from extract_smv_freeze import (  # noqa: E402
    FreezeError,
    main,
    parse_freeze,
    summarize_movie,
)
from probe_jumpover_fallthrough import (  # noqa: E402
    classify,
    controller_samples,
    first_divergence,
    rebuild_smv,
)


def block(tag: str, payload: bytes) -> bytes:
    return f"{tag}:{len(payload):06d}:".encode("ascii") + payload


def make_wram() -> bytearray:
    wram = bytearray(0x20000)
    struct.pack_into("<H", wram, 0x0411, 3930)
    struct.pack_into("<H", wram, 0x0415, 544)
    struct.pack_into("<h", wram, 0x04B7, -500)
    struct.pack_into("<H", wram, 0x04C7, 0x0135)  # low 6 bits = 53
    struct.pack_into("<H", wram, 0x0413, 2677)
    wram[0x0313] = 1
    wram[0x00CE] = 19
    return wram


def make_freeze(wram: bytes | None = None, magic: bytes = b"#!snes9x:1510\n", ram_tag: str = "RAM") -> bytes:
    wram = make_wram() if wram is None else wram
    return (
        magic
        + block("NAM", b"Uniracers (U) [!].smc\x00")
        + block("CPU", bytes(58))
        + block("REG", bytes.fromhex("820000050068000001ed000c0006a896"))
        + block(ram_tag, bytes(wram))
        + block("SRA", bytes(16))
    )


def make_smv(state: bytes, samples=(0x0200, 0x8200, 0x82A0), movie_options: int = 0) -> bytes:
    metadata = " ".encode("utf-16le")
    rominfo = b"\x00\x00\x00" + struct.pack("<I", 0x383858C7) + b"UNIRACERS".ljust(23, b"\x00")
    save_off = 0x40 + len(metadata) + len(rominfo)
    ctrl_off = save_off + len(state)
    hdr = bytearray(0x40)
    hdr[0:4] = b"SMV\x1a"
    struct.pack_into("<I", hdr, 4, 4)
    struct.pack_into("<I", hdr, 8, 0x4C6424D1)
    struct.pack_into("<I", hdr, 0x10, len(samples))
    hdr[0x14] = 0x01
    hdr[0x15] = movie_options
    hdr[0x17] = 0xF1
    struct.pack_into("<II", hdr, 0x18, save_off, ctrl_off)
    struct.pack_into("<I", hdr, 0x20, len(samples))
    hdr[0x24] = hdr[0x25] = 1
    ctrl = b"".join(struct.pack("<H", s) for s in samples)
    return bytes(hdr) + metadata + rominfo + state + ctrl + b"\x00\x00"


class ExtractSmvFreezeTests(unittest.TestCase):
    def write(self, td: str, data: bytes) -> Path:
        path = Path(td) / "movie.smv"
        path.write_bytes(data)
        return path

    def test_valid_embedded_freeze_summary(self):
        freeze = make_freeze()
        with tempfile.TemporaryDirectory() as td:
            path = self.write(td, make_smv(gzip.compress(freeze, mtime=0) + b"\xcc" * 3))
            summary, out = summarize_movie(path)
        self.assertEqual(out, freeze)
        self.assertEqual(summary["freeze_version"], 1510)
        self.assertEqual(summary["post_gzip_padding_bytes"], 3)
        self.assertEqual([b["tag"] for b in summary["blocks"]], ["NAM", "CPU", "REG", "RAM", "SRA"])
        self.assertEqual(summary["cpu_registers"]["pb_pc"], "82:A896")
        self.assertEqual(summary["cpu_registers"]["s"], "01ED")
        self.assertEqual(summary["freeze_rom_name"], "Uniracers (U) [!].smc")
        fields = summary["anchor_fields"]
        self.assertEqual(
            (fields["p1_x"], fields["p1_y"], fields["p1_x_speed"], fields["p1_pitch"], fields["p2_x"]),
            (3930, 544, -500, 53, 2677),
        )
        self.assertEqual((fields["race_active"], fields["track_id"]), (1, 19))

    def test_cli_writes_json_and_scratch_freeze(self):
        freeze = make_freeze()
        with tempfile.TemporaryDirectory() as td:
            path = self.write(td, make_smv(gzip.compress(freeze, mtime=0)))
            out_json = Path(td) / "anchor.json"
            rc = main([str(path), "--json-out", str(out_json), "--freeze-out-dir", str(Path(td) / "frz")])
            self.assertEqual(rc, 0)
            doc = json.loads(out_json.read_text())
            self.assertEqual(doc["kind"], "smv-embedded-freeze-anchor")
            self.assertEqual(doc["field_symbols"]["p1_x"]["wram"], "7E:0411")
            self.assertEqual((Path(td) / "frz" / "movie.frz").read_bytes(), freeze)

    def test_truncated_gzip_is_rejected(self):
        packed = gzip.compress(make_freeze(), mtime=0)
        with tempfile.TemporaryDirectory() as td:
            path = self.write(td, make_smv(packed[: len(packed) // 2]))
            with self.assertRaisesRegex(FreezeError, "truncated|corrupt"):
                summarize_movie(path)

    def test_non_gzip_region_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write(td, make_smv(make_freeze()))
            with self.assertRaisesRegex(FreezeError, "gzip"):
                summarize_movie(path)

    def test_wrong_freeze_magic_is_rejected(self):
        packed = gzip.compress(make_freeze(magic=b"#!s9xsnp:0012\n"), mtime=0)
        with tempfile.TemporaryDirectory() as td:
            path = self.write(td, make_smv(packed))
            with self.assertRaisesRegex(FreezeError, "snes9x"):
                summarize_movie(path)

    def test_wrong_smv_magic_is_rejected(self):
        data = bytearray(make_smv(gzip.compress(make_freeze(), mtime=0)))
        data[0:4] = b"BK2\x1a"
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(FreezeError, "not an SMV"):
                summarize_movie(self.write(td, bytes(data)))

    def test_missing_ram_block_is_rejected(self):
        packed = gzip.compress(make_freeze(ram_tag="VRA"), mtime=0)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(FreezeError, "no RAM"):
                summarize_movie(self.write(td, make_smv(packed)))

    def test_short_ram_block_is_rejected(self):
        packed = gzip.compress(make_freeze(wram=bytes(0x100)), mtime=0)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(FreezeError, "expected 131072"):
                summarize_movie(self.write(td, make_smv(packed)))

    def test_truncated_block_is_rejected(self):
        with self.assertRaisesRegex(FreezeError, "truncated"):
            parse_freeze(b"#!snes9x:1510\nRAM:131072:" + bytes(10))

    def test_reset_anchored_movie_is_rejected(self):
        packed = gzip.compress(make_freeze(), mtime=0)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(FreezeError, "reset-anchored"):
                summarize_movie(self.write(td, make_smv(packed, movie_options=1)))

    def test_cli_reports_error_code(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write(td, make_smv(make_freeze()))
            self.assertEqual(main([str(path)]), 2)


def rows(ys, airs):
    return [
        {"frame": i, "p1_y": y, "p1_air_time": a, "p1_pitch": 0}
        for i, (y, a) in enumerate(zip(ys, airs))
    ]


class JumpoverProbeAnalysisTests(unittest.TestCase):
    def test_rebuild_replaces_inputs_and_patches_anchor_wram(self):
        src = make_smv(gzip.compress(make_freeze(), mtime=0))
        out = rebuild_smv(src, samples=[0x0200] * 5, wram_writes={0x0411: 4000})
        self.assertEqual(controller_samples(out), [0x0200] * 5)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "rebuilt.smv"
            path.write_bytes(out)
            summary, _ = summarize_movie(path)
        self.assertEqual(summary["frame_count_header"], 5)
        self.assertEqual(summary["anchor_fields"]["p1_x"], 4000)
        self.assertEqual(summary["anchor_fields"]["p2_x"], 2677)

    def test_rebuild_without_changes_keeps_inputs(self):
        src = make_smv(gzip.compress(make_freeze(), mtime=0))
        self.assertEqual(rebuild_smv(src), src)

    def test_fall_through_against_ordinary_control(self):
        control = rows([544, 530, 560, 700, 760, 740, 720] + [720] * 12, [0, 1, 9, 9, 0, 0, 0] + [0] * 12)
        case = rows([544, 530, 560, 700, 800, 900] + [1000 + 10 * i for i in range(13)], [0, 1, 9, 9, 9, 9] + [9] * 13)
        result = classify(case, control)
        self.assertEqual(result["outcome"], "fall_through")
        self.assertEqual(result["first_frame_below_control_floor"], 4)
        self.assertEqual(classify(control, control)["outcome"], "ordinary")

    def test_late_lower_surface_contact_is_reported_not_recovery(self):
        control = rows([544, 530, 760, 740] + [740] * 15, [0, 1, 0, 0] + [0] * 15)
        airs = [0, 1, 9] + [9] * 13 + [0, 0, 1]
        case = rows([544, 530, 560] + [800 + 10 * i for i in range(16)], airs)
        result = classify(case, control)
        self.assertEqual(result["outcome"], "fall_through")
        self.assertEqual(result["first_contact_below_control_floor"]["frame"], 16)

    def test_control_must_be_an_ordinary_traversal(self):
        never_lands = rows([544, 530, 600, 700], [0, 1, 9, 9])
        with self.assertRaisesRegex(ValueError, "ordinary traversal"):
            classify(never_lands, never_lands)
        with self.assertRaisesRegex(ValueError, "direction-matched control"):
            classify(never_lands, [])

    def test_post_crossing_requires_full_airborne_witness(self):
        control = rows([0, 1, 2, 3] + [3] * 12, [0, 1, 0, 0] + [0] * 12)
        incomplete = rows([0, 1, 2, 4, 5, 6], [0, 1, 9, 9, 9, 9])
        with self.assertRaisesRegex(ValueError, "insufficient post-crossing"):
            classify(incomplete, control)

    def test_gapped_or_shifted_frames_are_not_valid_physics_evidence(self):
        control = rows([0, 1, 2, 3], [0, 1, 0, 0])
        dropped = [dict(r) for r in control]
        dropped.pop(1)
        with self.assertRaisesRegex(ValueError, "consecutive integers"):
            classify(control, dropped)
        shifted = [dict(r, frame=r["frame"] + 1) for r in control]
        with self.assertRaisesRegex(ValueError, "same frame"):
            classify(control, shifted)

    def test_first_divergence_rejects_empty_captures(self):
        a = rows([1, 2], [0, 0])
        for left, right in (([], []), (a, []), ([], a)):
            with self.subTest(left=len(left), right=len(right)):
                with self.assertRaisesRegex(ValueError, "nonempty captures"):
                    first_divergence(left, right, ("p1_y",))

    def test_first_divergence_rejects_missing_or_shifted_frames(self):
        a = rows([1, 2, 3], [0, 0, 0])
        with self.assertRaisesRegex(ValueError, "different frame counts"):
            first_divergence(a, a[:2], ("p1_y",))
        shifted = [dict(r, frame=r["frame"] + 1) for r in a]
        with self.assertRaisesRegex(ValueError, "frame-aligned"):
            first_divergence(a, shifted, ("p1_y",))
        duplicate = [dict(r) for r in a]
        duplicate[2]["frame"] = 1
        with self.assertRaisesRegex(ValueError, "consecutive integers"):
            first_divergence(a, duplicate, ("p1_y",))

    def test_first_divergence(self):
        a = rows([1, 2, 3], [0, 0, 0])
        b = rows([1, 2, 4], [0, 1, 0])
        self.assertEqual(first_divergence(a, b, ("p1_y", "p1_air_time")), {"frame": 1, "fields": ["p1_air_time"]})
        self.assertIsNone(first_divergence(a, a, ("p1_y",)))


if __name__ == "__main__":
    unittest.main()
