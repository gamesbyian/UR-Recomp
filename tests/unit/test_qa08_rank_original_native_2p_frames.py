"""Offline candidate original/native 2P screen alignment, not guest parity."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools import qa08_rank_original_native_2p_frames as subject
from tools import qa08_auth_original_2p_frame_window as original

HANDOFF=Path(__file__).resolve().parents[2]/"analysis/data/qa08-original-native-channel5-hdma-coldata-source-handoff.json"

def evidence(root):
    witness=json.loads(HANDOFF.read_text(encoding="utf8"))
    native=bytes(256*224*4)
    rows=[]
    for f in original.FRAMES:
        a=bytearray(native)
        # Synthetic ONLY. Source pixels deliberately put on exactly one
        # 256x224 screen, with no claimed original/native causal alignment.
        if f!=2208:
            for y in range(32,80):
                for x in range(32,208):
                    a[4*(256*y+x)]=abs(f-2208)%256
            for y in range(144,192):
                for x in range(32,208):
                    a[4*(256*y+x)]=(f-2187)%256
        data=bytes(a)
        (root/f"frame_{f:06d}_256x224.raw").write_bytes(data)
        rows.append({
            "original_Snesref_callback_frame_zero_based":f,
            "corresponding_original_retro_run_one_based":f+1,
            "raw_B_G_R_X_SHA256":hashlib.sha256(data).hexdigest()})
    return {
        "schema":subject.SCHEMA,
        "original_ROM_SHA256":"859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
        "original_script_SHA256":"94eaa5ffb487d9b227e34965c1d2ee09efe3dac06ade595f7dad05315dfc5221",
        "full_256x224_original_frames":37,
        "same_input_guest_phase_and_camera_as_native_proven":False,
        "original_vs_native_final_RGBA_parity_proven":False,
        "source_original_frames":rows},native,witness

class OriginalNativeTwoPlayerSourceFrameTest(unittest.TestCase):
    def test_exact_image_registration_diagnostic_without_false_qa(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            witness,native,handoff=evidence(root)
            report=subject.rank(root,witness,native,handoff)
            self.assertEqual(report["best_visual_frame_only_unverified_hypothesis"],2208)
            self.assertEqual(report["sorted_candidate_frames"][0],2208)
            self.assertFalse(report["original_native_exact_gameplay_state_and_2P_camera_alignment_proven"])
            self.assertFalse(report["original_native_final_RGB_composition_parity_proven"])
            best=next(x for x in report["all_source_frame_similarity_by_original_callback"]
                      if x["original_callback_frame"]==2208)
            self.assertEqual(best["regions"]["upper_play"]["exact_pixel_fraction"],1.0)

    def test_no_stale_unnamed_original_or_wrong_native_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            witness,native,handoff=evidence(root)
            (root/"frame_002208_256x224.raw").write_bytes(b"incorrect source")
            with self.assertRaisesRegex(ValueError,"source PPU image hash"):
                subject.rank(root,witness,native,handoff)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            witness,native,handoff=evidence(root)
            handoff["native_PPU_2P_guest_frame"]=2209
            with self.assertRaisesRegex(ValueError,"identity"):
                subject.rank(root,witness,native,handoff)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            witness,native,handoff=evidence(root)
            witness["same_input_guest_phase_and_camera_as_native_proven"]=True
            with self.assertRaisesRegex(ValueError,"identity"):
                subject.rank(root,witness,native,handoff)

    def test_genuine_native_source_P7_has_fixed_format_and_sha_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"native.pam"
            path.write_bytes(b"P7\nWIDTH 342\nHEIGHT 224\nENDHDR\n")
            with self.assertRaisesRegex(ValueError,"SHA"):
                subject.load_native(path)

if __name__=="__main__":unittest.main()
