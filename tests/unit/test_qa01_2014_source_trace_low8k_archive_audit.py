"""Synthetic raw-archive source history tests, with full-memory scope guard."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_2014_source_trace_low8k_archive_audit as target


class OriginalSourceArchiveTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.path=self.root/"source.zip"
        low=bytearray(8192)
        self.rows=[]
        def write(frame,address,value):
            old=low[address]
            self.rows.append({"f":frame,"adr":f"0x{address:05x}",
                              "old":f"0x{old:02x}","val":f"0x{value:02x}"})
            low[address]=value
        events=[
            (794,0x313,1),(795,0x313,0),
            (2874,0x9f,153),(2875,0x9f,0),
            (3190,0xce,1),(3190,0x313,1),(3191,0x313,0),
            (8353,0x9f,188),(8354,0x9f,0),
            (8620,0xce,2),(8620,0x313,1),(8621,0x313,0),
            (11985,0x9f,24),(11986,0x9f,0),
            (12327,0xce,3),(12327,0x313,1),(12328,0x313,0),
            (17030,0x9f,153),(17031,0x9f,0),
            (22940,0xce,0),(22941,0x313,1),(25343,0x313,0),
            (25344,0x9f,153),(25352,0x9f,0),(25731,0x313,1),
        ]
        for event in events:write(*event)
        self.trace=("\n".join(json.dumps(x,separators=(",",":"))
                              for x in self.rows)+"\n").encode()
        snap,_,_=target.reconstruct(self.trace.splitlines())
        self.log=(
            "script f=17030 dump original-switcher-result ok\n"
            "script f=22000 dump prior-horizon ok\n"
            "script f=36000 dump new-horizon ok\n").encode()
        self.report={
            "schema":target.PRODUCER_SCHEMA,
            "usa_rom_sha256":target.ROM_SHA,
            "original_movie_sha256":target.MOVIE_SHA,
            "source_controller_masks_modified":False,
            "USA_accepted_event_credit":0,
            "fresh_original_or_native_event_proven":False,
            "new_horizon":36000,
            "completed_new_unique_source_course_candidates":0,
            "completed_repeat_of_previously_sourced_course":1,
            "source_executed_log_sha256":target.sha(self.log),
            "source_raw_trace_sha256":target.sha(self.trace),
            "source_trace_bytes":len(self.trace),
            "genuine_original_source_sustained_active_runs_after_switcher":[
                {"start":22941,"last_active":25342,"track":0,
                 "separately_observed_terminal_result":{"host_frame":25344}},
                {"start":25731,"last_active":36000,"track":0,
                 "separately_observed_terminal_result":None},
            ],
        }
        self.members={
            "source/source-trace.jsonl":self.trace,
            "source/source.log":self.log,
        }
        for frame,label in target.DUMPS:
            # The historical low 8KiB is exact; changing other WRAM bytes
            # cannot be detected from a trace that records only low 8KiB.
            self.members[f"source/{label}.wram.bin"]=snap[frame]+bytes([frame%251])*122880
        self.write()

    def write(self):
        self.members["source-report.json"]=json.dumps(self.report).encode()
        with ZipFile(self.path,"w",ZIP_DEFLATED) as archive:
            for name,value in self.members.items():
                archive.writestr(name,value)
        return target.sha(self.path.read_bytes())

    def test_exact_source_entry_result_and_three_low_wram_dump_positives(self):
        r=target.audit(self.path,self.write())
        self.assertEqual(r["trace_distinct_low_wram_addresses"],3)
        self.assertEqual(r["real_2014_snes9x_trace_writes_replayed"],25)
        self.assertEqual(r["post_switcher_known_course_repeat"]["real_source_result"],25344)
        self.assertTrue(r["four_prior_original_course_entries_and_results_reproduced"])
        self.assertFalse(r["outside_trace_120k_reconstruction_possible"])
        self.assertFalse(r["historical_second_dragster_full_128k_entry_image_available"])
        self.assertEqual(r["distinct_new_usa_courses_proven"],0)
        self.assertEqual(r["usa_event_accepted_credit"],0)

    def test_wrong_full_dump_low_byte_rejected_but_upper_120k_not_inferred(self):
        name="source/new-horizon.wram.bin"
        raw=bytearray(self.members[name])
        raw[0x313] ^= 1
        self.members[name]=bytes(raw)
        with self.assertRaisesRegex(target.ArchiveError,"raw lower-8KiB disagrees"):
            target.audit(self.path,self.write())
        raw[0x313] ^= 1
        raw[0x5000]=0x91
        self.members[name]=bytes(raw)
        result=target.audit(self.path,self.write())
        self.assertFalse(result["outside_trace_120k_reconstruction_possible"])

    def test_forged_trace_old_byte_and_missing_real_dump_stamp_fail(self):
        rows=json.loads(json.dumps(self.rows))
        rows[1]["old"]="0xff"
        self.trace=("\n".join(json.dumps(x,separators=(",",":"))
                              for x in rows)+"\n").encode()
        self.members["source/source-trace.jsonl"]=self.trace
        self.report["source_raw_trace_sha256"]=target.sha(self.trace)
        self.report["source_trace_bytes"]=len(self.trace)
        with self.assertRaisesRegex(target.ArchiveError,"old-byte"):
            target.audit(self.path,self.write())
        self.members["source/source-trace.jsonl"]=("\n".join(
            json.dumps(x,separators=(",",":")) for x in self.rows)+"\n").encode()
        self.report["source_raw_trace_sha256"]=target.sha(self.members["source/source-trace.jsonl"])
        self.report["source_trace_bytes"]=len(self.members["source/source-trace.jsonl"])
        self.log=self.log.replace(b"script f=22000 dump",b"script f=22001 dump")
        self.members["source/source.log"]=self.log
        self.report["source_executed_log_sha256"]=target.sha(self.log)
        with self.assertRaisesRegex(target.ArchiveError,"host acknowledgment"):
            target.audit(self.path,self.write())

    def test_archive_hash_source_identity_and_no_acceptance_guards(self):
        digest=self.write()
        self.report["completed_new_unique_source_course_candidates"]=1
        self.write()
        with self.assertRaisesRegex(target.ArchiveError,"ZIP SHA256"):
            target.audit(self.path,digest)
        with self.assertRaisesRegex(target.ArchiveError,"falsely promoted"):
            target.audit(self.path,target.sha(self.path.read_bytes()))
        self.report["completed_new_unique_source_course_candidates"]=0
        self.report["source_controller_masks_modified"]=True
        with self.assertRaisesRegex(target.ArchiveError,"falsely promoted"):
            target.audit(self.path,self.write())


if __name__=="__main__":
    unittest.main()
