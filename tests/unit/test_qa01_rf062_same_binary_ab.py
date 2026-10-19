"""ROM-free adversarial on/off original/native helper observation tests."""
from __future__ import annotations
import copy
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
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
    def make_archive(self, path, *, omit=None, prefix=""):
        a,b,c,d,e,f=fixtures()
        payload={}
        for mode,report,logs,inputs in (("off",a,c,e),("on",b,d,f)):
            base=(prefix + "/" if prefix else "") + "qa01-rf062-ab/" + mode + "/"
            payload[base+"producer-report.json"]=json.dumps(report).encode()
            for guest,label in (("original","reference.log"),("native","native.log")):
                payload[base+"work/zoom-zoo/replay/"+label]=logs[guest]
            for guest,label in (("original","ref.input"),("native","pinned-baldosa.input")):
                payload[base+"work/zoom-zoo/replay/"+label]=inputs[guest]
        common_root=(prefix + "/" if prefix else "")
        payload[common_root+"qa01-case/case-result.json"]=json.dumps({
            "source_sha":"a"*40, "producer_exit_code":0,
            "disposition":"strict_candidate", "release_credit":0,
        }).encode()
        payload[common_root+"qa01-case/producer-report.json"]=json.dumps(b).encode()
        if omit is not None:
            payload.pop(next(k for k in payload if k.endswith(omit)))
        with zipfile.ZipFile(path,"w") as z:
            for name,bytes_ in payload.items():
                z.writestr(name,bytes_)
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_independent_zip_archive_replay_from_immutable_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"real-shaped.zip"
            digest=self.make_archive(path,prefix="runner-archive")
            result=x.archived(path,digest)
            self.assertEqual(result["authenticated_evidence_archive_sha256"],digest)
            self.assertTrue(result["zip_archive_raw_byte_reopened"])
            self.assertTrue(result["runtime_RF062_logging_noninterference_supported"])
            with self.assertRaisesRegex(ValueError,"SHA256 changed"):
                x.archived(path,"0"*64)

    def test_archived_actual_source_case_must_identify_on_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"source-join.zip"
            self.make_archive(path,omit="qa01-case/producer-report.json")
            with self.assertRaisesRegex(ValueError,"case source receipt missing"):
                x.archived(path)
            self.make_archive(path,omit="qa01-case/case-result.json")
            with self.assertRaisesRegex(ValueError,"case source receipt missing"):
                x.archived(path)

    def test_archive_missing_guest_control_is_not_implicitly_recovered(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"missing.zip"
            self.make_archive(path,omit="off/work/zoom-zoo/replay/ref.input")
            with self.assertRaisesRegex(ValueError,"missing or unbounded"):
                x.archived(path)

    def test_archive_duplicate_member_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"duplicate.zip"
            self.make_archive(path)
            with zipfile.ZipFile(path,"a") as z:
                z.writestr("qa01-rf062-ab/on/producer-report.json",b"{}")
            with self.assertRaisesRegex(ValueError,"duplicate/unsafe"):
                x.archived(path)

    def test_real_binary_artifact_bytes_not_merely_report_digest_strings(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"native-and-original.zip"
            binaries={
                "native":b"dummy test native image",
                "snes9x_libretro.so":b"dummy independent original core",
                "snesref":b"dummy source movie runner",
            }
            receipts={k:hashlib.sha256(v).hexdigest() for k,v in binaries.items()}
            with zipfile.ZipFile(path,"w") as z:
                for name,raw in binaries.items():
                    z.writestr(name,raw)
                z.writestr("SHA256SUMS","".join(
                    receipts[k]+"  "+k+"\n" for k in binaries).encode())
            source={"native_executable_sha256":receipts["native"],
                    "reference_core_sha256":receipts["snes9x_libretro.so"]}
            receipt=x.independent_binaries(path,source,
                                           hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertTrue(receipt["all_three_emulator_tool_binaries_rehashed"])
            source["native_executable_sha256"]="0"*64
            with self.assertRaisesRegex(ValueError,"real emulator binary bytes disagree"):
                x.independent_binaries(path,source)
            source["native_executable_sha256"]=receipts["native"]
            with self.assertRaisesRegex(ValueError,"binary artifact changed"):
                x.independent_binaries(path,source,"f"*64)
            with zipfile.ZipFile(path,"a") as z:
                z.writestr("native",b"replaced")
            with self.assertRaisesRegex(ValueError,"missing/duplicated"):
                x.independent_binaries(path,source)

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
        actual = d["native"].splitlines(keepends=True)
        d["native"] = b"".join(
            row.replace(b"master=3160 addr=11C774",
                        b"master=3161 addr=11C774")
            if row.startswith(b"QA01RF062NATIVE ") else row
            for row in actual)
        # Uncorroborated RF062 wrapper rows are never admissible.
        with self.assertRaisesRegex(ValueError,"not a real same-clock"):
            x.control(a,b,c,d,e,f)

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

    def test_exact_three_original_source_workdir_paths_not_guest_behavior(self):
        original_lines = (
            "[input] loaded 397 event(s) from /runner/A/work/zoom-zoo/replay/ref.input",
            "script: loaded 112 command(s) from /runner/A/work/zoom-zoo/replay/complete.script",
            "[memory] loaded 8192 SRAM bytes from /runner/A/work/zoom-zoo/anchored.srm",
            "QA01RF049LDA frame=6124 pc=82:82F0 ea=11C774 a1=63D0",
        )
        off = ("\n".join(original_lines) + "\n").encode()
        on = ("\n".join(x.replace("/runner/A/", "/runner/B/")
                         for x in original_lines) + "\n").encode()
        scope = x.strictly_qualified_original_path_variation(off,on)
        self.assertFalse(scope["exact_log_bytes_equal"])
        self.assertTrue(scope["source_nonpath_log_equality_proven"])
        self.assertEqual(len(scope["allowed_path_metadata_changes"]),3)
        a,b,c,d,e,f=fixtures()
        c["original"], d["original"] = off,on
        result=x.control(a,b,c,d,e,f)
        self.assertTrue(result["runtime_RF062_logging_noninterference_supported"])
        self.assertFalse(result["original_complete_log_byte_identical"])
        self.assertEqual(len(result["original_qualified_source_log_path_differences"]
                             ["allowed_path_metadata_changes"]),3)

    def test_guest_read_byte_or_clock_cannot_be_hidden_as_a_path_difference(self):
        original = (
            "[input] loaded 397 event(s) from /runner/A/work/zoom-zoo/replay/ref.input\n"
            "QA01RF049LDA frame=6124 pc=82:82F0 ea=11C774 a1=63D0\n"
        ).encode()
        other=original.replace(b"/runner/A/", b"/runner/B/").replace(
            b"a1=63D0", b"a1=63D1")
        a,b,c,d,e,f=fixtures()
        c["original"],d["original"]=original,other
        result=x.control(a,b,c,d,e,f)
        self.assertFalse(result["runtime_RF062_logging_noninterference_supported"])
        self.assertFalse(result["original_qualified_source_log_path_differences"]
                         ["source_nonpath_log_equality_proven"])
        # Even a changed input count at the exact allowed file suffix fails.
        other=original.replace(b"397 event(s)", b"396 event(s)")
        scope=x.strictly_qualified_original_path_variation(original,other)
        self.assertFalse(scope["source_nonpath_log_equality_proven"])

    def test_native_host_elapsed_and_exact_script_path_do_not_mask_cpu_events(self):
        a,b,c,d,e,f=fixtures()
        c["native"] = (
            b"[host +0.080s] SDL init ok: video=x11 audio=dummy\n"
            b"script: loaded 112 entries from '/runner/A/zoom-zoo/replay/complete.script'\n"
            + c["native"]
            + b"[host +109.676s] exit: script quit after 6460 frames\n"
        )
        d["native"] = (
            b"[host +0.078s] SDL init ok: video=x11 audio=dummy\n"
            b"script: loaded 112 entries from '/runner/B/zoom-zoo/replay/complete.script'\n"
            + d["native"]
            + b"[host +109.698s] exit: script quit after 6460 frames\n"
        )
        report=x.control(a,b,c,d,e,f)
        native=report["native_complete_nonRF062_log_metadata_limited_comparison"]
        self.assertTrue(native["all_other_native_lines_byte_equal_after_strict_host_metadata"])
        self.assertEqual(len(native["accepted_host_only_metadata_lines"]),3)
        self.assertTrue(report["runtime_RF062_logging_noninterference_supported"])
        # A changed CPU/SPC line is NOT host elapsed time or script metadata.
        d["native"]+=b"QA01RF050NATIVEPORT port=3 val=DE\n"
        broken=x.control(a,b,c,d,e,f)
        self.assertFalse(broken["runtime_RF062_logging_noninterference_supported"])
        self.assertFalse(broken["native_complete_nonRF062_log_metadata_limited_comparison"]
                         ["all_other_native_lines_byte_equal_after_strict_host_metadata"])

    def test_original_control_log_change_cannot_yield_positive_native_ab(self):
        a,b,c,d,e,f=fixtures()
        d["original"] += b"UNEXPLAINED_SOURCE_NMI_CHANGE\\n"
        result=x.control(a,b,c,d,e,f)
        self.assertFalse(result["original_complete_log_byte_identical"])
        self.assertTrue(result["native_actual_RF054_CPU_master_clocks_equal"])
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
