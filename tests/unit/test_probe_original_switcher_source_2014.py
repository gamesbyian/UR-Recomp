"""The Switcher source probe cannot turn original-only evidence into release credit."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_original_switcher_source_2014 as probe


class OriginalSwitcherSourceTest(unittest.TestCase):
    def test_horizon_and_rom_identity_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            args = SimpleNamespace(
                work_dir=root/"work",source_horizon=24001,
                rom=root/"rom",movie=root/"movie",movie_meta=root/"meta",
                snesref=root/"ref",core=root/"core",report=root/"out.json")
            with self.assertRaisesRegex(ValueError, "horizon"):
                probe.inspect_original(args)
            args.source_horizon=22000
            with mock.patch.object(probe.event,"sha",return_value="wrong"):
                with self.assertRaisesRegex(ValueError, "canonical"):
                    probe.inspect_original(args)

    def test_source_only_result_always_reports_zero_release_credit(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name in ("rom","movie","meta","ref","core"):
                (root/name).write_bytes(b"test")
            args=SimpleNamespace(
                work_dir=root/"work",source_horizon=22000,
                rom=root/"rom",movie=root/"movie",movie_meta=root/"meta",
                snesref=root/"ref",core=root/"core",report=root/"out.json")
            (root/"meta").write_text("{}")
            from probe_original_event_complete import CompleteEventError
            def fake_extract(cmd, **kw):
                work=root/"work"/"source-switcher"
                (work/"movie.input").write_text("dummy")
                (work/"anchored.srm").write_bytes(b"a"*8192)
                return SimpleNamespace(returncode=0)
            def fake_scan(ns, out, sram, source_input, decoded):
                self.assertEqual(ns.case,"switcher")
                self.assertEqual(ns.source_horizon,22000)
                self.assertEqual(len(decoded),3)
                path=out/"source"
                path.mkdir()
                (path/"source-event-diagnostic.json").write_text(
                    json.dumps({"observed_course":4,"result_menu":0x99}))
                raise CompleteEventError("source movie never demonstrated this course/result pair")
            with mock.patch.object(probe.event,"sha",return_value=probe.event.entry.USA_ROM_SHA256), \
                 mock.patch.object(probe.movie,"read_movie",return_value=(b"synthetic",None)), \
                 mock.patch.object(probe.movie,"window",return_value={}), \
                 mock.patch.object(probe.subprocess,"run",side_effect=fake_extract), \
                 mock.patch.object(probe.rnc,"find_streams",return_value=list(enumerate([b"x"]*45))), \
                 mock.patch.object(probe,"unpack_method1",return_value=b"ABC"), \
                 mock.patch.object(probe.event,"scan_source",side_effect=fake_scan):
                result=probe.inspect_original(args)
            self.assertEqual(result["status"],"source_event_not_qualified_within_bounded_horizon")
            self.assertEqual(result["release_complete_event_credit"],0)
            self.assertEqual(result["source_event_diagnostic"]["result_menu"],0x99)
            self.assertEqual(json.loads(args.report.read_text())["release_complete_event_credit"],0)


if __name__=="__main__":
    unittest.main()
