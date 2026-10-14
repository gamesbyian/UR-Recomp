"""Contracts for native two-seat guest fuzz workload; mock tests earn no game QA."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tools"))
import qa02_native_2p_seeded_endurance as c
from controller_input import load_controller_runs

SHA = "a"*40
IDENTITY = {
    "source_commit": SHA, "native_executable_sha256": "b"*64,
    "rom_sha256": c.ROM_SHA, "stock_input_sha256": "c"*64,
    "stock_script_sha256": "d"*64,
}


class SeededNativeInputContractTests(unittest.TestCase):
    def test_source_qualified_real_2p_setup_is_not_rewritten(self):
        source, script = c.base_source()
        self.assertIn("1580:24:080:040", source)
        self.assertTrue(script.rstrip().endswith("quit"))
        generated = c.render_script(script)
        self.assertIn("dump two-player-both-post-1620", generated)
        self.assertIn("dump endurance-1740", generated)
        self.assertIn("dump endurance-3420", generated)
        runner = (ROOT/"tools/qa02_native_2p_seeded_endurance.py").read_text()
        self.assertIn('(root / "user-data").mkdir()', runner)
        self.assertIn("DisableFrameDelay = 1", runner)
        self.assertIn('"--config", str(config)', runner)
        self.assertEqual(generated.strip().splitlines()[-1], "quit")
        self.assertEqual(generated.count("dump endurance-"), len(c.FRAMES))

    def test_many_plans_change_both_seats_without_overlapping_production_rows(self):
        source, _ = c.base_source()
        fingerprints = set()
        for seed in range(300):
            actions, diversity = c.input_plan(seed)
            self.assertGreater(diversity["p1_intervals"], 20)
            self.assertGreater(diversity["p2_intervals"], 20)
            self.assertEqual(actions[0], (1650, 60, 0x080, 0x040))
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                for label, mode in (("t",None), ("1","p1"), ("2","p2")):
                    file = root/(label+".input")
                    file.write_text(c.render_input(source, actions, mode))
                    self.assertTrue(load_controller_runs(file))
                treatment = (root/"t.input").read_bytes()
                self.assertNotEqual(treatment, (root/"1.input").read_bytes())
                self.assertNotEqual(treatment, (root/"2.input").read_bytes())
                fingerprints.add(c.hashlib.sha256(treatment).hexdigest())
        self.assertEqual(len(fingerprints), 300)

    def test_wram_checkpoint_acceptance_rejects_menu_only_and_shortened_dump(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in (c.BASE_CHECK, *(f"endurance-{n}" for n in c.FRAMES)):
                image = bytearray(131072)
                image[0x0313] = 1
                (root/(name+".wram.bin")).write_bytes(image)
            result = c.observe(root)
            self.assertEqual(len(result), 1+len(c.FRAMES))
            (root/(c.BASE_CHECK+".wram.bin")).write_bytes(bytes(131072))
            with self.assertRaisesRegex(ValueError,"never reached active"):
                c.observe(root)
            (root/(c.BASE_CHECK+".wram.bin")).unlink()
            with self.assertRaisesRegex(ValueError,"missing/incomplete"):
                c.observe(root)

    def test_four_process_oracle_detects_replay_drift_and_seat_noop(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, script = c.base_source()
            valid = {c.BASE_CHECK: "a"*64,
                     **{f"endurance-{n}": "c"*64 for n in c.FRAMES}}
            counter = dict(valid)
            counter[c.FIRST_PROBE] = "d"*64
            def run_ok(*args):
                variant = args[4].name
                return valid if variant in ("treatment","repeat") else counter
            with mock.patch.object(c, "execute", side_effect=run_ok):
                row = c.trial(Path("exe"),Path("rom"),source,c.render_script(script),
                              root/"good",17,30)
                self.assertTrue(row["two_seats_observably_active"])
                self.assertTrue(row["bit_exact_replay"])
                self.assertEqual(row["real_native_processes"],4)
            def replay_drift(*args):
                variant = args[4].name
                if variant == "repeat":
                    return {**valid, c.FIRST_PROBE:"f"*64}
                return valid if variant=="treatment" else counter
            with mock.patch.object(c,"execute",side_effect=replay_drift):
                with self.assertRaisesRegex(ValueError,"different WRAM"):
                    c.trial(Path("exe"),Path("rom"),source,c.render_script(script),
                            root/"drift",18,30)
            def no_seat(*args):
                variant = args[4].name
                return valid if variant in ("treatment","repeat","mute-p2") else counter
            with mock.patch.object(c,"execute",side_effect=no_seat):
                with self.assertRaisesRegex(ValueError,"no guest-WRAM response"):
                    c.trial(Path("exe"),Path("rom"),source,c.render_script(script),
                            root/"seat",19,30)

    def test_optional_native_guest_transcript_preserves_exact_runtime_dump_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            transcript=root/"native-transcript.log"
            fake=type("Completed",(),{"returncode":0,
                  "stdout":"script f=2580 dump endurance-2580 ok\n",
                  "stderr":"source diagnostics\n"})()
            with mock.patch.object(c.subprocess,"run",return_value=fake),mock.patch.object(
                    c,"observe",return_value={"endurance-2580":"f"*64}):
                observed=c.execute(
                    root/"exe",root/"rom",root/"input",root/"script",root/"run",30,
                    runtime_log=transcript)
            self.assertEqual(observed["endurance-2580"],"f"*64)
            self.assertIn("script f=2580 dump endurance-2580 ok",transcript.read_text())
            self.assertIn("source diagnostics",transcript.read_text())
            # The four-process endurance caller passes no runtime_log, so
            # its return shape and ordinary private transcript policy hold.
            self.assertTrue((root/"run"/"user-data").is_dir())

    def _populated(self, root: Path) -> Path:
        collection=root/"receipts"
        collection.mkdir()
        for shard in c.SHARDS:
            seed=20261011+shard*1000003
            receipt = {
                "schema":c.SCHEMA, "identity":dict(IDENTITY), "shard":shard,
                "base_seed":20261011, "minutes_budget":15, "max_unique_cases":3000,
                "attempted_cases":1, "passed_cases":1, "failed_cases":0,
                "failures":[], "elapsed_seconds":71, "stop_reason":"wall_budget",
                "case_results":[{
                    "seed":seed,"input_sha256":format(seed,"064x"),
                    "real_native_processes":4, "bit_exact_replay":True,
                    "two_seats_observably_active":True}],
                "total_real_native_processes":4,
                "disposition":"completed_positive", "release_gate_credit":0,
                "original_native_fidelity_accepted":False,
                "complete_two_player_result_accepted":False,
                "physical_gamepads_tested":False,
            }
            receipt["receipt_sha256"]=c.hash_object(receipt)
            c.save(collection/f"native-2p-endurance-{shard}/result.json",receipt)
        return collection

    def test_two_distinct_candidate_bound_shards_and_no_release_credit(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            path=self._populated(root)
            result=c.aggregate(path,SHA,15,3000,20261011)
            self.assertEqual(result["disposition"],"completed_positive")
            self.assertEqual(result["total_unique_cases"],2)
            self.assertEqual(result["total_real_native_processes"],8)
            self.assertEqual(result["release_gate_credit"],0)

    def test_missing_forged_cross_candidate_and_fake_credit_fail_closed(self):
        for fault in ("missing","extra","receipt","binary","seed","credit",
                      "replay","guest","casecount","different_revision"):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td)
                collection=self._populated(root)
                target=collection/"native-2p-endurance-1/result.json"
                if fault=="missing":
                    target.unlink()
                elif fault=="extra":
                    (collection/"native-2p-endurance-99").mkdir()
                else:
                    row=json.loads(target.read_text())
                    if fault=="receipt": row["receipt_sha256"]="0"*64
                    elif fault=="binary":row["identity"]["native_executable_sha256"]="f"*64
                    elif fault=="seed":row["case_results"][0]["seed"]+=1
                    elif fault=="credit":row["release_gate_credit"]=1
                    elif fault=="replay":row["case_results"][0]["bit_exact_replay"]=False
                    elif fault=="guest":row["case_results"][0]["two_seats_observably_active"]=False
                    elif fault=="casecount":row["passed_cases"]=3
                    elif fault=="different_revision":row["identity"]["source_commit"]="f"*40
                    if fault!="receipt":
                        row["receipt_sha256"]=c.hash_object({
                            k:v for k,v in row.items() if k!="receipt_sha256"})
                    c.save(target,row)
                result=c.aggregate(collection,SHA,15,3000,20261011)
                self.assertEqual(result["disposition"],"incomplete_or_failed")
                self.assertTrue(result["issues"])
                self.assertEqual(result["release_gate_credit"],0)

    def test_manual_only_shared_build_no_unbounded_jobs_or_data_upload(self):
        wf=(ROOT/".github/workflows/qa02-native-2p-seeded-endurance.yml").read_text()
        self.assertIn("workflow_dispatch:",wf)
        self.assertNotIn("\n  pull_request:",wf)
        self.assertNotIn("\n  push:",wf)
        self.assertNotIn("schedule:",wf)
        self.assertIn("cancel-in-progress: false",wf)
        self.assertIn("modern-shared-native-acceptance.yml",wf)
        # The actual compiled Linux candidate links GLIBC_2.38. It ran on the
        # producer's ubuntu-latest, but both 22.04 shards in 38182883707
        # exited before their FIRST guest frame. Keep producer and consumer
        # on the exact same Actions runner generation.
        producer=(ROOT/".github/workflows/modern-shared-native-acceptance.yml").read_text()
        self.assertIn("  build:\n    if:",producer)
        self.assertIn("    runs-on: ubuntu-latest",producer)
        stress=wf.split("  stress:\n",1)[1].split("  aggregate:\n",1)[0]
        self.assertIn("    runs-on: ubuntu-latest",stress)
        self.assertNotIn("    runs-on: ubuntu-22.04",stress)
        self.assertIn('ldd "$EXE" 2>&1',stress)
        self.assertIn('dpkg --compare-versions "$libc_version" ge "2.38"',stress)
        self.assertIn("max-parallel: 2",wf)
        self.assertIn("wall_minutes_per_shard:",wf)
        self.assertIn("timeout-minutes: 145",wf)
        self.assertIn("native-2p-endurance-aggregate",wf)
        self.assertNotIn(chr(92)+chr(36)+"{{",wf)
        self.assertNotIn("private-work/trial",wf)
        self.assertNotIn("cmake --build",wf)


if __name__ == "__main__":
    unittest.main()
