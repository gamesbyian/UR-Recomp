"""Fast negative-contract tests; require no ROM, SDL or FFmpeg subprocess."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


stage = load("continuous_stage", ROOT / "tools/showcase/stage_continuous_native_capture.py")
validate = load("continuous_validate", ROOT / "tools/showcase/validate_continuous_native_capture.py")


class StageTests(unittest.TestCase):
    def source(self):
        return ("static void SdlRenderer_EndDraw(void) {\n" + stage.ANCHOR + "}\n"
                "static void SdlRenderer_Reconfigure(void) {}\n")

    def test_unique_anchor_and_idempotence(self):
        result = stage.patch(self.source())
        self.assertIn(stage.MARK, result)
        self.assertEqual(result, stage.patch(result))
        self.assertEqual(result.count("UrContinuousNativeCapture();"), 1)

    def test_drift_or_ambiguous_anchor_fails_closed(self):
        for source in ("different", self.source() + stage.ANCHOR):
            with self.assertRaises(ValueError):
                stage.patch(source)


class ValidationTests(unittest.TestCase):
    def setup_capture(self, directory: Path, count=600):
        directory.mkdir(exist_ok=True)
        master = directory / "test.mkv"
        master.write_bytes(b"lossless-master-fixture")
        frames = directory / "frames.tsv"
        header = "ordinal\tguest_frame\twidth\theight\n"
        rows = "".join(f"{n}\t{2208+n}\t1280\t720\n" for n in range(count))
        frames.write_text(header + rows)
        log = directory / "host.log"
        log.write_text(
            f"UR_NATIVE_VIDEO_END actual={count} expected={count} "
            f"last={2208+count-1} ffmpeg_status=0 status=complete\n"
        )
        control = directory / "disabled.crc"
        recorded = directory / "enabled.crc"
        control.write_bytes(b"guest-crc-fixture")
        recorded.write_bytes(b"guest-crc-fixture")
        return master, frames, log, control, recorded

    def run_validate(self, files, count=600):
        master, frames, log, control, recorded = files
        with patch.object(validate, "probe", return_value={
            "codec_name": "ffv1", "width": 1280, "height": 720,
            "r_frame_rate": "60/1", "nb_read_frames": str(count)}):
            return validate.validate(
                master, frames, log, control, recorded, count,
                master.parent / "result.json", "a" * 64, "b" * 40, "race_2p_split"
            )

    def test_full_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = self.setup_capture(Path(tmp))
            result = self.run_validate(files)
            self.assertEqual(result["consecutive_host_presentations"], 600)
            self.assertEqual(result["guest_frame_end"], 2807)

    def test_reject_discontinuity(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = self.setup_capture(Path(tmp))
            path = files[1]
            text = path.read_text().replace("71\t2279\t", "71\t2280\t")
            path.write_text(text)
            with self.assertRaisesRegex(ValueError, "discontinuity"):
                self.run_validate(files)

    def test_reject_crc_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = self.setup_capture(Path(tmp))
            files[4].write_bytes(b"different")
            with self.assertRaisesRegex(ValueError, "WRAM CRC"):
                self.run_validate(files)

    def test_reject_incomplete_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = self.setup_capture(Path(tmp), 599)
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                self.run_validate(files)

    def test_reject_missing_native_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = self.setup_capture(Path(tmp))
            files[2].write_text("process ended")
            with self.assertRaisesRegex(ValueError, "completion"):
                self.run_validate(files)


if __name__ == "__main__":
    unittest.main()
