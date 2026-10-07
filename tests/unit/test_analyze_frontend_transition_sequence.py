import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "analyze_frontend_transition_sequence.py"

spec = importlib.util.spec_from_file_location("transition_sequence", TOOL)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def frame(width, height, fn):
    out = bytearray()
    for y in range(height):
        for x in range(width):
            value = fn(x, y)
            out.extend((value, value ^ 0x55, value ^ 0xAA, 0xFF))
    return bytes(out)


def shift_down(source, width, height, shift):
    row_bytes = width * 4
    out = bytearray(len(source))
    black_row = bytes((0, 0, 0, 255)) * width
    for y in range(height):
        dst = y * row_bytes
        if y >= shift:
            src = (y - shift) * row_bytes
            out[dst:dst + row_bytes] = source[src:src + row_bytes]
        else:
            out[dst:dst + row_bytes] = black_row
    return bytes(out)


def shift_right(source, width, height, shift):
    row_bytes = width * 4
    out = bytearray(len(source))
    for y in range(height):
        for x in range(width):
            dst = y * row_bytes + x * 4
            if x >= shift:
                src = y * row_bytes + (x - shift) * 4
                out[dst:dst + 4] = source[src:src + 4]
            else:
                out[dst:dst + 4] = bytes((0, 0, 0, 255))
    return bytes(out)


class FrontendTransitionSequenceTests(unittest.TestCase):
    def test_detects_known_horizontal_translation(self):
        width = 24
        height = 8
        before = frame(width, height, lambda x, y: (x * 7 + y * 19) & 0xFF)
        after = shift_right(before, width, height, 3)

        result = module.best_horizontal_shift(
            before,
            after,
            width=width,
            max_shift=5,
            sample_step=1,
        )
        self.assertEqual(result["best_shift_pixels"], 3)
        self.assertGreater(result["best_agreement"], 0.95)
        self.assertGreater(result["agreement_gain"], 0.5)

    def test_detects_known_vertical_translation(self):
        width = 24
        height = 12
        before = frame(width, height, lambda x, y: (x * 5 + y * 23) & 0xFF)
        after = shift_down(before, width, height, 2)

        result = module.best_vertical_shift(
            before,
            after,
            width=width,
            max_shift=4,
            sample_step=1,
        )
        self.assertEqual(result["best_vertical_shift_pixels"], 2)
        self.assertGreater(result["best_vertical_agreement"], 0.95)
        self.assertGreater(result["vertical_agreement_gain"], 0.5)

    def test_identical_frame_prefers_zero_shift(self):
        width = 16
        payload = frame(width, 4, lambda x, y: (x + y * 17) & 0xFF)
        result = module.best_horizontal_shift(
            payload,
            payload,
            width=width,
            max_shift=4,
            sample_step=1,
        )
        self.assertEqual(result["best_shift_pixels"], 0)
        self.assertEqual(result["best_agreement"], 1.0)
        self.assertEqual(result["agreement_gain"], 0.0)

    def test_change_metrics_bound_exact_pixel_delta(self):
        width = 8
        before = bytearray(frame(width, 3, lambda x, y: 1))
        after = bytearray(before)
        pos = (2 * width + 5) * 4
        after[pos:pos + 4] = bytes((9, 8, 7, 6))
        result = module.changed_metrics(bytes(before), bytes(after), width=width)
        self.assertEqual(result["changed_pixels"], 1)
        self.assertEqual(result["bbox_inclusive"], [5, 2, 5, 2])

    def test_sequence_summary_uses_gain_not_nonzero_shift_alone(self):
        width = 24
        height = 8
        first = frame(width, height, lambda x, y: (x * 11 + y * 13) & 0xFF)
        second = shift_right(first, width, height, 2)
        third = second
        report = module.analyze_sequence(
            [(10, first), (11, second), (12, third)],
            width=width,
            max_shift=4,
            sample_step=1,
        )
        self.assertEqual(report["frame_count"], 3)
        self.assertEqual(report["changed_pair_count"], 1)
        self.assertEqual(report["motion_candidate_pair_count"], 1)
        self.assertEqual(report["dominant_horizontal_shift_pixels"], 2)
        self.assertEqual(report["vertical_motion_candidate_pair_count"], 0)
        self.assertIsNone(report["dominant_vertical_shift_pixels"])

    def test_loader_requires_consecutive_valid_bgrx_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            payload = frame(4, 2, lambda x, y: x + y)
            (root / "title-motion-000.fb.bgrx").write_bytes(payload)
            (root / "title-motion-001.fb.bgrx").write_bytes(payload)
            rows = module.load_sequence(root, width=4)
            self.assertEqual([index for index, _ in rows], [0, 1])

            (root / "title-motion-003.fb.bgrx").write_bytes(payload)
            with self.assertRaisesRegex(ValueError, "not consecutive"):
                module.load_sequence(root, width=4)


if __name__ == "__main__":
    unittest.main()
