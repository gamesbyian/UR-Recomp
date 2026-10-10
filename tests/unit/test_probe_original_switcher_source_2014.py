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
        self.assertEqual(probe.SOURCE_HORIZONS, (22000, 48000, 96000))
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
            (root/"meta").write_text(json.dumps({"sample_count": 100000}))
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
                    json.dumps({
                        "schema": "UR-QA01-SOURCE-RESULT-PROBE/1",
                        "wanted_course_track": 3,
                        "wanted_result_menu": 0x99,
                        "source_trace_frames": [0, ns.source_horizon - 1],
                        "active_track_frames": 0,
                        "source_event_candidate_entries": [],
                        "stable_original_results": [],
                        "complete_event_qa_credit": 0,
                        "original_source_horizon_host_frame": ns.source_horizon,
                        "original_source_horizon_wram_bytes": 0x20000,
                        "original_source_horizon_observed_from_guest_dump": True
                    }))
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
            self.assertEqual(result["source_event_diagnostic"]["wanted_result_menu"],0x99)
            self.assertEqual(json.loads(args.report.read_text())["release_complete_event_credit"],0)


    def test_without_end_of_scan_guest_attestation_even_exact_absence_is_invalid(self):
        from probe_original_event_complete import CompleteEventError
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("rom", "movie", "meta", "ref", "core"):
                (root/name).write_bytes(b"test")
            (root/"meta").write_text(json.dumps({"sample_count": 100000}))
            args = SimpleNamespace(
                work_dir=root/"work", source_horizon=48000,
                rom=root/"rom", movie=root/"movie", movie_meta=root/"meta",
                snesref=root/"ref", core=root/"core", report=root/"out.json")
            def fake_extract(cmd, **kw):
                work = root/"work"/"source-switcher"
                (work/"movie.input").write_text("dummy")
                (work/"anchored.srm").write_bytes(b"a" * 8192)
                return SimpleNamespace(returncode=0)
            diag = {
                "schema": "UR-QA01-SOURCE-RESULT-PROBE/1",
                "wanted_course_track": 3,
                "wanted_result_menu": 0x99,
                "source_trace_frames": [0, 47999],
                "complete_event_qa_credit": 0,
            }
            def negative_scan(ns, out, sram, movieinput, decoded):
                source = out / "source"
                source.mkdir()
                (source/"source-event-diagnostic.json").write_text(
                    json.dumps(diag))
                raise CompleteEventError(probe.NONQUALIFICATION)
            with mock.patch.object(probe.event, "sha",
                                   return_value=probe.event.entry.USA_ROM_SHA256), \
                 mock.patch.object(probe.movie, "read_movie",
                                   return_value=(b"synthetic", None)), \
                 mock.patch.object(probe.movie, "window", return_value={}), \
                 mock.patch.object(probe.subprocess, "run",
                                   side_effect=fake_extract), \
                 mock.patch.object(probe.rnc, "find_streams",
                                   return_value=list(enumerate([b"x"]*45))), \
                 mock.patch.object(probe, "unpack_method1", return_value=b"ABC"), \
                 mock.patch.object(probe.event, "scan_source", side_effect=negative_scan):
                with self.assertRaisesRegex(ValueError, "invalid or incomplete"):
                    probe.inspect_original(args)
            self.assertFalse(args.report.exists())

    def test_source_core_failure_cannot_be_disguised_as_negative_movie_evidence(self):
        # Only the exact qualifying-source absence is a benign diagnostic.
        # A broken original process must fail CI rather than report a
        # successful negative Switcher result.
        from probe_original_event_complete import CompleteEventError
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("rom", "movie", "meta", "ref", "core"):
                (root/name).write_bytes(b"test")
            (root/"meta").write_text(json.dumps({"sample_count": 100000}))
            args = SimpleNamespace(
                work_dir=root/"work", source_horizon=48000,
                rom=root/"rom", movie=root/"movie", movie_meta=root/"meta",
                snesref=root/"ref", core=root/"core", report=root/"out.json")
            def fake_extract(cmd, **kw):
                work=root/"work"/"source-switcher"
                (work/"movie.input").write_text("dummy")
                (work/"anchored.srm").write_bytes(b"a" * 8192)
                return SimpleNamespace(returncode=0)
            patches = (
                mock.patch.object(probe.event, "sha",
                                  return_value=probe.event.entry.USA_ROM_SHA256),
                mock.patch.object(probe.movie, "read_movie",
                                  return_value=(b"synthetic", None)),
                mock.patch.object(probe.movie, "window", return_value={}),
                mock.patch.object(probe.subprocess, "run",
                                  side_effect=fake_extract),
                mock.patch.object(probe.rnc, "find_streams",
                                  return_value=list(enumerate([b"x"]*45))),
                mock.patch.object(probe, "unpack_method1", return_value=b"ABC"),
            )
            with patches[0], patches[1], patches[2] as window_check, patches[3], patches[4], patches[5]:
                for problem in (
                    "source-original replay failed: source core crashed",
                    "original entry capture failed: missing WRAM",
                    "implausibly short source event",
                ):
                    if args.work_dir.exists():
                        import shutil
                        shutil.rmtree(args.work_dir)
                    with mock.patch.object(probe.event, "scan_source",
                                           side_effect=CompleteEventError(problem)):
                        with self.assertRaisesRegex(CompleteEventError, problem):
                            probe.inspect_original(args)
                    self.assertFalse(args.report.exists())
                # Even the exact absence verdict needs independent trace
                # diagnostics. A crashed source probe cannot fabricate those.
                import shutil
                shutil.rmtree(args.work_dir)
                with mock.patch.object(probe.event, "scan_source",
                                       side_effect=CompleteEventError(probe.NONQUALIFICATION)):
                    with self.assertRaisesRegex(ValueError, "missing original trace diagnostic"):
                        probe.inspect_original(args)
                self.assertFalse(args.report.exists())
                # A 48k original scan must actually validate the entire
                # post-Zoo source input, not merely its first 1810 frames.
                self.assertIn(mock.call(b"synthetic", {"sample_count": 100000},
                                        3190, 24000),
                              window_check.call_args_list)
                self.assertIn(mock.call(b"synthetic", {"sample_count": 100000},
                                        27190, 20810),
                              window_check.call_args_list)


if __name__=="__main__":
    unittest.main()
