"""RF045/RF047 actual-log readiness must not fabricate a causal witness."""
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf045_rf047_causal_readiness as m


class CausalReadiness(unittest.TestCase):
    @staticmethod
    def original(with_seq=True):
        prefix = "seq=1 " if with_seq else ""
        return (
            f"QA01RF045ORIGSTACK {prefix}f=1017 kind=pullB pc=82:D4EE\n"
            "QA01RF044ORIGBUS f=1017 kind=wb addr=01ED\n"
            "QA01RF044ORIGNMI f=1017 pc=82D4EE\n"
        )

    @staticmethod
    def native(opcode=True):
        lines = [
            "WRAM writer fragment QA01RF047NATIVE seq=1 stage=entry f=1017",
            "QA01RF047NATIVE seq=2 stage=read f=1017 bank=00 addr=01ED width=1 value=0026 nmi=1",
        ]
        if opcode:
            lines.append("QA01RF047NATIVE seq=3 stage=opcode f=1017 guestPC=82D4F0 tier=aot master=42")
        return "\n".join(lines) + "\n"

    def test_existing_legacy_logs_are_still_hold(self):
        report=m.inspect(self.original(with_seq=False), self.native(opcode=False))
        self.assertFalse(report["original_macro_local_seq_contiguous"])
        self.assertTrue(report["native_rf047_seq_contiguous"])
        self.assertEqual(report["native_reads_with_executed_guest_pc"], 0)
        self.assertFalse(report["eligible_for_causal_window_assess"])
        self.assertEqual(report["accepted_USA_events"], 0)
        self.assertEqual(report["consumer_schema"], "ur-qa01-causal-window/1")

    def test_new_opcode_marker_is_not_helper_read_execution_proof(self):
        report=m.inspect(self.original(), self.native())
        self.assertTrue(report["original_macro_local_seq_contiguous"])
        self.assertEqual(report["native_actual_opcode_pc_markers"], 1)
        self.assertEqual(report["native_reads_with_executed_guest_pc"], 0)
        self.assertFalse(report["original_shared_bus_checkpoint_seq_proven"])
        self.assertFalse(report["checkpoint_unmasked_actual_raw_bytes_reopened"])
        self.assertFalse(report["native_bus_pc_instruction_lifetime_proven"])

    def test_gaps_and_fake_pc_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "gap"):
            m.inspect(self.original(), self.native().replace("seq=2 stage=read","seq=3 stage=read"))
        with self.assertRaisesRegex(ValueError, "executed proof"):
            m.inspect(self.original(), self.native().replace(
                "value=0026 nmi=1", "value=0026 guestPC=82D4F0 nmi=1"))
        with self.assertRaisesRegex(ValueError, "marker incomplete"):
            m.inspect(self.original(), self.native().replace("guestPC=82D4F0", "guestPC=0000000"))
        with self.assertRaisesRegex(ValueError, "truncated"):
            m.inspect(self.original(), self.native()+"QA01RF047NATIVE_TRUNCATED\n")

    def test_archive_reopened_and_hashed_not_authenticated_by_assertion(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            case=root/"case.zip"
            with zipfile.ZipFile(case, "w") as z:
                z.writestr(m.SOURCE, self.original())
                z.writestr(m.NATIVE, self.native())
            report=m.from_case(case)
            self.assertEqual(len(report["case_zip_sha256"]),64)
            self.assertEqual(len(report["native_log_sha256"]),64)
            self.assertFalse(report["source_identity_independently_authenticated"])
            self.assertFalse(report["eligible_for_causal_window_assess"])


if __name__ == "__main__":
    unittest.main()
