from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from build_native_menu_sfx_route import EVENT_NAMES, build
from check_native_menu_sfx_commands import NATIVE_DUMPS, verify
from probe_menu_sfx_ids import RING_HEAD, RING_HI, RING_LO

EXPECTED = ROOT / "analysis/generated/menu-sfx-ids.json"


def snapshots(reference: dict) -> dict[str, bytes]:
    stages = {}
    mem = bytearray(0x20000)
    mem[0x009F] = 0xD7
    stages["e00-start"] = bytes(mem)
    for i, name in enumerate(EVENT_NAMES, 1):
        commands = reference["events"][name]["commands"]
        for word in commands:
            index = mem[RING_HEAD] & 15
            mem[RING_HI + index] = int(word[:2], 16)
            mem[RING_LO + index] = int(word[2:], 16)
            mem[RING_HEAD] = (mem[RING_HEAD] + 1) & 15
        if i == 3:
            mem[0x009F] = 0x3C
        stages[NATIVE_DUMPS[i]] = bytes(mem)
    return stages


LOG = "\n".join(
    f"script f={frame} dump {name} ok"
    for frame, name in zip((506, 528, 550, 650), NATIVE_DUMPS)
) + "\n"


class NativeMenuSfxCommandsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(EXPECTED.read_text(encoding="utf-8"))

    def test_native_route_reuses_only_original_reference_events(self):
        route = build()
        self.assertIn("until 009F == D7 3600", route)
        self.assertIn("press down 2", route)
        self.assertIn("press up 2", route)
        self.assertIn("press a 2", route)
        self.assertEqual(route.count("dump e"), 4)
        self.assertEqual(route.count("quit"), 1)
        self.assertNotIn("poke ", route)

    def test_reference_sfx_identity_passes_exact_source_command_pairs(self):
        report = verify(snapshots(self.reference), LOG, self.reference)
        self.assertTrue(report["all_three_commands_match"])
        self.assertEqual(list(report["events"]), list(EVENT_NAMES))
        self.assertEqual([r["sfx_id"] for r in report["events"].values()],
                         [[3], [3], [2]])
        self.assertEqual(report["events"]["main_confirm_1p_slide"]["commands"],
                         ["084F", "0202"])

    def test_live_guest_authority_and_menu_state_fail_closed(self):
        good = snapshots(self.reference)
        bad = dict(good)
        bad["e01"] = bad["e01"][:-1]
        with self.assertRaisesRegex(ValueError, "128KiB"):
            verify(bad, LOG, self.reference)
        for log in (
            LOG.replace("script f=528", "script f=506"),
            LOG.replace("dump e02", "dump e99"),
            LOG.replace("script f=550", "script f=500"),
        ):
            with self.subTest(log=log), self.assertRaises(ValueError):
                verify(good, log, self.reference)
        broken = dict(good)
        mem = bytearray(good["e03"])
        mem[0x009F] = 0xD7
        broken["e03"] = bytes(mem)
        with self.assertRaisesRegex(ValueError, "stock frontend"):
            verify(broken, LOG, self.reference)

    def test_sfx_command_mutation_or_reference_swap_fails(self):
        actual = snapshots(self.reference)
        for name, slot, value in (
            ("e01", 1, 0x07), ("e02", 3, 0x09), ("e03", 5, 0x06)
        ):
            broken = dict(actual)
            mem = bytearray(actual[name])
            mem[RING_LO + slot] = value
            broken[name] = bytes(mem)
            with self.subTest(name=name), self.assertRaises(ValueError):
                verify(broken, LOG, self.reference)
        ref = dict(self.reference)
        ref["all_checks_pass"] = False
        with self.assertRaisesRegex(ValueError, "untrusted"):
            verify(actual, LOG, ref)

    def test_workflow_owns_native_provenance_and_not_a_new_gha_job(self):
        wf = (ROOT / ".github/workflows/windows-native-audio-output.yml").read_text()
        self.assertIn("build_native_menu_sfx_route.py", wf)
        self.assertIn("check_native_menu_sfx_commands.py", wf)
        self.assertIn("analysis/generated/menu-sfx-ids.json", wf)
        self.assertIn("audio-menu-sfx-native-report.json", wf)
        self.assertIn("SNESRECOMP_DUMP_DIR=", wf)
        self.assertIn('rm -f "$PCM"', wf)


if __name__ == "__main__":
    unittest.main()
