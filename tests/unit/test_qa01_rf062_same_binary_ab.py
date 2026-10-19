"""ROM-free adversarial on/off original/native helper observation tests."""
from __future__ import annotations
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf062_same_binary_ab as x


def fixtures():
    common={k:str(k) for k in x.IMMUTABLE}
    common.update({
        "zoo_race_mesh":{"strict":True},
        "source_terminal_followthrough":{"guest":"original/native"},
        "zoo_next_bowl_handoff":{"offset":267},
    })
    original=b"QA01REFORIGINAL original=1\n"
    helpers=[]
    for i in range(12):
        helpers.append("QA01RF054NATIVEBUS kind=read8 seq=%s frame=6124 master=%s "
                       "addr=11%04X A=630D Y=%04X D=0000 dp63=00 dp64=00 dp65=11 "
                       "scope=Snd_UploadBlockList_82EF_M1X0" %
                       (i+1,1000+i*540,0xC770+i,0xC770+i))
    direct=[]
    for i in range(10):
        direct.append("QA01RF062NATIVE seq=%s f=6124 executedPC=8282F0 master=%s "
                      "addr=11%04X value=%s A=630D Y=%04X D=0000" %
                      (i+1,1000+i*540,0xC770+i,
                       "D0" if i==4 else "00",0xC770+i))
    off={"original":original,"native":("\n".join(helpers)+"\n").encode()}
    on={"original":original,
        "native":("\n".join(helpers+direct)+"\n").encode()}
    inp={"original":b"controller frames 1..3","native":b"native frames 1..3"}
    return copy.deepcopy(common), copy.deepcopy(common), off,on,inp,dict(inp)


class SameBinaryNativeProbeAB(unittest.TestCase):
    def test_real_same_binary_fixture_but_no_wrapper_parity_claim(self):
        result=x.control(*fixtures())
        self.assertTrue(result["runtime_RF062_logging_noninterference_supported"])
        self.assertEqual(result["native_real_sound_helper_count_off_on"],[12,12])
        self.assertEqual(result["rf062_actual_native_read_count_off_on"],[0,10])
        self.assertFalse(result["wrapper_replacement_noninterference_proven"])
        self.assertEqual(result["USA_events_accepted"],0)

    def test_actual_controller_bytes_cannot_change(self):
        a,b,c,d,e,f=fixtures()
        f["native"] += b"extra"
        with self.assertRaisesRegex(ValueError,"controller input changed"):
            x.control(a,b,c,d,e,f)

    def test_source_rom_movie_and_binary_must_be_equal(self):
        for field in x.IMMUTABLE:
            a,b,c,d,e,f=fixtures()
            b[field]="revised"
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"identity"):
                x.control(a,b,c,d,e,f)

    def test_missing_native_sound_observation_must_fail(self):
        a,b,c,d,e,f=fixtures()
        d["native"]=d["native"].replace(b"QA01RF062NATIVE seq=5",b"QA01RF062_WRONG seq=5")
        with self.assertRaisesRegex(ValueError,"on/off observation"):
            x.control(a,b,c,d,e,f)

    def test_same_byte_wrong_native_master_rejected(self):
        a,b,c,d,e,f=fixtures()
        d["native"]=d["native"].replace(b"master=3160 addr=11C774",
                                        b"master=3161 addr=11C774")
        # The separate same-byte direct record is not treated as parity
        # because the helper's master value was preserved separately.
        result=x.control(a,b,c,d,e,f)
        self.assertTrue(result["native_actual_RF054_CPU_master_clocks_equal"])
        # on/off shim events alone are not a full CPU timing oracle.
        self.assertEqual(result["USA_events_accepted"],0)

    def test_actual_helper_missing_at_frame_edge_is_reported_not_hidden(self):
        a,b,c,d,e,f=fixtures()
        d["native"]=d["native"].replace(b"QA01RF054NATIVEBUS kind=read8 seq=12",b"QA01RF054_OTHER kind=read8 seq=12")
        result=x.control(a,b,c,d,e,f)
        self.assertEqual(result["native_real_sound_helper_count_off_on"],[12,11])
        self.assertFalse(result["runtime_RF062_logging_noninterference_supported"])
        self.assertTrue(result["native_sound_helper_edit_blocks"])

    def test_changed_native_helper_clock_reports_hard_noninterference_negative(self):
        a,b,c,d,e,f=fixtures()
        d["native"]=d["native"].replace(b"master=3700 addr=11C775",
                                        b"master=3701 addr=11C775")
        result=x.control(a,b,c,d,e,f)
        self.assertTrue(result["native_actual_RF054_address_and_register_rows_equal"])
        self.assertFalse(result["native_actual_RF054_CPU_master_clocks_equal"])
        self.assertFalse(result["runtime_RF062_logging_noninterference_supported"])

    def test_guest_progression_difference_never_waived(self):
        a,b,c,d,e,f=fixtures()
        b["zoo_next_bowl_handoff"]={"offset":268}
        result=x.control(a,b,c,d,e,f)
        self.assertFalse(result["original_native_whole_mesh_and_followthrough_equal"])
        self.assertFalse(result["runtime_RF062_logging_noninterference_supported"])

    def test_overflow_trace_rejected(self):
        a,b,c,d,e,f=fixtures()
        d["native"]+=b"QA01RF062NATIVE_TRUNCATED\n"
        with self.assertRaisesRegex(ValueError,"overflow"):
            x.control(a,b,c,d,e,f)


if __name__ == "__main__":
    unittest.main()
