import csv
from pathlib import Path
import tempfile
import unittest

from tools.select_racer_hd_same_state_native_frame import select


STATE = (
    "p1_primary=0541 p2_primary=0540 p1_companion=0D0D "
    "p2_companion=0000 p1_selector=0000 p2_selector=0000 "
    "p1_gate=0001 p2_gate=0000"
)
OTHER = STATE.replace("p1_companion=0D0D", "p1_companion=0D2D")


def trace(frame, state=STATE):
    return f"UR_RACER_PRESENTATION_TRACE frame={frame} {state}\n"


def ppm(width=256, height=224, rgb=(10, 20, 30)):
    return f"P6\n{width} {height}\n255\n".encode() + bytes(rgb) * (width * height)


def write_capture(path: Path, guest_frames, images):
    path.mkdir()
    with (path / "presents.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["present", "frame"])
        for index, frame in enumerate(guest_frames):
            writer.writerow([index, frame])
            (path / f"present_{index:06d}.ppm").write_bytes(images[index])


class RacerNativeExactStateScreenshotTests(unittest.TestCase):
    def test_selects_only_native_present_with_exact_eight_word_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_capture(root / "captures", [1219, 1220, 1221],
                          [ppm(rgb=(1, 2, 3)), ppm(rgb=(4, 5, 6)), ppm()])
            ref = trace(1220)
            cand = trace(1219, OTHER) + trace(1220, OTHER) + trace(1221)
            image, report = select(
                ref, cand, root / "captures", reference_frame=1220
            )
            self.assertEqual(image, ppm())
            self.assertEqual(report["selected_guest_frame"], 1221)
            self.assertEqual(report["guest_frame_offset"], 1)
            self.assertEqual(report["matching_state_fields"]["p1_companion"], "0D0D")

    def test_rejects_multiple_same_state_guest_frames_and_missing_present(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_capture(root / "captures", [1219], [ppm()])
            with self.assertRaisesRegex(ValueError, "exactly one"):
                select(trace(1220), trace(1219) + trace(1221),
                       root / "captures", reference_frame=1220)
            with self.assertRaisesRegex(ValueError, "missing captured"):
                select(trace(1220), trace(1221), root / "captures",
                       reference_frame=1220)

    def test_rejects_wrong_density_and_inconsistent_repeated_presents(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            images = [ppm(), ppm(rgb=(20, 21, 22))]
            write_capture(root / "captures", [1221, 1221], images)
            with self.assertRaisesRegex(ValueError, "different output pixels"):
                select(trace(1220), trace(1221), root / "captures",
                       reference_frame=1220)
            (root / "captures" / "present_000001.ppm").write_bytes(ppm(342, 224))
            with self.assertRaisesRegex(ValueError, "wrong screenshot density"):
                select(trace(1220), trace(1221), root / "captures",
                       reference_frame=1220)


if __name__ == "__main__":
    unittest.main()
