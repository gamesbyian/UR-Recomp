from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from mesen_mcp.session import _bridge_stage_summary, _bridge_startup_timeout, _extract_rom_from_zip, _launcher_log_tail


class BridgeStartupDiagnosticsTests(unittest.TestCase):
    def test_surfaces_log_tail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mesen.stderr.log").write_text("prefix-" + "x" * 20)
            diagnostics = _session_log_diagnostics(root, tail_chars=8)
            self.assertIn("mesen.stderr.log tail:", diagnostics)
            self.assertTrue(diagnostics.endswith("xxxxxxxx"))


class BridgeStartupTimeoutTests(unittest.TestCase):
    def test_respects_short_session_timeout(self) -> None:
        self.assertEqual(_bridge_startup_timeout(8), 8.0)

    def test_caps_long_session_timeout(self) -> None:
        self.assertEqual(_bridge_startup_timeout(300), 60.0)


class BridgeStageSummaryTests(unittest.TestCase):
    def test_reports_reached_stages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ready = Path(tmp) / "bridge.ready"
            Path(str(ready) + ".lua").write_text("ok\n", encoding="utf-8")
            Path(str(ready) + ".socket").write_text("ok\n", encoding="utf-8")
            self.assertEqual(_bridge_stage_summary(ready), "lua,socket")

    def test_reports_no_stages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_bridge_stage_summary(Path(tmp) / "bridge.ready"), "none")


class LauncherLogTailTests(unittest.TestCase):
    def test_collects_launcher_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mesen.stdout.log").write_text("stdout marker", encoding="utf-8")
            (root / "mesen.stderr.log").write_text("stderr marker", encoding="utf-8")
            tail = _launcher_log_tail(root)
            self.assertIn("stdout marker", tail)
            self.assertIn("stderr marker", tail)


class ZipRomTests(unittest.TestCase):
    def test_extracts_single_supported_rom_member(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "game.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("docs/readme.txt", "not a rom")
                zf.writestr("nested/Game.sfc", b"rom bytes")

            extracted = _extract_rom_from_zip(archive, root / "session")

            self.assertEqual(extracted.name, "Game.sfc")
            self.assertEqual(extracted.read_bytes(), b"rom bytes")
            self.assertEqual(extracted.parent, root / "session")

    def test_rejects_zip_without_supported_rom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "game.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("readme.txt", "not a rom")

            with self.assertRaisesRegex(ValueError, "no supported ROM"):
                _extract_rom_from_zip(archive, root / "session")

    def test_rejects_ambiguous_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "game.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("one.sfc", b"one")
                zf.writestr("two.sfc", b"two")

            with self.assertRaisesRegex(ValueError, "multiple supported ROM"):
                _extract_rom_from_zip(archive, root / "session")
