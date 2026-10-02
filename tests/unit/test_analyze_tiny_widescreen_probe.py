import unittest

from tools.analyze_tiny_widescreen_probe import classify_margin, contact_word, trajectory_state


class TinyWidescreenProbeAnalyzerTests(unittest.TestCase):
    def _wram(self, collision=0x22):
        blob = bytearray(0x20000)

        def put16(addr, value):
            blob[addr] = value & 0xFF
            blob[addr + 1] = value >> 8

        blob[0x0313] = 1
        put16(0x0411, 25271)
        put16(0x0415, 857)
        put16(0x04B7, 216)
        put16(0x04BB, 0)
        put16(0x0419, 25199)
        put16(0x0E95, collision)
        put16(0x1199, 1)
        put16(0x119D, 1)
        put16(0x0EF1, 0)
        return bytes(blob)

    def test_contact_word_is_diagnostic_not_part_of_durable_trajectory(self):
        control = self._wram(0x22)
        widened = self._wram(0x26)
        self.assertEqual(trajectory_state(control), trajectory_state(widened))
        self.assertNotEqual(contact_word(control), contact_word(widened))

    def test_constant_cadence_plus_transient_contact_classifies_non_authoritative(self):
        rows = [
            {
                "trajectory_equal": True,
                "guest_frame_delta": -3,
                "contact_equal": i not in {2, 3},
            }
            for i in range(6)
        ]
        self.assertEqual(
            classify_margin(rows),
            "cadence-aligned-transient-contact-only",
        )

    def test_trajectory_difference_remains_hard_failure(self):
        rows = [
            {
                "trajectory_equal": True,
                "guest_frame_delta": -3,
                "contact_equal": True,
            },
            {
                "trajectory_equal": False,
                "guest_frame_delta": -3,
                "contact_equal": True,
            },
        ]
        self.assertEqual(
            classify_margin(rows),
            "meaningful-authoritative-divergence",
        )


if __name__ == "__main__":
    unittest.main()
