"""Fixed 3-band original 23-edge PPU motion uses no fitted regions."""
import unittest
from tools.art.score_original_mesen24_full_saddle import (
    ARMS,TICKS,aggregate_original_timeline,
)
from tools.art.score_original_mesen24_fixed_pivot_glb import SOURCE_Y_BANDS

def point(x,y):
    a=bytearray(4096)
    a[y*64+x]=1
    return bytes(a)

class TemporalSourceBandsTests(unittest.TestCase):
    def test_true_23_edge_partition_and_false_motion(self):
        zero=bytes(4096)
        upper,middle,lower=point(6,3),point(8,20),point(30,40)
        originals={t:{"alpha":zero} for t in TICKS}
        for t,p in ((1602,upper),(1603,middle),(1604,lower)):
            originals[t]={"alpha":p}
        preds={t:{name:zero for name in ARMS} for t in TICKS}
        for t in TICKS:
            preds[t]["original_source_2d_rotation"]=originals[t]["alpha"]
        preds[1602]["axle_root_saddle_plus15_fixed_tick_24deg"]=upper
        preds[1602]["axle_root_saddle_plus15_rom_phase_15deg"]=lower
        result=aggregate_original_timeline(originals,preds)
        self.assertEqual(len(result["arms"]),len(ARMS))
        full=result["arms"]["original_source_2d_rotation"]
        self.assertEqual(full["source_actual_23_consecutive_edge_change_pooled_iou"],1.)
        b=full["source_actual_23_consecutive_edge_change_fixed_y_bands"]
        self.assertEqual(set(b),{n for n,_,_ in SOURCE_Y_BANDS})
        for name in b:
            self.assertEqual(b[name]["tp_fp_fn"],{"tp":2,"fp":0,"fn":0})
            self.assertEqual(b[name]["source_chronological_edge_count"],23)
            self.assertEqual(b[name]["source_actual_xor_changed_pixel_instances"],2)
        p=result["arms"]["axle_root_saddle_plus15_fixed_tick_24deg"][
            "source_actual_23_consecutive_edge_change_fixed_y_bands"]
        self.assertEqual(p["upper_y0_14"]["tp_fp_fn"],{"tp":2,"fp":0,"fn":0})
        self.assertEqual(p["middle_y15_26"]["tp_fp_fn"],{"tp":0,"fp":0,"fn":2})
        self.assertEqual(p["lower_y27_63"]["tp_fp_fn"],{"tp":0,"fp":0,"fn":2})
        wrong=result["arms"]["axle_root_saddle_plus15_rom_phase_15deg"][
            "source_actual_23_consecutive_edge_change_fixed_y_bands"]
        self.assertEqual(wrong["lower_y27_63"]["tp_fp_fn"],{"tp":0,"fp":2,"fn":2})
        for name,record in result["arms"].items():
            expected=record["source_actual_23_consecutive_edge_change_tp_fp_fn"]
            got={k:sum(q["tp_fp_fn"][k] for q in record[
                "source_actual_23_consecutive_edge_change_fixed_y_bands"].values())
                for k in ("tp","fp","fn")}
            with self.subTest(name=name):
                self.assertEqual(got,expected)
    def test_missing_candidate_and_malformed_original_fail_closed(self):
        originals={t:{"alpha":bytes(4096)} for t in TICKS}
        preds={t:{name:bytes(4096) for name in ARMS} for t in TICKS}
        del preds[1602][ARMS[-1]]
        with self.assertRaisesRegex(ValueError,"complete original"):
            aggregate_original_timeline(originals,preds)
        preds[1602][ARMS[-1]]=bytes(4096)
        originals[1607]={"alpha":bytes([2])+bytes(4095)}
        with self.assertRaisesRegex(ValueError,"malformed"):
            aggregate_original_timeline(originals,preds)

if __name__=="__main__":
    unittest.main()
