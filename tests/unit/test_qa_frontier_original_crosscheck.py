"""Original-emulator cross-check of signed native frontier census cases."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa_frontier_original_crosscheck as m


def wram(**bytes_at: int) -> bytes:
    page = bytearray(131072)
    for addr, value in bytes_at.items():
        page[int(addr.removeprefix("a"), 16)] = value
    return bytes(page)


class FakeOriginal:
    """Writes a synthetic WRAM page per dumped frame; P1 X encodes the frame."""

    identity = {"original_rom_sha256": "x"}

    def __init__(self, divergent_frames=()):
        self.divergent = set(divergent_frames)
        self.inputs = []

    def run(self, control, frames, work):
        work.mkdir(parents=True)
        self.inputs.append(control)
        out = {}
        for f in frames:
            page = bytearray(131072)
            page[0x0313] = 1
            x = 0 if f < 2000 else f * 64 + (64 if f in self.divergent else 0)
            page[0x0411:0x0413] = (x & 0xFFFF).to_bytes(2, "little")
            p = work / f"o-{f}.wram.bin"
            p.write_bytes(bytes(page))
            out[f] = p
        return out


class Crosscheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_shift_moves_only_post_entry_events_earlier(self):
        text = "# c\n1080:2:100:000\n1180:2:100:000\n1650:60:080:040\n"
        shifted = m.shift_post_entry(text, 2)
        self.assertEqual(shifted, "# c\n1080:2:100:000\n1178:2:100:000\n1648:60:080:040\n")
        self.assertEqual(m.shift_post_entry(text, 0), text)
        with self.assertRaisesRegex(ValueError, "implausible"):
            m.shift_post_entry(text, 40)
        with self.assertRaisesRegex(ValueError, "before race entry"):
            m.shift_post_entry("1135:2:100:000\n", 2)

    def test_case_input_is_the_exact_frontier_planner_stream(self):
        import qa02_native_2p_seeded_endurance as guest
        import qa_adaptive_frontier as frontier
        prefix, _ = guest.base_source()
        actions, _ = frontier.actions_for(50036056, "rotation")
        self.assertEqual(m.case_input(50036056, "rotation"),
                         guest.render_input(prefix, actions, None))

    def _census(self, fake_pages_lag, seed, run):
        """Native tokens for a case whose original side is FakeOriginal at ``lag``."""
        fake = FakeOriginal()
        dumps = fake.run("", [f - fake_pages_lag for f in m.CENSUS_FRAMES], self.root / "n")
        census = {}
        for f in m.CENSUS_FRAMES:
            tok = m.frontier.normalized_token(dumps[f - fake_pages_lag], f"endurance-{f}")
            census[tok] = (run if f != 1740 else 1, seed if f != 1740 else 7, "rotation", 0)
        return census

    def test_agreement_divergence_and_attribution(self):
        census = self._census(2, 50036056, 99)
        good = m.check_case(FakeOriginal(), census, 99, 50036056, "rotation", 2,
                            self.root / "a")
        self.assertEqual(good["disposition"], "coarse_agreement")
        self.assertEqual([c["relation"] for c in good["checkpoints"]],
                         ["shared_seed_independent", "this_case", "this_case"])
        self.assertEqual(good["original_frame_for_native_2580"], 2578)
        self.assertFalse((self.root / "a" / "50036056-rotation").exists())
        bad = m.check_case(FakeOriginal(divergent_frames={3418}), census, 99,
                           50036056, "rotation", 2, self.root / "b")
        self.assertEqual(bad["disposition"], "coarse_divergence")
        self.assertEqual(bad["first_divergent_native_frame"], 3420)
        # A token owned by another case is never credited as agreement.
        other = m.check_case(FakeOriginal(), census, 99, 50036057, "rotation", 2,
                             self.root / "c")
        self.assertEqual(other["checkpoints"][1]["relation"], "other_case")
        self.assertEqual(other["disposition"], "coarse_divergence")
        # The wrong declared lag samples other original frames.
        wrong = m.check_case(FakeOriginal(), census, 99, 50036056, "rotation", 0,
                             self.root / "d")
        self.assertEqual(wrong["first_divergent_native_frame"], 2580)

    def test_original_errors_are_retained_not_counted(self):
        census = self._census(2, 50036056, 99)
        ledger = {"records": [{"campaign": "frontier", "github_run_id": 99,
                               "disposition": "completed_positive",
                               "metrics": {"native_executable_sha256": "e"}}]}

        class Broken(FakeOriginal):
            def run(self, *a):
                raise RuntimeError("emulator exited 1")
        with mock.patch.object(m, "load_census", return_value=(census, "c")):
            report = m.crosscheck(ledger, 99, 2, Broken(), self.root / "w", 1, None, None)
        self.assertEqual(report["counts"], {"original_error": 1})
        self.assertEqual(report["divergent_cases"], [])
        self.assertEqual(report["release_gate_credit"], 0)
        self.assertFalse(report["original_native_parity_claimed"])

    def test_requires_single_completed_frontier_record(self):
        with self.assertRaisesRegex(ValueError, "single completed"):
            m.run_record({"records": [{"campaign": "frontier", "github_run_id": 5,
                                       "disposition": "incomplete_or_failed"}]}, 5)

    def test_refuses_reused_evidence_root(self):
        work = self.root / "used"
        work.mkdir()
        orig = m.Original.__new__(m.Original)
        with self.assertRaisesRegex(ValueError, "reuse"):
            m.Original.run(orig, "", [1], work)


if __name__ == "__main__":
    unittest.main()
