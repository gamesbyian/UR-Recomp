"""Synthetic controls only; genuine archived guest proof comes from Actions."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa01_dragster_cold_record as target
import qa01_dragster_zoo_handoff as next_zoo
import qa01_cold_result_record as shared


class DragsterColdGuestTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.replay=self.root/"replay"
        self.image=bytearray(8192)
        self.image[0x0422:0x0424]=(2508).to_bytes(2,"little")
        self.image[0x054e:0x0550]=(2508).to_bytes(2,"little")
        self.rows=[]
        for offset in next_zoo.OFFSETS:
            item={"offset_from_respective_dragster_result":offset,"fresh_guests":{}}
            for side,sub in (("original","ref"),("native","native")):
                (self.replay/sub).mkdir(exist_ok=True,parents=True)
                (self.replay/sub/f"dragster-next-zoo-{offset:03d}.sram.bin").write_bytes(self.image)
                item["fresh_guests"][side]={
                    "track":1,"tour_row":0,"in_race":1,
                    "full_sram_bytes":8192,
                    "full_sram_sha256":shared.digest(self.image),
                    "ranked_records_checksum_valid":True,
                    "dragster_record_three_ranks":[{
                        "rank":0,"value_word":2508,"holder_index":0}]
                }
            self.rows.append(item)
        self.report={
            "schema_version":1,"name":"dragster","course_id":"course:01",
            "family":"race-a","native_backend":"pinned-baldosa",
            "admission":"investigative candidate; not a release-ledger pass",
            "rom_sha256":shared.ROM_SHA,
            "original_movie_sha256":shared.MOVIE_SHA,
            "original_movie_window_sha256":target.MOVIE_WINDOW_SHA,
            "input_sha256":target.source_script_sha(),
            "reference_script_sha256":target.source_script_sha(),
            "source_sram_sha256":"1"*64,
            "reference_core_sha256":"2"*64,
            "native_executable_sha256":"3"*64,
            "original_source_event":{
                "original_entry_frame":794,
                "original_result_frame":2874,
                "source_active_frames_to_result":2080,
            },
            "comparison":{
                "terminal_result_guest_frame":{
                    "reference_relative":2081,"native_relative":2079},
                "first_sample_disagreement":None,
                "both_reached_terminal_menu":True,
                "rendered_result_and_score_text_matched":True,
                "timed_race_or_circuit_result_visible":True,
                "original_source_entry_equivalent":True,
                "fresh_guest_entry_equivalent":True,
                "paired_event_candidate":False,
            },
            "dragster_next_zoo_handoff":{
                "schema":next_zoo.SCHEMA,
                "original_movie_dragster_result_frame":2874,
                "original_movie_zoo_entry_frame":3190,
                "original_movie_zoo_entry_relative_to_dragster_result":316,
                "sample_offsets":list(next_zoo.OFFSETS),
                "source_controller_masks_rephased":False,
                "release_complete_usa_event_credit":0,
                "original_native_ranked_checksum_valid_all_samples":True,
                "fresh_original_loaded_true_zoo_course_while_active":True,
                "fresh_native_loaded_true_zoo_course_while_active":True,
                "samples":self.rows,
            },
        }
        self.work=self.root/"cold"
        for side,sub in (("original","ref"),("native","native")):
            path=self.work/side/sub
            path.mkdir(parents=True)
            for offset in target.BOOT_FRAMES:
                (path/f"cold-{offset:03d}.sram.bin").write_bytes(self.image)

    def test_source_exact_and_ranked_cold_both_real_guest_layouts(self):
        seeds=target.source_seeds(self.report,self.replay)
        result=target.evaluate_cold(seeds,self.work)
        self.assertEqual(result["schema"],target.SCHEMA)
        self.assertEqual(result["source_earned_dragster_rank0_centiseconds"],2508)
        self.assertTrue(result["full_150_ranked_words_holders_checksum_preserved"])
        self.assertTrue(result["two_independent_original_native_new_guest_processes"])
        self.assertEqual(len(result["boot_observations"]),2)
        self.assertFalse(result["actual_windows_host_disk_autosave_power_cut_proven"])
        self.assertFalse(result["complete_original_native_dragster_event_parity_proven"])
        self.assertEqual(result["release_complete_usa_event_credit"],0)

    def test_source_does_not_accept_forged_result_controller_or_wrong_race(self):
        for f in (
            lambda r:r["original_source_event"].update({"original_result_frame":2875}),
            lambda r:r.update({"original_movie_window_sha256":"4"*64}),
            lambda r:r.update({"input_sha256":"4"*64}),
            lambda r:r["comparison"]["terminal_result_guest_frame"].update({"native_relative":2080}),
            lambda r:r["comparison"].update({"paired_event_candidate":True}),
            lambda r:r["dragster_next_zoo_handoff"].update({"source_controller_masks_rephased":True}),
            lambda r:r["dragster_next_zoo_handoff"]["samples"][-1]["fresh_guests"]["native"].update({
                "dragster_record_three_ranks":[{"rank":0,"value_word":2507,"holder_index":0}]}),
        ):
            value=copy.deepcopy(self.report)
            f(value)
            with self.subTest(f=f),self.assertRaises(target.DragsterColdError):
                target.source_seeds(value,self.replay)

    def test_guest_cold_changes_and_source_raw_crc_missing_fail_closed(self):
        seeds=target.source_seeds(self.report,self.replay)
        path=self.work/"native"/"native"/"cold-300.sram.bin"
        changed=bytearray(path.read_bytes());changed[0x0550]=1;path.write_bytes(changed)
        with self.assertRaisesRegex(target.DragsterColdError,"changed"):
            target.evaluate_cold(seeds,self.work)
        path.write_bytes(self.image)
        path=self.replay/"native"/"dragster-next-zoo-336.sram.bin"
        path.write_bytes(bytes(8191))
        with self.assertRaises(shared.ColdProofError):
            target.source_seeds(self.report,self.replay)
        path.write_bytes(self.image)
        path=self.work/"original"/"ref"/"cold-420.sram.bin"
        path.unlink()
        with self.assertRaisesRegex(target.DragsterColdError,"missing real"):
            target.evaluate_cold(seeds,self.work)


if __name__=="__main__":
    unittest.main()
