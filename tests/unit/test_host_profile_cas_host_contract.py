"""Reject restoration of unguarded production profile writes.

The unit process fixture separately exercises the actual OS-handle-owned lock.
This source contract stops future host routes from accidentally bypassing it.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class HostProfileCasHostContract(unittest.TestCase):
    def test_every_production_profile_mutation_uses_expected_state(self):
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("save_host_profile_state_file(", host)
        # Includes save/resume, rollback of failed SRAM publication, rename
        # compensation, profile creation, Recent Course and ghost metadata.
        self.assertGreaterEqual(
            host.count("save_host_profile_state_file_if_current("), 11
        )


if __name__ == "__main__":
    unittest.main()
