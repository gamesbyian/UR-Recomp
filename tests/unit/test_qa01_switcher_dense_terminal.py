"""ROM-free source-bound Switcher full-guest stage and corruption controls."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_switcher_dense_terminal as witness
import probe_original_event_complete as producer


class SwitcherDenseRawTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root=Path(d.name)
        self.replay=self.root/"switcher"/"replay"
        self.replay.mkdir(parents=True)
        self.report={
            "course_id":"course:04","name":"switcher",
            "rom_sha256":witness.SOURCE_ROM_SHA,
            "original_movie_sha256":witness.SOURCE_MOVIE_SHA,
            "native_backend":"pinned-baldosa",
            "original_source_event":{
                "original_entry_frame":12327,"original_result_frame":17030,
                "source_active_frames_to_result":4703},
            "reference_entry":1000,"native_entry":1002,
            "relative_sample_frames":list(witness.OFFSETS),
            "comparison":{
                "both_reached_terminal_menu":True,
                "rendered_result_and_score_text_matched":True,
                "original_source_entry_equivalent":True,
                "fresh_guest_entry_equivalent":True,
                "paired_event_candidate":False,
                "terminal_result_guest_frame":{
                    "reference_relative":4704,"native_relative":4702}},
        }
        self.logs={}
        for side,folder,entry,first in (
            ("original","ref",1000,4664),("native","native",1002,4665)):
            path=self.replay/folder
            path.mkdir()
            lines=[]
            for off in witness.OFFSETS:
                tag=f"scene-{off:05d}"
                w=bytearray(131072)
                stage=first<=off<first+34
                w[0x9F]=0x84 if stage else 0x16
                w[0xCE]=0 if stage else 3
                w[0x313]=1
                (path/f"{tag}.wram.bin").write_bytes(w)
                (path/f"{tag}.sram.bin").write_bytes(bytes(8192))
                lines.append(f"script f={entry+off} dump {tag} ok")
            result=self.report["comparison"]["terminal_result_guest_frame"][
                "reference_relative" if side=="original" else "native_relative"]
            lines.append(f"script f={entry+result} dump result-onset ok")
            self.logs[side]="\n".join(lines)+"\n"
        (self.replay/"reference.log").write_text(self.logs["original"])
        (self.replay/"native.log").write_text(self.logs["native"])
        self.write()

    def write(self):
        (self.root/"switcher-report.json").write_text(json.dumps(self.report))

    def test_real_guest_frame_matching_and_unmasked_full_memory(self):
        r=witness.audit(self.root)
        self.assertEqual(r["same_absolute_guest_host_pair_count"],42)
        self.assertEqual(r["actual_source_original_movie_result"],17030)
        self.assertEqual(r["original_native_stages_observed"]["original"][0]["observed_length"],34)
        self.assertEqual(r["original_native_stages_observed"]["native"][0]["observed_length"],34)
        self.assertEqual(r["original_native_real_result_relative_frames"],
                         {"reference_relative":4704,"native_relative":4702})
        self.assertEqual(r["independent_USA_event_acceptance"],0)
        self.assertFalse(r["source_movie_controls_rephased"])
        self.assertFalse(r["full_original_native_course_parity_proven"])
        self.assertEqual(r["memory_bytes_excluded"],0)

    def test_wrong_source_identity_no_credit_and_no_native_guest(self):
        self.report["original_source_event"]["original_result_frame"]=17031
        self.write()
        with self.assertRaisesRegex(witness.EvidenceError,"route not qualified"):
            witness.audit(self.root)
        self.report["original_source_event"]["original_result_frame"]=17030
        self.report["comparison"]["rendered_result_and_score_text_matched"]=False
        self.write()
        with self.assertRaisesRegex(witness.EvidenceError,"route not qualified"):
            witness.audit(self.root)

    def test_false_executed_frame_missing_image_and_guest_stage_fail(self):
        path=self.replay/"native.log"
        path.write_text(path.read_text().replace(
            "script f=5660 dump scene-04658",
            "script f=5661 dump scene-04658"))
        with self.assertRaisesRegex(witness.EvidenceError,"clock mismatch"):
            witness.audit(self.root)
        path.write_text(self.logs["native"])
        snapshot=self.replay/"ref"/"scene-04658.wram.bin"
        snapshot.write_bytes(bytes(131071))
        with self.assertRaisesRegex(witness.EvidenceError,"whole executed"):
            witness.audit(self.root)
        snapshot.write_bytes(bytes(131072))
        for off in witness.OFFSETS:
            path=self.replay/"native"/f"scene-{off:05d}.wram.bin"
            w=bytearray(path.read_bytes())
            w[0x9F]=0x16
            w[0xCE]=3
            path.write_bytes(w)
        with self.assertRaisesRegex(witness.EvidenceError,"never observed"):
            witness.audit(self.root)

    def test_dense_producer_flag_does_not_retime_or_drop_old_samples(self):
        sparse=producer.sample_frames("switcher",4703)
        dense=producer.sample_frames("switcher",4703,switcher_terminal_dense=True)
        self.assertEqual([f for f in dense if f not in sparse],
                         [f for f in witness.OFFSETS if f not in sparse])
        self.assertTrue(set(sparse).issubset(dense))
        self.assertEqual(dense[-1],4701)
        a=producer.replay_script(4,0x99,sparse,False)
        b=producer.replay_script(4,0x99,dense,False)
        self.assertIn("dump scene-04658",b)
        self.assertIn("dump scene-04701",b)
        self.assertTrue(b.endswith("dump result-stable\nquit\n"))
        self.assertEqual(
            [line for line in a.splitlines() if line.startswith("press ")],
            [line for line in b.splitlines() if line.startswith("press ")])
        with self.assertRaisesRegex(producer.CompleteEventError,"requires"):
            producer.sample_frames("dragster",2080,switcher_terminal_dense=True)


if __name__=="__main__":
    unittest.main()
