#!/usr/bin/env python3
"""ROM-free negative path contracts for the two-native-created-player journey.

Synthetic log strings test the witness parser only, never confer release or
source execution proof. Windows job must run the real executable to pass.
"""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_native_player_created_2p_records_probe as flow
from baldosa_native_2p_records_probe import (
    source_match_published, source_paired_records_reopened,
)


def played() -> str:
    return (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike\n"
        "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2\n"
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1\n"
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2\n"
        "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\n"
        "UR_BALDOSA_NATIVE_MATCH CAPTURED=1 profile1=mike "
        "profile2=martin course=course:01 frames=40000 path=pair.urrun\n"
        "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p "
        "race_host=1900 result_host=39700 riders=0,2 "
        "hundredths=2900,60000 winner=1 "
        "input_frames=37799 input_runs=6 published=1\n"
    )


def records(profile: str) -> str:
    return (
        f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={profile} "
        f"root=saves/profile-{profile}\n"
        "UR_BALDOSA_MODERN_ROOT records_page=1p\n"
        "UR_BALDOSA_MODERN_ROOT records_opened=1 "
        "profile=selected validated=0 unavailable=0\n"
        "UR_BALDOSA_MODERN_ROOT matches_readonly=1 paired=1 "
        "unavailable=0 selected=1\n"
        "UR_BALDOSA_MODERN_ROOT records_page=2p\n"
        "UR_BALDOSA_MODERN_ROOT records_last_2p=LAST 01 WIN 00:29.00 "
        "source=historical_paired_archive\n"
        "UR_BALDOSA_MODERN_ROOT records_page=1p\n"
        "UR_BALDOSA_MODERN_ROOT records_closed=1\n"
    )


class NativePlayerCreated2PJourneyUnit(unittest.TestCase):
    def test_martin_ui_creator_reuses_exact_original_stock_picker_and_drive(self):
        script = flow.source_martin_match_script()
        self.assertEqual(script, flow.source_match_script())
        self.assertIn("press p2:down 2\nwait 30\n", script)
        self.assertIn("until16 0053 == 8610", script)
        self.assertIn("until 0E1F != 00", script)
        self.assertTrue(script.endswith("dump after-source-2p-drive\nquit\n"))
        self.assertNotIn("write ", script.lower())

    def test_legacy_anonymous_bootstrap_is_never_named_save_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            user = Path(directory)
            anon = user / "saves" / "save.srm"
            self.assertIsNone(flow.anonymous_bootstrap_sram(user))
            flow.require_legacy_untouched(user, None)
            anon.parent.mkdir()
            original = bytes(range(256)) * 32
            anon.write_bytes(original)
            flow.require_legacy_untouched(user, original)
            with self.assertRaisesRegex(ValueError, "after bootstrap"):
                flow.require_legacy_untouched(user, None)
            anon.write_bytes(bytes(8192))
            with self.assertRaisesRegex(ValueError, "after bootstrap"):
                flow.require_legacy_untouched(user, original)
            anon.write_bytes(b"short")
            with self.assertRaisesRegex(ValueError, "8192"):
                flow.require_legacy_untouched(user, original)
            anon.unlink()
            anon.symlink_to(user / "private-save.srm")
            with self.assertRaisesRegex(ValueError, "symlink"):
                flow.require_legacy_untouched(user, original)

    def test_second_preset_changed_through_real_root_modal_not_fixture(self):
        from baldosa_native_second_racer_probe import require_p2_creation
        receipt = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
            "root=saves/profile-mike\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT second_racer_opened=1 preset=1 "
            "activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT second_racer_preset=2\n"
            "UR_BALDOSA_NATIVE_SECOND_RACER status=0 preset=2 "
            "id=martin activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT second_racer_created=1 "
            "activation=next_process\n"
        )
        require_p2_creation(receipt, preset=2)
        for bad in (
            receipt.replace("second_racer_preset=2", "second_racer_preset=3"),
            receipt.replace("id=martin", "id=andrew"),
            receipt.replace("status=0", "status=3"),
            receipt.replace("profile=mike", "profile=martin"),
            receipt + receipt,
        ):
            with self.subTest(log=bad[-90:]), self.assertRaises(ValueError):
                require_p2_creation(bad, preset=2)
        root = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        self.assertIn("UR_BALDOSA_SECOND_RACER_TEST_PRESET", root)
        self.assertIn("source_martin && frame == 61 ? SDLK_DOWN", root)

    def test_player_pair_requires_source_settled_result_not_fixture(self):
        args = dict(p1_profile="mike", p2_profile="martin",
                    p1_rider=0, p2_rider=2)
        self.assertEqual(
            source_match_published(played(), **args)["source_result_host"],
            39700)
        for bad in (
            played().replace("riders=0,2", "riders=0,1"),
            played().replace("profile2=martin", "profile2=mike"),
            played().replace("published=1", "published=0"),
            played().replace("course=course:01", "course=course:02"),
            played().replace("join_confirmed seat=2", "join_confirmed seat=1"),
            played() + played(),
        ):
            with self.subTest(log=bad[-90:]), self.assertRaises(ValueError):
                source_match_published(bad, **args)

    def test_each_player_must_reopen_exactly_one_readonly_pair(self):
        for identity in ("mike", "martin"):
            source_paired_records_reopened(
                records(identity), selected_profile=identity)
            for bad in (
                records(identity).replace("paired=1", "paired=0"),
                records(identity).replace("selected=1", "selected=0"),
                records(identity) + records(identity),
                records(identity) + "UR_BALDOSA_NATIVE_MATCH CAPTURED=1\n",
            ):
                with self.subTest(identity=identity, log=bad[-80:]):
                    with self.assertRaises(ValueError):
                        source_paired_records_reopened(
                            bad, selected_profile=identity)

    def test_existing_product_store_remains_sole_next_boot_authority(self):
        fixture = (ROOT / "tools/baldosa_modern_profile_native_fixture.cpp"
                   ).read_text(encoding="utf-8")
        probe = (ROOT / "tools/baldosa_native_player_created_2p_records_probe.py"
                 ).read_text(encoding="utf-8")
        self.assertIn("select_baldosa_existing_profile_for_next_boot", fixture)
        self.assertIn('"--select-existing-next-boot"', fixture)
        self.assertNotIn("--add-second-keep-first", probe)
        self.assertNotIn("--seed-readonly-records", probe)
        self.assertNotIn("--seed-readonly-2p", probe)
        self.assertIn("native_existing_p1_profile_selector_UI_proved", probe)
        self.assertIn('require_switch(ui_switch, P1, P2)', probe)
        self.assertIn('"mike_ui_selects_martin", "7"', probe)
        self.assertIn('synthetic_p1_switch_gamepad=', probe)
        root = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        self.assertIn('std::strcmp(opt, "7") == 0', root)
        self.assertIn('ur_baldosa_modern_root_gamepad(0, button, 1)', root)
        self.assertIn('kGamepadBtn_X', root)
        self.assertIn('kGamepadBtn_B', root)
        self.assertNotIn('subprocess.run(', probe)
        self.assertNotIn('"--select-existing-next-boot"', probe)


if __name__ == "__main__":
    unittest.main()
