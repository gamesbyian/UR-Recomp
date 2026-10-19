"""ROM-free exact-source SMV input-window attestation, never event admission."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_event_historical_source_attestation as historical
import qa01_event_route_artifact_audit as route


def genuine_shape_fixture(root: Path, case: str = "zoom-zoo"):
    course, first, last = historical.SOURCE_EVENT_ANCHORS[case]
    size, offset, uid, crc = 12000, 256, 0xAABBCCDD, 0x383858C7
    data = bytearray(offset + size * 2)
    data[:4] = b"SMV\x1a"
    def u32(at, value): struct.pack_into("<I", data, at, value)
    u32(4, 4)
    u32(8, uid)
    u32(0x18, 200)
    u32(0x1C, offset)
    u32(0x20, size)
    data[0x14] = 1
    data[0x15] = 1
    data[0x17] = 0x40
    u32(173, crc)
    for at, value in ((first + 10, 0x0080), (first + 11, 0x0080),
                      (first + 60, 0x4000), (first + 61, 0x4000)):
        struct.pack_into("<H", data, offset + 2 * at, value)
    source_len = (last - first) + 80
    window = bytes(data[offset + 2 * first:offset + 2 * (first + source_len)])
    source_digest = hashlib.sha256(window).hexdigest()
    movie = root / "2014.smv"
    movie.write_bytes(data)
    metadata = {
        "version": 4, "uid": uid, "sample_count": size,
        "controller_mask": 1, "reset_anchored": True,
        "rom_info": {"crc32": f"{crc:08x}"},
        "controller_data_offset": offset,
    }
    meta = root / "2014-metadata.json"
    meta.write_text(json.dumps(metadata), encoding="utf-8")
    report = {
        "name": case, "course_id": course,
        "original_source_event": {
            "original_entry_frame": first,
            "original_result_frame": last,
            "source_active_frames_to_result": last - first,
        },
        "original_movie_sha256": hashlib.sha256(data).hexdigest(),
        "original_movie_window_sha256": source_digest,
        "reference_entry": 100,
        "native_frame_shift": 1,
        "relative_sample_frames": [0, 1, 2],
        "input_sha256": hashlib.sha256(
            b"dump race-entered\ndump scene-00001\ndump scene-00002\n"
            b"dump result-onset\ndump result-stable\n").hexdigest(),
        "reference_script_sha256": hashlib.sha256(
            b"dump race-entered\ndump scene-00001\ndump scene-00002\n"
            b"dump result-onset\ndump result-stable\n").hexdigest(),
    }
    return movie, meta, report, source_len


class HistoricControllerSourceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.movie, self.meta, self.report, self.n = genuine_shape_fixture(self.root)
        self.patch = patch.object(
            historical, "SOURCE_2014_ARCHIVE_SHA256",
            self.report["original_movie_sha256"])
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_exact_source_movie_window_recovered_and_route_bound(self):
        observed = historical.source_window(self.report, self.movie, self.meta)
        self.assertEqual(observed["frames"], self.n)
        self.assertEqual(
            observed["raw_controller_window_sha256"],
            self.report["original_movie_window_sha256"])
        self.assertEqual(len(observed["relative_input_segments"]), 2)
        target = self.root / "work" / "zoom-zoo" / "replay"
        target.mkdir(parents=True)
        src = [
            (100 + row["start"], row["duration"], int(row["mask"], 16))
            for row in observed["relative_input_segments"]
        ]
        (target / "ref.input").write_text(
            "".join(f"{a}:{b}:{c:03x}\n" for a,b,c in src))
        (target / "pinned-baldosa.input").write_text(
            "".join(f"{a+1}:{b}:{c:03x}\n" for a,b,c in src))
        (target / "complete.script").write_text(
            "dump race-entered\ndump scene-00001\ndump scene-00002\n"
            "dump result-onset\ndump result-stable\n")
        verified = route.audit(self.root, self.report, source_window=observed)
        self.assertTrue(verified["original_2014_movie_controller_window_recomputed"])
        self.assertEqual(verified["input_event_rows_per_guest"], 2)
        self.assertEqual(verified["release_credit"], 0)
        # Two internally consistent *forged* original and native files fail
        # even though their relative +1 guest frame calibration still agrees.
        src[0] = (src[0][0], src[0][1], src[0][2] ^ 2)
        (target / "ref.input").write_text(
            "".join(f"{a}:{b}:{c:03x}\n" for a,b,c in src))
        (target / "pinned-baldosa.input").write_text(
            "".join(f"{a+1}:{b}:{c:03x}\n" for a,b,c in src))
        with self.assertRaisesRegex(ValueError, "source-movie controller window"):
            route.audit(self.root, self.report, source_window=observed)

    def test_forged_original_movie_sha_or_controller_window_denied(self):
        with self.assertRaisesRegex(ValueError, "exact immutable source"):
            historical.source_window(
                dict(self.report, original_movie_sha256="f"*64),
                self.movie, self.meta)
        with self.assertRaisesRegex(ValueError, "no unique"):
            historical.source_window(
                dict(self.report, original_movie_window_sha256="e"*64),
                self.movie, self.meta)

    def test_wrong_source_entry_or_original_event_result_is_not_admitted(self):
        report = json.loads(json.dumps(self.report))
        report["original_source_event"]["original_result_frame"] += 1
        with self.assertRaisesRegex(ValueError, "event identity"):
            historical.source_window(report, self.movie, self.meta)

    def test_mutated_original_crc_or_fake_metadata_fails_after_hash_selection(self):
        bad = json.loads(self.meta.read_text())
        bad["rom_info"]["crc32"] = "ffffffff"
        self.meta.write_text(json.dumps(bad))
        with self.assertRaisesRegex(ValueError, "ROM CRC"):
            historical.source_window(self.report, self.movie, self.meta)

    def test_truncated_source_window_without_unique_source_hash_fails(self):
        data = self.movie.read_bytes()
        m = json.loads(self.meta.read_text())
        with self.assertRaisesRegex(ValueError, "truncated"):
            historical.select_source_controller_length(
                data[:400], m, 3190, 5163,
                self.report["original_movie_window_sha256"])


if __name__ == "__main__":
    unittest.main()
