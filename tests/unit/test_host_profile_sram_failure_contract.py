"""QA-02: host-owned SRAM and profile mirror must share failure discipline.

The native process fixture exercises the real profile-state CAS including
authorized rollback and a conflicting third writer. This source contract binds
that tested primitive to the production *second-phase SRAM failure* branch.
A text contract alone does not prove power-loss safety or a packaged journey.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class HostProfileSramFailureContract(unittest.TestCase):
    def test_live_snapshot_rolls_back_only_own_intermediate_profile(self):
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        body = host.split("bool persist_live_profile_snapshot() {", 1)[1].split(
            "\n}\n\nbool activate_profile_id", 1
        )[0]
        self.assertIn("const auto original_state = *g_profile_state;", body)
        self.assertRegex(
            body,
            r"save_host_profile_state_file_if_current\\s*\\("
            r"[^;]*original_state,\\s*candidate\\)",
        )
        self.assertRegex(
            body,
            r"if \\(!RtlTryWriteSram\\(\\)\\)\\s*\\{"
            r"[^}]*save_host_profile_state_file_if_current\\s*\\("
            r"[^;]*candidate,\\s*original_state\\)",
        )
        self.assertIn("SRAM_FAILED_ROLLBACK_CONFLICT", body)
        self.assertLess(
            body.index("if (!RtlTryWriteSram())"),
            body.index("g_profile_state = std::move(candidate)"),
            "Do not advance the in-memory CAS baseline before SRAM commits",
        )


if __name__ == "__main__":
    unittest.main()
