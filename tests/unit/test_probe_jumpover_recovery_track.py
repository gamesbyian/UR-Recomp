"""ROM-free contract for extended, controlled Jumpover recovery survey."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_jumpover_recovery_track as rc  # noqa: E402


def image(y=1200, track=19, active=1, size=0x20000, air=0):
    b = bytearray(size)
    if size > 0x545:
        b[0x00CE] = track
        b[0x0313] = active
        b[0x0415:0x0417] = y.to_bytes(2, "little")
        b[0x0545] = air
    return bytes(b)


class RecoveryProbeTests(unittest.TestCase):
    def test_sampling_and_script_continuity(self):
        self.assertEqual(rc.sample_frames(110, 4), [100, 104, 108, 110])
        with self.assertRaises(rc.RecoveryEvidenceError):
            rc.sample_frames(609, 4)
        ref_frame = 1088
        splice = ref_frame + rc.jf.ROUTES["right"]["splice_offset"]
        script = rc.extension_script(ref_frame, splice, 36, 72, 120, 5)
        self.assertEqual(script.count("poke 11CF 4800"), 1)
        self.assertEqual(script.count("dump s"), len(rc.sample_frames(120, 5)))
        self.assertTrue(script.endswith("quit\n"))

    def test_movie_extension_and_original_shoulder_control(self):
        for name in ("right", "left"):
            fall = rc.long_movie(name, 280, control=False)
            control = rc.long_movie(name, 280, control=True)
            self.assertEqual(len(fall), 281)
            self.assertEqual(len(control), 281)
            changes = [i for i, (a, b) in enumerate(zip(fall, control)) if a != b]
            self.assertEqual(changes, [rc.jf.CONTROL_SAMPLE])
            self.assertEqual(fall[-1], fall[-2])

    def test_load_capture_rejects_gaps_foreign_races_and_bad_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            for i in rc.sample_frames(110, 4):
                (d / f"s{i:03d}.wram.bin").write_bytes(image())
            rows = rc.read_series(d, 110, 4)
            self.assertEqual(len(rows), 4)
            self.assertEqual(rc.classify_scout(rows)["contact_below_old_floor_sample_frames"],
                             [100, 104, 108, 110])
            self.assertIsNone(rc.compare(rows, copy.deepcopy(rows))["first_divergence"])
            path = d / "s110.wram.bin"
            for data, match in ((image(size=0x2000), "expected"),
                                (image(track=21), "not active Jumpover"),
                                (image(active=0), "not active Jumpover")):
                path.write_bytes(data)
                with self.assertRaisesRegex(rc.RecoveryEvidenceError, match):
                    rc.read_series(d, 110, 4)
            path.unlink()
            with self.assertRaisesRegex(rc.RecoveryEvidenceError, "missing"):
                rc.read_series(d, 110, 4)

    def test_first_semantic_divergence_without_claiming_recovery(self):
        base = {k: 0 for k in rc.jf.FIELDS}
        base["y"] = 1300
        base["air_time"] = 0
        refs = {100: dict(base), 104: dict(base)}
        nat = copy.deepcopy(refs)
        nat[104]["contact_word"] = 14
        result = rc.compare(refs, nat)
        self.assertEqual(result["first_divergence"],
                         {"sample": 104, "fields": ["contact_word"]})
        self.assertEqual(result["reference"]["recovery_surface_classification"].split(":")[0],
                         "unknown")
        with self.assertRaisesRegex(rc.RecoveryEvidenceError, "nonempty"):
            rc.compare({}, {})


if __name__ == "__main__":
    unittest.main()
