import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class BaldosaModernUtf8PathContractTests(unittest.TestCase):
    def test_native_profile_and_records_boundaries_are_utf8(self):
        source = (ROOT / "tools" / "baldosa_modern_profile_activation.cpp").read_text(encoding="utf-8")
        self.assertIn('#include "local_tournament_utf8_path.hpp"', source)
        for raw in ("root", "user_root", "post_raw_gate", "before_switch_gate"):
            self.assertIn(f"host_native_path_from_utf8(std::string({raw}))", source)
        # Native filesystem paths passed to public product APIs, lock owners,
        # and C-facing Records getters must never be encoded in the ACP.
        self.assertNotIn(".string()", source)
        for suffix in ('"multiplayer-runs").u8string()',
                       '"profiles-v1.txt").u8string()',
                       'g_verified_native_profile_id).u8string()',
                       'directory.u8string(), *run',
                       'archive.u8string(), *run, *match'):
            self.assertIn(suffix, source)

    def test_native_fixture_exercises_non_ansi_root_and_records_getters(self):
        fixture = (ROOT / "tests/native/baldosa_modern_profile_activation_test.cpp").read_text(encoding="utf-8")
        self.assertIn('u8"-路径-🌈"', fixture)
        for symbol in ("ur_baldosa_modern_profile_records_directory()",
                       "ur_baldosa_modern_profile_multiplayer_records_directory()",
                       "ur_baldosa_modern_profile_catalog_path()"):
            self.assertIn(symbol, fixture)


if __name__ == "__main__":
    unittest.main()
