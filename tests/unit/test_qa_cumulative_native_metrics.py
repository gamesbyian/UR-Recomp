"""Contracts for frame/resource research. Mocks are NOT native gameplay witnesses."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa_cumulative_native_metrics as n
from controller_input import load_controller_runs

SHA="a"*40


class NativeFrameAndResourceResearchContracts(unittest.TestCase):
    def test_seeded_input_and_long_native_one_process_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for mode in n.MODES:
                with self.subTest(mode=mode):
                    path=root/mode
                    path.mkdir()
                    controls,script,diversity=n.extended_case(10000000,mode,path)
                    original=n.native.CONTROL_FILE.read_text()
                    self.assertTrue(controls.read_text().startswith(original.rstrip()))
                    self.assertTrue(load_controller_runs(controls))
                    self.assertGreater(diversity["p1_frames"],60)
                    self.assertGreater(diversity["p2_frames"],60)
                    self.assertIn("dump two-player-both-post-1620",script.read_text())
                    self.assertIn("dump endurance-3420",script.read_text())
                    self.assertTrue(script.read_text().endswith("quit\n"))
                    if mode=="performance":
                        for i in range(n.PERF_SAMPLES):
                            self.assertIn(f"dump perf-long-{i:02d}",script.read_text())
                    else:
                        self.assertNotIn("perf-long",script.read_text())

    def test_seed_variation_changes_both_player_input_and_preserves_source_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            identities=set()
            for seed in (10000000,10000001,10010000,10100000):
                case=root/str(seed)
                case.mkdir()
                stream,_,_=n.extended_case(seed,"graphics",case)
                identities.add(n.sha(stream))
            self.assertEqual(len(identities),4)

    def test_same_seed_visual_drift_fails_without_weakening_pixel_equality(self):
        def render(exe,rom,input_file,script,root,mode,timeout):
            root.mkdir()
            (root/"frames").mkdir()
            (root/"dumps").mkdir()
            name="frame_001620.bmp"
            (root/"frames"/name).write_bytes(b"AAA" if root.name=="first" else b"BBB")
            (root/"dumps"/"checkpoint.wram.bin").write_bytes(b"identical")
            return dict(duration_seconds=4,peak_rss_kib=1234,
                        rss_first_kib=1100,rss_last_kib=1234,
                        peak_open_fds=12,observed_resource_samples=5,
                        checkpoint_sha256={"fake":"a"*64},
                        frames=str(root/"frames"),dumps=str(root/"dumps"))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with mock.patch.object(n,"run_native",side_effect=render):
                with self.assertRaisesRegex(ValueError,"frame/WRAM replay differs"):
                    n.trial(Path("exe"),Path("rom"),root/"bad",
                            "graphics",10000000,200)

    def test_synthetic_equal_frames_only_proves_replay_not_original_parity(self):
        def render(exe,rom,input_file,script,root,mode,timeout):
            root.mkdir()
            (root/"frames").mkdir()
            (root/"dumps").mkdir()
            for i in range(1620,2000):
                (root/"frames"/f"frame_{i:06d}.bmp").write_bytes(bytes([i%251]))
            (root/"dumps"/"checkpoint.wram.bin").write_bytes(b"identical")
            return dict(duration_seconds=4,peak_rss_kib=1234,
                        rss_first_kib=1100,rss_last_kib=1234,
                        peak_open_fds=12,observed_resource_samples=5,
                        checkpoint_sha256={"fake":"a"*64},
                        frames=str(root/"frames"),dumps=str(root/"dumps"))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with mock.patch.object(n,"run_native",side_effect=render):
                row=n.trial(Path("exe"),Path("rom"),root/"good",
                            "graphics",10000000,200)
            self.assertEqual(row["real_native_processes"],2)
            self.assertGreaterEqual(row["measured_frame_checks"],300)
            self.assertTrue(row["replay_bit_identical"])

    def test_failure_never_claims_forged_native_gameplay_or_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            exe=root/"native"
            rom=root/"rom"
            exe.write_bytes(b"executable")
            rom.write_bytes(b"stock test placeholder")
            with mock.patch.object(n,"sha",side_effect=lambda p: n.native.ROM_SHA if p==rom else "b"*64),\
                 mock.patch.object(n,"trial",side_effect=RuntimeError("real memory leak")):
                result=n.campaign(exe=exe,rom=rom,source_sha=SHA,mode="performance",
                                  minutes=15,seed=10000000,root=root/"trial",max_cases=2)
            self.assertEqual(result["disposition"],"invariant_violation")
            self.assertEqual(result["completed_processes"],0)
            self.assertEqual(result["unique_seeded_frame_sweeps"],0)
            self.assertFalse(result["original_native_event_parity"])
            self.assertFalse(result["windows_build_tested"])
            self.assertEqual(result["release_gate_credit"],0)

    def test_bounds_and_real_source_oracle_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for mode in ("bogus","graphics"):
                with self.subTest(mode=mode),self.assertRaises(ValueError):
                    n.campaign(exe=root/"absent",rom=root/"absent",
                               source_sha=SHA,mode=mode,
                               minutes=300,seed=10000000,
                               root=root/"trials")
        workflow=(ROOT/".github/workflows/qa-cumulative-native-metrics.yml").read_text()
        self.assertIn("modern-shared-native-acceptance.yml",workflow)
        self.assertIn("timeout-minutes: 145",workflow)
        self.assertIn("mode: graphics", (ROOT/".github/workflows/qa-cumulative-research.yml").read_text())
        self.assertIn("mode: performance", (ROOT/".github/workflows/qa-cumulative-research.yml").read_text())
        self.assertIn("persist-credentials: false",workflow)
        self.assertNotIn("pull_request:",workflow)
        self.assertNotIn("schedule:",workflow)
        self.assertIn("SNESRECOMP_FRAMEDUMP_PIXELS", (ROOT/"tools/qa_cumulative_native_metrics.py").read_text())


if __name__=="__main__":
    unittest.main()
