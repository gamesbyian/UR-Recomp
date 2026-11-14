"""Deterministic and adversarial controls for source-bound RF095 PCM comparison."""
import hashlib
import io
import json
import random
import struct
import sys
import tempfile
import unittest
import warnings
import wave
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf095_pcm_pair_compare as compare

SHA = "a" * 40


def make_artifact(path: Path, *, silence=False, tamper=False, duplicate=False):
    rng = random.Random(351)
    original = [(0, 0)] * 250 + [
        (rng.randint(-12000, 12000), rng.randint(-12000, 12000))
        for _ in range(950)
    ]
    if silence:
        original = [(0, 0)] * len(original)
    native = original[76:1076]
    def pcm(values):
        return b"".join(struct.pack("<hh", *pair) for pair in values)
    with io.BytesIO() as stream:
        with wave.open(stream, "wb") as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(32040)
            wav.writeframes(pcm(original))
        wav_bytes = stream.getvalue()
    original_map = ("frame,samples\n" + "".join(
        f"{f},{(f - 6445) * 100}\n" for f in range(6445, 6458))).encode()
    native_map = ("frame,samples\n" + "".join(
        f"{f},{(f - 6447) * 100}\n" for f in range(6447, 6458))).encode()
    native_bytes = pcm(native)
    receipt = {
        "schema": "ur-qa01-rf095-source-registered-pcm/1",
        "original": {
            "wav_sha256": hashlib.sha256(wav_bytes).hexdigest(),
            "map_sha256": hashlib.sha256(original_map).hexdigest(),
            "first_sample_index": 0,
            "sample_rate": 32040,
            "frame_sample_indices": {
                str(i): (i - 6445) * 100 for i in range(6445, 6453)
            },
        },
        "native": {
            "raw_sha256": hashlib.sha256(native_bytes).hexdigest(),
            "map_sha256": hashlib.sha256(native_map).hexdigest(),
            "frame_sample_indices": {
                str(i): (i - 6447) * 100 for i in range(6447, 6458)
            },
        },
    }
    files = {
        compare.FILES["wav"]: wav_bytes,
        compare.FILES["reference_map"]: original_map,
        compare.FILES["native_pcm"]: native_bytes,
        compare.FILES["native_map"]: native_map,
        compare.FILES["receipt"]: json.dumps(receipt).encode(),
    }
    if tamper:
        files[compare.FILES["native_pcm"]] = native_bytes[:-4] + b"\x00\x00\x00\x00"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as z:
        for key, value in files.items():
            z.writestr(key, value)
        if duplicate:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                z.writestr(compare.FILES["wav"], wav_bytes)


class PCMComparisonTests(unittest.TestCase):
    def test_exact_shift_matches_both_channels_but_cannot_grant_credit(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "actual.zip"
            make_artifact(path)
            result = compare.analyze(path, SHA, max_lag=128)
            self.assertEqual(result["best_original_minus_native_lag_sample_frames"], 76)
            self.assertEqual(result["aligned_pearson_left"], 1.0)
            self.assertEqual(result["aligned_pearson_right"], 1.0)
            self.assertEqual(result["original_extracted_sample_frames"], 1200)
            self.assertEqual(result["native_sample_frames"], 1000)
            self.assertIsNotNone(result["original_first_nonzero"])
            self.assertIsNotNone(result["native_first_nonzero"])
            self.assertFalse(result["waveform_parity_proven"])
            self.assertFalse(result["clock_equivalence_proven"])
            self.assertFalse(result["output_stage_equivalence_proven"])
            self.assertEqual(result["usa_course_credit"], 0)
            self.assertEqual(result["release_gate_credit"], 0)

    def test_modified_pcm_refused_before_correlation(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "tamper.zip"
            make_artifact(path, tamper=True)
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                compare.analyze(path, SHA, max_lag=128)

    def test_silent_trace_cannot_be_called_correlated(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "silent.zip"
            make_artifact(path, silence=True)
            with self.assertRaisesRegex(ValueError, "no informative"):
                compare.analyze(path, SHA, max_lag=128)

    def test_duplicate_zip_member_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ambiguous.zip"
            make_artifact(path, duplicate=True)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                compare.analyze(path, SHA, max_lag=128)

    def test_reject_unbounded_search_and_unpinned_source(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "valid.zip"
            make_artifact(path)
            for sha, lag in ((SHA[:12], 128), (SHA, -1), (SHA, 99999)):
                with self.subTest(sha=sha, lag=lag), self.assertRaises(ValueError):
                    compare.analyze(path, sha, max_lag=lag)

    def test_frame_map_missing_or_incomplete(self):
        for raw in (b"frame,samples\n6445,0\n6446,100\n",
                    b"frame,samples\n6445,0\n6446,99\n6447,98\n",
                    b"frame,samples\n6445,0\n6445,100\n",
                    b"frame,samples\r6445,0\n"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                compare.parse_map(raw, 6445, 6457)


if __name__ == "__main__":
    unittest.main()
