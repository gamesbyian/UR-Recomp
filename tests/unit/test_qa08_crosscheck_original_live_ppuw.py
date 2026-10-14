"""Independent original PPU write journal and live after-write source crosschecks."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools import qa08_crosscheck_original_live_ppuw as subject


def fixture(root):
    frames=(1988,1989,1990,2231,2232,2233,2471,2472)
    readings=[]
    for f in frames:
        for i in range(12):
            readings.append({
                "ordinal":len(readings),"original_emulator_frame":f,
                "original_beam_v":subject.EXPECTED_V[i//2],
                "original_live_PPU_register":"$2131" if i%2==0 else "$2132",
                "source":subject.EXPECTED_SRCS[i],
                "observed_original_HDMA_PPU_written_byte":"0x"+subject.EXPECTED_BYTES[i],
                "original_Wram_equals_BBus_value":True,
                "observed_byte_matches_prior_executed_original_table":True,
                "original_live_PPU_fixed_RGB15_after_write":"0x0260"
            })
    live={"schema":subject.SCHEMA,
          "actual_original_PPU_2131_2132_writes":96,
          "actual_original_channel5_register_pairs":48,
          "source_expected_byte_matches":96,
          "actual_WRAM_PPU_byte_matches":96,
          "real_original_native_identical_frame_input_PPU_parity":False,
          "actual_original_Snes9x_finished_PPU_RGB_pixels_sampled":False,
          "source_event_records":readings}
    lp=root/"live.json"
    lp.write_text(json.dumps(live))
    for tag, f in (("go",1989),("t480",2473)):
        info={"tag":tag,"frame":f,"fb_frame":f,"fb_width":256,"fb_height":224,
              "fb_dump_format":"BGRX8888","ppuw_entries":12,
              "ppuw_truncated":False,"no_colormath":False,"no_clip":False,
              "layer_mask":"1F","snesref_dbg_version":1}
        (root/f"{tag}.info.json").write_text(json.dumps(info))
        (root/f"{tag}.fb.bgrx").write_bytes(b"\x00\x01\x02\x00"*(256*224))
        lines=["#frame\tvcounter\thcounter\taddr\tvalue\tsource"]
        for i in range(12):
            lines.append(f"{f}\t{subject.EXPECTED_V[i//2]}\t{200+(i%2)*2}\t"
                         f"{0x2131+(i%2):04X}\t{subject.EXPECTED_BYTES[i]}\thdma")
        (root/f"{tag}.ppuw.tsv").write_text("\n".join(lines)+"\n")
    return lp

class OriginalLiveVsWriteJournalTests(unittest.TestCase):
    def test_two_source_observers_agree_in_real_original_frame_1989(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);lp=fixture(root)
            result=subject.check(root,lp)
            self.assertEqual(result["original_GO_PPU_register_records_crosschecked"],12)
            self.assertEqual(result["actual_original_channel5_HDMA_mode1_pairs_crosschecked"],6)
            self.assertEqual(result["per_original_GO_PPU_write"][1]["original_h"],202)
            self.assertFalse(result["original_Snes9x_frame_to_native_guest_frame_aligned"])

    def test_exact_input_sha_pins_fail_when_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);lp=fixture(root);accepted=subject.check(root,lp)
            pins={
                "live_ppu":accepted["original_live_source_report_SHA256"],
                "go_ppuw":accepted["original_ppuw_SHA256"],
                "go_rgb":accepted["original_GO_frame_RGB_B_G_R_X_SHA256"],
                "t480_rgb":accepted["original_t480_frame_RGB_B_G_R_X_SHA256"]}
            self.assertEqual(subject.check(root,lp,pins)["original_GO_PPU_register_records_crosschecked"],12)
            pins["go_rgb"]="0"*64
            with self.assertRaisesRegex(ValueError,"sha changed"):
                subject.check(root,lp,pins)

    def test_wrong_source_byte_register_beam_and_counterfeit_live_report_fail(self):
        for change in ("byte","register","h","v","source","live_byte","live_addr",
                       "live_frame","live_promote","missing","duplicate"):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);lp=fixture(root)
                journal=root/"go.ppuw.tsv"
                lines=journal.read_text().splitlines()
                data=json.loads(lp.read_text())
                e=data["source_event_records"][12]
                if change=="byte":lines[1]=lines[1].replace("\t04\thdma","\t05\thdma")
                if change=="register":lines[1]=lines[1].replace("\t2131\t","\t2130\t")
                if change=="h":lines[2]=lines[2].replace("\t202\t","\t199\t")
                if change=="v":lines[1]=lines[1].replace("\t0\t","\t1\t")
                if change=="source":lines[1]=lines[1].replace("hdma","cpu")
                if change=="live_byte":e["observed_original_HDMA_PPU_written_byte"]="0x05"
                if change=="live_addr":e["source"]="7E:2084"
                if change=="live_frame":e["original_beam_v"]=7
                if change=="live_promote":data["real_original_native_identical_frame_input_PPU_parity"]=True
                if change=="missing":data["source_event_records"].pop(12)
                if change=="duplicate":lp.write_text('{"schema":"a","schema":"b"}')
                else:lp.write_text(json.dumps(data))
                journal.write_text("\n".join(lines)+"\n")
                with self.assertRaises(ValueError):
                    subject.check(root,lp)


if __name__=="__main__":
    unittest.main()
