"""Research-only two-seat Baldosa input shim: install boundary and refusals."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import research_baldosa_2p_input_patch as m
import baldosa_qa_dense_scene_input_patch as qa

HOST = ("static int other;\n" + m.MARKER_DECL + "  return 0;\n}\n"
        "void loop(void) {\n" + m.MARKER_INPUT + "}\n")


class Shim(unittest.TestCase):
    def test_installs_once_with_full_two_seat_override(self):
        out = m.patch(HOST)
        self.assertEqual(out.count("UrResearch2pInputAt("), 2)
        self.assertIn("inputs = (inputs & ~0xffffffu) | ur_r2p_mask;", out)
        self.assertIn('getenv("UR_RESEARCH_2P_INPUT_FILE")', out)
        # p2 occupies bits 12..23 of the host input word
        self.assertIn("event->mask = p1 | (p2 << 12);", out)
        with self.assertRaisesRegex(ValueError, "already installed"):
            m.patch(out)

    def test_never_combines_with_the_qa01_one_seat_shim(self):
        with self.assertRaisesRegex(ValueError, "already installed"):
            m.patch(qa.patch(HOST))

    def test_refuses_an_unrecognised_host(self):
        with self.assertRaises(ValueError):
            m.patch("int main(void) { return 0; }\n")


if __name__ == "__main__":
    unittest.main()
