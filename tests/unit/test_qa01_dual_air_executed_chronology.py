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
    return {
        "schema": "UR-QA01-DUAL-AIR-SOURCE-NATIVE-OPCODE-WRITER/1",
        "source_run": 38509912672, "complete_event_release_credit": 0,
        "strict_complete_event_accepted": False,
        "actual_cpu_instruction_and_ppu_phase_aligned": False,
        "dense_original_native_same_host": frames,
        "original_cpu_opcode_changes": source,
        "original_cpu_shared_working_scopes": [{}] * 205,
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
                       "delta","count","scope"):
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


if __name__ == "__main__":
    unittest.main()
