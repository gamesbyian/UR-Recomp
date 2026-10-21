"""ROM-free, adversarial two-native-epoch 25-case visual acceptance contract."""
import copy
import json
from pathlib import Path
import unittest

from tools import qa_modern_visual_cross_epoch as qa


class ModernVisualCrossEpochTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(Path("analysis/modern-visual-acceptance-matrix.json").read_text())
        cls.old = json.loads(Path("analysis/evidence/modern-visual-integrated-final-sdl-21cases-20261021.json").read_text())
        cls.strict = json.loads(Path("analysis/evidence/modern-visual-strict-480p-1080p-zip-recheck-20261020.json").read_text())
        cls.stored = json.loads(Path("analysis/evidence/modern-visual-25case-independent-epoch-matrix-20261020.json").read_text())

    def check_rejected(self, m=None, o=None, s=None, x=None, pattern=""):
        with self.assertRaisesRegex(ValueError, pattern):
            qa.reconcile(m or self.matrix, o or self.old, s or self.strict, x or self.stored)

    def test_original_25_case_current_main_index_is_exact_and_zero_credit(self):
        result = qa.reconcile(self.matrix, self.old, self.strict, self.stored)
        self.assertEqual(result["source_epochs"],[qa.legacy.FROZEN_CHECKOUT_SHA,qa.SOURCE])
        self.assertNotEqual(qa.legacy.FROZEN_PE_SHA256,qa.PE)
        self.assertEqual(result["historical_native_cases"],25)
        self.assertEqual(result["counts"]["old_run_21_close"],5)
        self.assertEqual(result["counts"]["old_run_21_partial"],9)
        self.assertEqual(result["counts"]["separate_strict_output_cases"],4)
        self.assertEqual(result["counts"]["without_ANY_related_capture_across_both_epochs"],8)
        self.assertFalse(result["human_approved"])
        self.assertFalse(result["hardware_approved"])
        self.assertFalse(result["raw_capture_ZIPs_rechecked_this_run"])
        self.assertEqual(result["release_gate_credit"],0)

    def test_all_original_strict_cases_must_retain_full_p7_png_and_title_hashes(self):
        for key, value in (
            ("route","title-intro-reduced"), ("output",[1280,720]),
            ("PNG_sha256","0"*64), ("final_SDL_P7_sha256","1"*64),
            ("original_title_P7_sha256","2"*64),
            ("original_title_source_RGBA_FNV64","deadbeefdeadbeef"),
            ("logical_source",[256,224]), ("input","verified physical gamepad"),
        ):
            with self.subTest(key=key):
                strict=copy.deepcopy(self.strict)
                case=next(x for x in strict["cases"] if x["id"]=="title-wide-1080")
                case[key]=value
                self.check_rejected(s=strict,pattern="strict|title")

    def test_reject_changed_capture_case_set_and_duplicate_rows(self):
        strict=copy.deepcopy(self.strict)
        strict["cases"].append(copy.deepcopy(strict["cases"][0]))
        self.check_rejected(s=strict,pattern="four original")
        strict=copy.deepcopy(self.strict)
        strict["cases"][0]["id"]=strict["cases"][1]["id"]
        self.check_rejected(s=strict,pattern="duplicate")

    def test_reject_binary_epoch_swaps_and_native_overapproval(self):
        for key, val in (("checkout_sha","0"*40),("PE_SHA256","0"*64),
                         ("run_id",999),("artifact_id",9),("PE_bytes",10)):
            with self.subTest(key=key):
                strict=copy.deepcopy(self.strict)
                strict["source"][key]=val
                self.check_rejected(s=strict,pattern="executable/source epoch drift")
        for key,val in (("release_gate_credit",1),("human_approved",True),
                        ("physical_hardware_approved",True),
                        ("original_guest_parity_approved",True),
                        ("original_PNG_P7_exact_matches",3)):
            with self.subTest(key=key):
                strict=copy.deepcopy(self.strict)
                strict["result"][key]=val
                self.check_rejected(s=strict,pattern="overclaims")

    def test_reject_stored_human_approval_or_case_id_substitution(self):
        for field,val in (("acceptance","APPROVED"),("visual_accepted",True),
                          ("human_approved",True),("hardware_approved",True),
                          ("release_gate_credit",1),
                          ("required_input","pad-p2"),
                          ("required_state","earned-2p")):
            with self.subTest(field=field):
                index=copy.deepcopy(self.stored)
                index["cases"][6][field]=val
                self.check_rejected(x=index,pattern="stored cross-epoch matrix differs")
        index=copy.deepcopy(self.stored)
        index["counts"]["without_ANY_related_capture_across_both_epochs"]=0
        self.check_rejected(x=index,pattern="stored cross-epoch matrix differs")

    def test_different_native_epoch_cannot_pretend_old_21_source(self):
        old=copy.deepcopy(self.old)
        old["run"]["executable"]["sha256"]=qa.PE
        self.check_rejected(o=old,pattern="unqualified historical source/PE")
        old=copy.deepcopy(self.old)
        old["cases"][8]["source_sha_exact"]=False
        self.check_rejected(o=old,pattern="qualified 21-case")

    def test_original_capture_pe_archives_are_required_as_a_pair(self):
        # Negative-path tests do not mint a fake authentic Windows executable.
        with self.assertRaises((FileNotFoundError, OSError, ValueError)):
            qa.verify_original_archives(self.strict, Path("/does-not-exist.zip"),
                                        Path("/also-missing.zip"))


if __name__ == "__main__":
    unittest.main()
