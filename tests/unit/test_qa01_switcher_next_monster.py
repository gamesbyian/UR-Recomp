"""ROM-free guards for source-qualified Switcher Race B -> Monster Circuit B."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_switcher_monster_handoff as witness
import probe_original_event_complete as producer


class NextMonsterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.ref, self.native = base / "ref", base / "native"
        self.ref.mkdir()
        self.native.mkdir()
        self.delta = 330
        self.source_event = {
            "original_entry_frame": 12327, "original_result_frame": 17030,
            "source_active_frames_to_result": 4703}
        self.states = {}
        for f in range(17030+73,17030+350):
            active = f >= 17030+self.delta
            self.states[f] = {
                "menu": 0 if active else 0x16,
                "track": 4 if active else 3,
                "in_race": 1 if active else 0}
        self.proof = witness.source_next_monster(self.states,self.source_event)
        self.logs = []
        for side, directory, entry, relative, active_delta in (
                ("original",self.ref,1079,4704,329),
                ("native",self.native,1081,4702,332)):
            lines=[]
            for offset in self.proof["sample_offsets"]:
                tag=f"switcher-next-monster-{offset:04d}"
                active=offset >= active_delta
                w=bytearray(0x20000)
                w[0x009f]=0 if active else 0x16
                w[0x00ce]=4 if active else 3
                w[0x0313]=1 if active else 0
                (directory/f"{tag}.wram.bin").write_bytes(w)
                (directory/f"{tag}.sram.bin").write_bytes(bytes(8192))
                lines.append(f"script f={entry+relative+offset} dump {tag} ok")
            self.logs.append("\n".join(lines)+"\n")

    def _observe(self, **kwargs):
        return witness.observe_next_monster(
            self.ref,self.native,self.logs[0],self.logs[1],
            self.proof,1079,1081,4704,4702,
            observed_dump_frame=producer.observed_dump_frame,
            audit_wram=producer.audit_qa01_wram_pair,
            monster_payload=bytes(range(16)),
            validate_course_payload=lambda payload,ram:True,
            **kwargs)

    def test_source_must_show_sustained_unique_monster_after_real_switcher_result(self):
        self.assertEqual(self.proof["source_switcher_result_to_monster_entry"],330)
        self.assertEqual(self.proof["source_monster_entry_movie_frame"],17360)
        self.assertEqual(self.proof["sample_offsets"][0],325)
        self.assertEqual(self.proof["sample_offsets"][-1],340)
        with self.assertRaisesRegex(witness.SwitcherMonsterError,"not proven"):
            witness.source_next_monster(self.states,dict(self.source_event,
                                                 original_result_frame=17031))
        states=dict(self.states)
        for i in range(330,350):
            states[17030+i]=dict(self.states[17030+i],in_race=0)
        with self.assertRaisesRegex(witness.SwitcherMonsterError,"missing/ambiguous"):
            witness.source_next_monster(states,self.source_event)

    def test_actual_guest_clocks_source_disagreement_and_zero_credit(self):
        result=self._observe()
        self.assertEqual(result["source_monster_entry_relative_result_offset"],330)
        self.assertEqual(result["original_entry_relative_result_offset"],329)
        self.assertEqual(result["native_entry_relative_result_offset"],332)
        self.assertFalse(result["all_three_entries_same_result_relative_offset"])
        self.assertTrue(result["original_monster_source_course_loaded_on_active_sample"])
        self.assertTrue(result["native_monster_source_course_loaded_on_active_sample"])
        self.assertTrue(result["all_full_8192_sram_pairs_equal"])
        self.assertEqual(result["first_triplet_named_state_mismatch_offset"],329)
        self.assertEqual(result["release_complete_event_credit"],0)
        self.assertFalse(result["source_2014_monster_complete_result_proven"])

    def test_missing_raw_clock_and_full_byte_perturbations_fail_or_report(self):
        tag=f"switcher-next-monster-{self.proof['sample_offsets'][0]:04d}"
        path=self.native/f"{tag}.sram.bin"
        path.write_bytes(bytes(8191))
        with self.assertRaisesRegex(witness.SwitcherMonsterError,"short"):
            self._observe()
        path.write_bytes(bytes(8192))
        path=self.native/f"{tag}.wram.bin"
        w=bytearray(path.read_bytes());w[0x01dd]=42;path.write_bytes(w)
        result=self._observe()
        first=result["samples"][0]
        self.assertFalse(first["unmasked_full_wram"]["byte_exact"])
        self.assertEqual(first["unmasked_full_wram"]["excluded_byte_count"],0)
        self.assertEqual(first["unmasked_full_wram"]["differing_byte_count"],1)
        self.assertEqual(result["release_complete_event_credit"],0)
        good=self.logs[1]
        self.logs[1]=good.replace(
            f"script f={1081+4702+self.proof['sample_offsets'][0]} dump",
            f"script f={1082+4702+self.proof['sample_offsets'][0]} dump")
        with self.assertRaisesRegex(witness.SwitcherMonsterError,"host frame"):
            self._observe()

    def test_bounded_script_keeps_stock_inputs_unmodified(self):
        frames=producer.sample_frames("switcher",4703)
        base=producer.replay_script(4,0x99,frames,False,source_followthrough=True)
        extra=producer.replay_script(
            4,0x99,frames,False,source_followthrough=True,
            switcher_next_monster_offsets=self.proof["sample_offsets"])
        self.assertIn("dump original-follow-72\nwait 253\ndump switcher-next-monster-0325",extra)
        self.assertTrue(extra.endswith("dump switcher-next-monster-0340\nquit\n"))
        self.assertNotIn("poke ",extra)
        self.assertEqual([x for x in base.splitlines() if x.startswith("press ")],
                         [x for x in extra.splitlines() if x.startswith("press ")])
        with self.assertRaisesRegex(producer.CompleteEventError,"requires"):
            producer.replay_script(3,0x18,frames,True,source_followthrough=True,
                                   switcher_next_monster_offsets=self.proof["sample_offsets"])


if __name__=="__main__":
    unittest.main()
