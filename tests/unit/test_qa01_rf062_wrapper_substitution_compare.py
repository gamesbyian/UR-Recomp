"""ROM-free adversarial controls for identical-source wrapper-only A/B."""
from __future__ import annotations
import copy,hashlib,json,sys,tempfile,unittest
from unittest import mock
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf062_wrapper_substitution_compare as target

def fixture(root):
    w,c=root/"wrapped",root/"unwrapped"
    for p in (w,c):
        (p/"work/zoom-zoo/replay").mkdir(parents=True)
    bins=root/"binaries"
    bins.mkdir()
    (bins/"native").write_bytes(b"wrapped native code")
    (bins/"native-control").write_bytes(b"unwrapped native code")
    identity={k:k+"_sha" for k in target.IDENTITY}
    mesh={k:{"sampled_whole_Wram_pairs":78,"release_credit":0}
          for k in target.CONTROLS}
    for p,binary in ((w,"native"),(c,"native-control")):
        (p/"producer-report.json").write_text(json.dumps({
            **identity,**mesh,"native_executable_sha256":
            hashlib.sha256((bins/binary).read_bytes()).hexdigest()}))
        path=p/"work/zoom-zoo/replay"
        (path/"ref.input").write_bytes(b"same real original controls")
        (path/"pinned-baldosa.input").write_bytes(b"same real native controls")
        (path/"reference.log").write_text(
            "[input] loaded 10 event(s) from /tmp/R/work/zoom-zoo/replay/ref.input\n"
            "QA01RF049LDA f=6124 pc=82:82F0 value=D0\n")
        lines=[
            ("QA01RF054NATIVEBUS kind=read8 seq=%d frame=6124 master=%d "
             "addr=11%04X A=630D Y=%04X D=0000 dp63=63 dp64=00 dp65=11 "
             "scope=Snd_UploadBlockList_82EF_M1X0")%
            (i+1,10+i*22,0xC770+i,0xC770+i) for i in range(10)
        ]
        (path/"native.log").write_text("\n".join(lines)+"\n")
    static=root/"static.json"
    static.write_text(json.dumps({
        "schema":"ur-qa01-rf062-wrapper-only-generated-c-diff/1",
        "only_one_live_generated_c_file_changed":True}))
    return w,c,static,bins/"native",bins/"native-control"

class RF062WrapperAB(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.items=fixture(Path(t.name))

    def check(self):
        with mock.patch.object(target,"retained_memory_control",return_value={
            "original_and_native_exact_variant_raw_memory_equal":True,
            "full_raw_images_independently_reopened":712,
            "unique_relative_race_frames":78,
            "earned_Bowl_handoff_offsets":11,
            "first_12_between_variant_raw_memory_differences":[],
            "number_of_between_variant_raw_memory_differences":0,
            "every_unsampled_CPU_opcode_or_frame_proven_equivalent":False,
        }):
            return target.compare(*self.items)

    def test_genuine_shaped_positive_stays_bounded(self):
        r=self.check()
        self.assertTrue(r["bounded_wrapper_substitution_noninterference_supported"])
        self.assertTrue(r["all_helper_native_local_master_cycles_equal"])
        self.assertEqual(r["genuine_CPU_helper_count_wrapped"],10)
        self.assertFalse(r["undetected_CPU_instructions_or_CPU_joypad_polls_equivalent_proven"])
        self.assertEqual(r["accepted_USA_events"],0)

    def test_changed_real_native_helper_clock_is_a_scientific_negative(self):
        wrapped=self.items[0]/"work/zoom-zoo/replay/native.log"
        wrapped.write_text(wrapped.read_text().replace("master=98 ","master=99 "))
        r=self.check()
        self.assertTrue(r["all_helper_observed_address_register_rows_equal"])
        self.assertFalse(r["bounded_wrapper_substitution_noninterference_supported"])

    def test_changed_helper_address_is_recorded_not_waived(self):
        wrapped=self.items[0]/"work/zoom-zoo/replay/native.log"
        wrapped.write_text(wrapped.read_text().replace("addr=11C774","addr=11C775"))
        r=self.check()
        self.assertFalse(r["all_helper_observed_address_register_rows_equal"])
        self.assertIsNotNone(r["first_observed_helper_edit"])

    def test_changed_original_source_execution_is_rejected(self):
        wrapped=self.items[0]/"work/zoom-zoo/replay/reference.log"
        wrapped.write_text(wrapped.read_text().replace("value=D0","value=D1"))
        with self.assertRaisesRegex(ValueError,"original emulator actual execution"):
            self.check()

    def test_original_guest_controller_input_must_be_identical(self):
        wrapped=self.items[0]/"work/zoom-zoo/replay/ref.input"
        wrapped.write_bytes(b"modified original controls")
        with self.assertRaisesRegex(ValueError,"actual original supplied controls"):
            self.check()

    def test_changed_native_executable_bytes_cannot_claim_frozen_source(self):
        wrapped=self.items[3]
        wrapped.write_bytes(wrapped.read_bytes()+b"bad")
        with self.assertRaisesRegex(ValueError,"authenticated and distinct"):
            self.check()

    def test_false_single_source_delta_report_rejected(self):
        static=self.items[2]
        static.write_text(json.dumps({
            "schema":"ur-qa01-rf062-wrapper-only-generated-c-diff/1",
            "only_one_live_generated_c_file_changed":False}))
        with self.assertRaisesRegex(ValueError,"one-site compiled source"):
            self.check()

    def test_changed_78_sample_mesh_disproves_same_guest_progression(self):
        wrapped=self.items[0]/"producer-report.json"
        r=json.loads(wrapped.read_text())
        r["zoo_race_mesh"]["sampled_whole_Wram_pairs"]=77
        wrapped.write_text(json.dumps(r))
        self.assertFalse(self.check()["bounded_wrapper_substitution_noninterference_supported"])

if __name__=="__main__":unittest.main()
