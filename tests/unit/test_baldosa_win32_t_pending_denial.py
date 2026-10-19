"""Strict source-console evidence guard for a partially completed original T."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from baldosa_win32_interactive_t_pending_delete_denial import (
    validate_refused_t_transcript,
)


PROMPT = "Explicit recovery choice [R/T/S/Q]: T"
CHOICE = "UR_BALDOSA_RECOVERY_CHOICE choice=typed status=4"
REFUSAL = "UR-BALDOSA-RECOVERY-REFUSED:"
WARNING = "Recovery did not complete; no safe relaunch was authorized"
PARTIAL = "Some files may already have been archived or restored"
VALID = "\n".join((PROMPT, CHOICE, REFUSAL, WARNING, PARTIAL))


class PartialTRefusalTranscriptTests(unittest.TestCase):
    def test_complete_original_console_witness(self):
        validate_refused_t_transcript(VALID, True)

    def test_real_console_key_is_required(self):
        with self.assertRaises(ValueError):
            validate_refused_t_transcript(VALID, False)

    def test_no_invented_guest_success_or_false_restart(self):
        for extra in (
            "first frame simulated",
            "UR-BALDOSA-RECOVERY-COMMITTED:",
            PROMPT,
            REFUSAL,
        ):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                validate_refused_t_transcript(VALID + "\n" + extra, True)

    def test_partial_restore_must_be_described_truthfully(self):
        for text in (
            VALID.replace(WARNING, ""),
            VALID.replace(PARTIAL, ""),
            VALID.replace(PARTIAL, "No automatic replacement was made"),
            VALID.replace(CHOICE, "UR_BALDOSA_RECOVERY_CHOICE choice=typed status=1"),
        ):
            with self.subTest(text=text[-70:]), self.assertRaises(ValueError):
                validate_refused_t_transcript(text, True)

    def test_no_bare_refusal_or_unverified_success(self):
        for missing in (PROMPT, CHOICE, REFUSAL):
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                validate_refused_t_transcript(VALID.replace(missing, ""), True)


if __name__ == "__main__":
    unittest.main()
