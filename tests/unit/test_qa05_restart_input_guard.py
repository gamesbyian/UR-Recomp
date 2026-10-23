"""ROM-free negative controls for the QA-05 Windows Restart log oracle."""
from __future__ import annotations

import unittest

from tools.qa05_restart_input_guard import validate_restart_guest_input


def trace(*, leak_at=None, waiting_cleared_at=4, missing=None, duplicate=False):
    lines = []
    for index in range(12):
        if index == missing:
            continue
        waiting = int(index < waiting_cleared_at)
        guest = "1000" if index == leak_at else "0000"
        lines.append(
            "UR_RESTART_INPUT raw=1000 guest=" + guest +
            f" return_held={waiting} release_waiting={waiting} "
            f"host_owned=0 remaining={11-index}"
        )
    if duplicate:
        lines.append(lines[-1])
    return "before\n" + "\n".join(lines) + "\nafter\n"


class RestartInputGuardTest(unittest.TestCase):
    def test_valid_window_with_latch_release(self):
        self.assertEqual(validate_restart_guest_input(trace()), 12)

    def test_early_disarm_cannot_hide_guest_start(self):
        with self.assertRaisesRegex(ValueError, "guest Start leaked"):
            validate_restart_guest_input(trace(leak_at=6, waiting_cleared_at=2))

    def test_held_latch_cannot_hide_guest_start(self):
        with self.assertRaisesRegex(ValueError, "guest Start leaked"):
            validate_restart_guest_input(trace(leak_at=1))

    def test_missing_sample_is_not_success(self):
        with self.assertRaisesRegex(ValueError, "expected 12"):
            validate_restart_guest_input(trace(missing=7))

    def test_duplicate_sample_is_not_success(self):
        with self.assertRaisesRegex(ValueError, "expected 12"):
            validate_restart_guest_input(trace(duplicate=True))

    def test_noncontiguous_countdown_is_not_success(self):
        corrupted = trace().replace("remaining=8", "remaining=9")
        with self.assertRaisesRegex(ValueError, "expected remaining=8"):
            validate_restart_guest_input(corrupted)

    def test_extra_truncated_probe_cannot_hide_start(self):
        corrupted = trace() + "UR_RESTART_INPUT raw=1000 guest=1000\\n"
        with self.assertRaisesRegex(ValueError, "malformed UR_RESTART_INPUT"):
            validate_restart_guest_input(corrupted)

    def test_extra_malformed_countdown_cannot_hide_start(self):
        corrupted = trace() + (
            "UR_RESTART_INPUT raw=1000 guest=1000 return_held=0 "
            "release_waiting=0 host_owned=0 remaining=?\\n"
        )
        with self.assertRaisesRegex(ValueError, "malformed UR_RESTART_INPUT"):
            validate_restart_guest_input(corrupted)

    def test_unrelated_diagnostics_remain_allowed(self):
        self.assertEqual(
            validate_restart_guest_input(
                "UR_OTHER_EVENT ready=1\\n" + trace() + "UR_OTHER_EVENT done=1\\n"
            ), 12
        )

    def test_missing_diagnostics_is_not_success(self):
        with self.assertRaisesRegex(ValueError, "malformed UR_RESTART_INPUT"):
            validate_restart_guest_input("UR_RESTART_INPUT guest=0000")


if __name__ == "__main__":
    unittest.main()
