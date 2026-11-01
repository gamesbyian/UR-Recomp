"""ROM-free negative controls for the QA-05 Windows Restart log oracle."""
from __future__ import annotations

import unittest

from tools.qa05_restart_input_guard import (
    validate_restart_guest_input, validate_restart_p2_guest_input,
)


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


def p2_trace(*, leak_at=None, missing=None, malformed=False, bad_countdown=False):
    lines = []
    for index in range(12):
        if index == missing:
            continue
        guest = "0100" if index == leak_at else "0000"
        remaining = 9 if bad_countdown and index == 3 else 11 - index
        lines.append(
            f"UR_RESTART_INPUT_P2 raw=0100 guest={guest} "
            f"return_held={int(index < 4)} "
            f"release_waiting={int(index < 4)} remaining={remaining}"
        )
    if malformed:
        lines.append("UR_RESTART_INPUT_P2 raw=0100 guest=0100 remaining=?")
    return "\n".join(lines) + "\n"


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
        corrupted = trace() + "UR_RESTART_INPUT raw=1000 guest=1000\n"
        with self.assertRaisesRegex(ValueError, "malformed UR_RESTART_INPUT"):
            validate_restart_guest_input(corrupted)

    def test_extra_malformed_countdown_cannot_hide_start(self):
        corrupted = trace() + (
            "UR_RESTART_INPUT raw=1000 guest=1000 return_held=0 "
            "release_waiting=0 host_owned=0 remaining=?\n"
        )
        with self.assertRaisesRegex(ValueError, "malformed UR_RESTART_INPUT"):
            validate_restart_guest_input(corrupted)

    def test_extra_p1_namespace_malformed_line_cannot_hide_start(self):
        # A missing delimiter previously vanished from the emitted-line
        # census, letting twelve valid probes plus a corrupt Start leak pass.
        for extra in (
            "UR_RESTART_INPUTguest=1000",
            "UR_RESTART_INPUT_P1 raw=1000 guest=1000",
            "UR_RESTART_INPUT_P3 raw=1000 guest=1000",
            "UR_RESTART_INPUT\traw=1000 guest=1000",
        ):
            with self.subTest(extra=extra), self.assertRaisesRegex(
                ValueError, "malformed UR_RESTART_INPUT"
            ):
                validate_restart_guest_input(trace() + extra + "\n")

    def test_malformed_p2_namespace_stays_in_p2_parser(self):
        with self.assertRaisesRegex(ValueError, "malformed UR_RESTART_INPUT_P2"):
            validate_restart_guest_input(trace() + p2_trace() +
                                         "UR_RESTART_INPUT_P2guest=0100\n")

    def test_unrelated_diagnostics_remain_allowed(self):
        self.assertEqual(
            validate_restart_guest_input(
                "UR_OTHER_EVENT ready=1\n" + trace() + "UR_OTHER_EVENT done=1\n"
            ), 12
        )

    def test_new_p2_diagnostics_coexist_with_p1_and_are_checked(self):
        combined = trace() + p2_trace()
        self.assertEqual(validate_restart_guest_input(combined), 12)
        self.assertEqual(validate_restart_p2_guest_input(combined), 12)

    def test_p2_guest_start_leak_rejected_even_with_valid_p1(self):
        with self.assertRaisesRegex(ValueError, "P2 post-Restart sample 5: guest Start leaked"):
            validate_restart_guest_input(trace() + p2_trace(leak_at=4))

    def test_p2_truncated_or_malformed_diagnostic_rejected(self):
        for extra in (p2_trace(missing=3), p2_trace(malformed=True)):
            with self.subTest(extra=extra[-60:]), self.assertRaisesRegex(
                ValueError, "P2 post-Restart|malformed UR_RESTART_INPUT_P2"
            ):
                validate_restart_guest_input(trace() + extra)

    def test_p2_countdown_discontinuity_rejected(self):
        with self.assertRaisesRegex(ValueError, "P2 post-Restart sample 4: expected remaining=8"):
            validate_restart_guest_input(trace() + p2_trace(bad_countdown=True))

    def test_strict_p2_witness_rejects_vacuous_no_start_probes(self):
        valid = trace() + p2_trace()
        self.assertEqual(
            validate_restart_guest_input(valid, require_p2_start_witness=True),
            12,
        )
        self.assertEqual(
            validate_restart_p2_guest_input(
                p2_trace(), require_raw_start_witness=True), 12,
        )
        # A 12-line, zero-leak P2 trace does not prove the Return/Start
        # collision was ever exercised. Keep the ordinary P1-only diagnostic
        # backwards-compatible, but refuse it as a two-seat witness.
        variants = (
            trace(),
            trace() + p2_trace().replace('raw=0100', 'raw=0000'),
            trace() + p2_trace().replace(
                'raw=0100 guest=0000 return_held=1',
                'raw=0000 guest=0000 return_held=1'),
            trace() + p2_trace().replace(
                'return_held=1', 'return_held=0'),
            trace() + p2_trace().replace(
                'release_waiting=1', 'release_waiting=0'),
        )
        for candidate in variants:
            with self.subTest(candidate=candidate[-90:]), self.assertRaisesRegex(
                    ValueError, 'P2 raw Start/held Return witness absent'):
                validate_restart_guest_input(
                    candidate, require_p2_start_witness=True)
        self.assertEqual(
            validate_restart_guest_input(
                trace() + p2_trace().replace('raw=0100', 'raw=0000')),
            12,
        )

    def test_historical_p1_only_log_remains_valid_without_p2_credit(self):
        self.assertEqual(validate_restart_guest_input(trace()), 12)
        self.assertEqual(validate_restart_p2_guest_input(trace()), 0)

    def test_missing_diagnostics_is_not_success(self):
        with self.assertRaisesRegex(ValueError, "malformed UR_RESTART_INPUT"):
            validate_restart_guest_input("UR_RESTART_INPUT guest=0000")


if __name__ == "__main__":
    unittest.main()
