"""Fail-closed source/native executed 2P writer chronology classification."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_dual_air_executed_chronology as m


def fixture():
    frames = []
    for frame in m.FRAMES:
        o = dict(p1_raw_air=0, p2_raw_air=0, p1_y=857,
                 p2_y=859, p1_y_velocity=0, p2_y_velocity=0)
        n = o.copy()
        if frame == 2579:
            o.update(p2_raw_air=1, p2_y=860, p2_y_velocity=19)
            n = o.copy()
        if frame == 2580:
            o.update(p2_raw_air=2, p2_y=863, p2_y_velocity=38)
            n = o.copy()
            n.update(p1_raw_air=1, p1_y=858, p1_y_velocity=19, p2_y=862)
        if frame in (2581, 2582):
            o.update(p2_y=864)
            n = o.copy()
            n["p1_y"] = 858
        if frame in (2583, 2584):
            o.update(p2_y=864)
            n = o.copy()
        frames.append({
            "absolute_host_frame": frame,
            "original": o, "native": n,
            "same_host_named_raw_bytes_equal": o == n,
            "p1_y_native_minus_original": n["p1_y"] - o["p1_y"],
            "p2_y_native_minus_original": n["p2_y"] - o["p2_y"],
        })
    source = [
        dict(frame=2579, pc=pc, address="7E:" + addr,
             old=old, new=new, vcounter=v, static_candidate_pc=pc in
             ("81:8E26", "81:8F7A"))
        for pc,addr,old,new,v in (
            ("81:8E26","0545","00","00",80),
            ("81:8F7A","0547","01","02",104),
            ("81:8E3C","0415","5B","59",80),
            ("81:8E48","04BB","13","00",81),
            ("82:928F","0417","5C","5F",34),
        )
    ]
    source.append(dict(frame=2580, pc="81:8E26", address="7E:0545",
                       old="00", new="00", vcounter=78,
                       static_candidate_pc=True))
    source.extend([dict(frame=2577, pc="82:8DA1", address="7E:0415",
                        old="59", new="5B", vcounter=2,
                        static_candidate_pc=False)] * (126 - len(source)))
    native = [
        dict(pre_run_host=2579, source_scope="bank_81_8D18_M0X0",
             address=addr, value=value, width=2, bank="00")
        for addr,value in (
            ("0545","0001"),("0547","0002"),("0415","035A"),
            ("04BB","0013"),("0417","035E"),
        )
    ]
    native.append(dict(pre_run_host=2580, source_scope="bank_81_8D18_M0X0",
                       address="0545", value="0000", width=2, bank="00"))
    native.extend([dict(pre_run_host=2577, source_scope="bank_81_8D18_M0X0",
                        address="0419", value="0000", width=2, bank="00")]
                  * (813 - len(native)))
    words = []
    for row in frames:
        words.append({
            side: {
                "p1_candidate_state_word": row[side]["p1_raw_air"],
                "p2_candidate_state_word": row[side]["p2_raw_air"],
            } for side in ("original", "native")
        })
    scratch = [
        dict(frame=frame, pc=pc, address="7E:0F29", old=old, new=new,
             vcounter=v, changed=True)
        for frame, pc, old, new, v in (
            (2579, "81:8DB1", "01", "00", 56),
            (2579, "81:8F0B", "00", "01", 82),
            (2579, "81:9268", "01", "02", 103),
            (2580, "81:966D", "02", "00", 103),
        )
    ]
    scratch.extend([dict(frame=2577, pc="82:A9A3",
                         address="7E:0FA1", old="00", new="13",
                         vcounter=0, changed=True)] * (205-len(scratch)))
    return {
        "schema": "UR-QA01-DUAL-AIR-SOURCE-NATIVE-OPCODE-WRITER/1",
        "source_run": 38509912672, "complete_event_release_credit": 0,
        "strict_complete_event_accepted": False,
        "actual_cpu_instruction_and_ppu_phase_aligned": False,
        "dense_original_native_same_host": frames,
        "original_cpu_opcode_changes": source,
        "original_cpu_shared_working_scopes": scratch,
        "original_cpu_neighbor_high_byte_scopes": [],
        "native_cpu_helper_writes": native,
        "original_cpu_source_receipts_qualified": 331,
    }, words


class OriginalNativeExecuted2PAir(unittest.TestCase):
    def test_real_artifact_identity_is_immutable(self):
        self.assertEqual(m.RUN, 38520105599)
        self.assertEqual(m.ARTIFACT_ID, 11873951116)
        self.assertEqual(
            m.ARCHIVE_SHA256,
            "1fa1cf0e4c50e2d1977443310e31acd26f2fcf5941ccb93232d289ca9ce469af")
        self.assertEqual(
            m.CROSSWALK_SHA256,
            "3716fdf4d5612791ad9ef9f6e08d797e0591409aad8abe56e327d02eeec78775")

    def test_synthetic_crosswalk_keeps_original_native_cpu_clock_separate(self):
        data, words = fixture()
        result = m.summarize(data, words)
        self.assertEqual(result["earliest_named_guest_difference_host"], 2580)
        self.assertEqual(result["first_named_reconvergence_host"], 2583)
        self.assertEqual(len(result["dense_same_host"]), 9)
        self.assertEqual(result["provenance"]["original_core_cpu_receipts"], 331)
        self.assertEqual(result["provenance"]["native_helper_write_scopes"], 813)
        self.assertEqual(
            result["original_cpu_frame_2579"]["p1_state"]["new"], "00")
        self.assertEqual(
            result["native_helper_pre_run_host_2579"]["p1_state"]["value"], "0001")
        self.assertEqual(
            result["original_cpu_frame_2579"]["p2_state"]["new"], "02")
        self.assertEqual(
            result["native_helper_pre_run_host_2579"]["p2_state"]["value"], "0002")
        original_scratch = result["original_cpu_collision_scratch_2579"]
        self.assertEqual(
            original_scratch["p1_stage_from_prior_p2"]["new"], "00")
        self.assertEqual(
            original_scratch["p2_actual_collision_state_increment"]["pc"],
            "81:9268")
        self.assertEqual(
            original_scratch["p2_actual_collision_state_increment"]["new"], "02")
        self.assertFalse(result["native_cpu_internal_collision_scratch_observed"])
        self.assertFalse(result["cpu_instruction_or_ppu_beam_phase_aligned"])
        self.assertFalse(result["native_helper_scope_is_opcode_pc"])
        self.assertFalse(result["first_causal_upstream_condition_proven"])
        self.assertEqual(result["strict_complete_usa_events_admitted"], 0)

    def test_any_source_writer_pc_or_native_byte_mutation_rejects(self):
        for field,idx,key,value in (
            ("original_cpu_opcode_changes",0,"new","01"),
            ("original_cpu_opcode_changes",1,"new","03"),
            ("original_cpu_opcode_changes",3,"new","13"),
            ("native_cpu_helper_writes",0,"value","0000"),
            ("native_cpu_helper_writes",1,"value","0001"),
            ("native_cpu_helper_writes",3,"value","0000"),
        ):
            with self.subTest(field=field,idx=idx,key=key):
                a,w = fixture()
                a[field][idx][key] = value
                with self.assertRaises(ValueError):
                    m.summarize(a,w)

    def test_snapshot_contamination_never_becomes_a_zero_credit_pass(self):
        for action in ("phase","award","frame","state","word",
                       "delta","count","scope","collision"):
            with self.subTest(action=action):
                a,w = fixture()
                if action == "phase":
                    a["actual_cpu_instruction_and_ppu_phase_aligned"] = True
                elif action == "award":
                    a["strict_complete_event_accepted"] = True
                elif action == "frame":
                    a["dense_original_native_same_host"][4]["absolute_host_frame"] = 2581
                elif action == "state":
                    a["dense_original_native_same_host"][4]["native"]["p1_y"] = 857
                elif action == "word":
                    w[4]["native"]["p1_candidate_state_word"] = 0
                elif action == "delta":
                    a["dense_original_native_same_host"][4]["p1_y_native_minus_original"] = 0
                elif action == "count":
                    a["original_cpu_source_receipts_qualified"] = 330
                elif action == "collision":
                    a["original_cpu_shared_working_scopes"][2]["new"] = "03"
                else:
                    a["original_cpu_opcode_changes"][0]["pc"] = "81:8E27"
                with self.assertRaises(ValueError):
                    m.summarize(a,w)

    def test_forged_zip_is_not_an_executed_original_cpu_replay(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "forged.zip"
            p.write_bytes(b"not the independently executed original CPU trace")
            with self.assertRaisesRegex(ValueError, "ZIP SHA-256"):
                m.report_zip(p)


    def test_archived_two_seat_local_update_has_three_common_upstream_calls(self):
        # The original opcode logger saw the final *writer*, not necessarily
        # which of three shared callees produced the divergent state.
        bank = (ROOT / "reference/imported/reverse-engineering/nitrodon/"
                "bank 81.txt").read_text(encoding="utf-8")
        selectors = (
            ("81/8DD0: A0 00 00     LDY #$0000",
             "81/8DD3: 8C EF 0F     STY $0FEF",
             "81/8DD6: 20 2A 9E     JSR $9E2A",
             "81/8DD9: 20 95 8B     JSR $8B95",
             "81/8DDC: 20 B8 8F     JSR $8FB8",
             "81/8E23: AD 29 0F     LDA $0F29",
             "81/8E26: 8D 45 05     STA $0545"),
            ("81/8F24: A0 02 00     LDY #$0002",
             "81/8F27: 8C EF 0F     STY $0FEF",
             "81/8F2A: 20 2A 9E     JSR $9E2A",
             "81/8F2D: 20 95 8B     JSR $8B95",
             "81/8F30: 20 B8 8F     JSR $8FB8",
             "81/8F77: AD 29 0F     LDA $0F29",
             "81/8F7A: 8D 47 05     STA $0547"),
        )
        for path in selectors:
            with self.subTest(path=path[0]):
                indices = [bank.index(x) for x in path]
                self.assertEqual(indices, sorted(indices))
        self.assertIn("81/8DAE: AD 45 05     LDA $0545", bank)
        self.assertIn("81/8DB1: 8D 29 0F     STA $0F29", bank)
        self.assertIn("81/8F08: AD 47 05     LDA $0547", bank)
        self.assertIn("81/8F0B: 8D 29 0F     STA $0F29", bank)
        gate = (
            "81/9255: AD C0 02     LDA $02C0",
            "81/9258: C2 20        REP #$20",
            "81/925A: 10 12        BPL $926E",
            "81/925F: AD 29 0F     LDA $0F29",
            "81/9262: 1A           INC",
            "81/9263: C9 0A 00     CMP #$000A",
            "81/9266: 10 03        BPL $926B",
            "81/9268: 8D 29 0F     STA $0F29",
        )
        points = [bank.index(line) for line in gate]
        self.assertEqual(points, sorted(points))



if __name__ == "__main__":
    unittest.main()
