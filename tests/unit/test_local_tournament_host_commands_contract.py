import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LocalTournamentHostCommandsContract(unittest.TestCase):
    def test_c_abi_accepts_explicit_roster_courses_and_fixture_selection(self):
        code = """
#include "uniracers_modern_host.h"
int create_tournament(void) {
    const char *participants[] = {"alice", "bob"};
    const char *courses[] = {"course:01", "course:04"};
    struct UrModernTournamentOverview overview = {0};
    int created = ur_uniracers_modern_local_tournament_create(
        participants, 2, courses, 2, 0);
    int armed = ur_uniracers_modern_local_tournament_arm_fixture(0);
    int cancelled = ur_uniracers_modern_local_tournament_cancel_fixture();
    return created + armed + cancelled +
        ur_uniracers_modern_local_tournament_overview(&overview);
}
"""
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "tournament_commands.c"
            target.write_text(code, encoding="utf-8")
            subprocess.run(
                [
                    "gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-fsyntax-only", "-I",
                    str(ROOT / "native/product"), str(target),
                ], check=True, cwd=ROOT,
            )

    def test_commands_are_modern_frontend_only_and_use_real_authority(self):
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn('#include "local_tournament_tokens.hpp"', host)
        start = host.index("bool local_tournament_command_context()")
        commands = host[start:]
        for authority in (
            "ensure_session() && modern_mode()",
            "g_ram[0x009F] == 0xD7",
            "g_ram[0x0313] != 0x01",
            "g_multiplayer_run_capture.capturing()",
            "ensure_profile_catalog()",
            "create_local_tournament_coordinator(",
            "arm_local_tournament_fixture(",
            "cancel_local_tournament_capture(",
            "mint_local_tournament_token()",
            "local_tournament_bounded_c_string(",
            "g_local_tournament_session->launch.pending",
        ):
            self.assertIn(authority, commands)
        self.assertIn("product_diagnostic(\"UR_LOCAL_TOURNAMENT CREATED\")", commands)
        self.assertIn("product_diagnostic(\"UR_LOCAL_TOURNAMENT FIXTURE_ARMED\")", commands)
        self.assertIn("product_diagnostic(\"UR_LOCAL_TOURNAMENT FIXTURE_CANCELLED\")", commands)
        for forbidden in (
            "g_sram[", "g_ram[0x1199]", "append_multiplayer_match_pair(",
            "RtlSetSaveRoot(", "snesrecomp_desktop_arm_relative_input(",
            "local_multiplayer_assign(", "run_record_capture.",
            "record_local_tournament_result(",
        ):
            self.assertNotIn(forbidden, commands)

    def test_creation_and_route_lifecycle_remain_separate(self):
        header = (ROOT / "native/product/uniracers_modern_host.h").read_text(
            encoding="utf-8"
        )
        self.assertIn("The API never", header)
        self.assertIn("The stock 2P join surface must", header)
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        create = host.index(
            'extern "C" int ur_uniracers_modern_local_tournament_create('
        )
        arm = host.index(
            'extern "C" int ur_uniracers_modern_local_tournament_arm_fixture('
        )
        cancel = host.index(
            'extern "C" int ur_uniracers_modern_local_tournament_cancel_fixture('
        )
        self.assertLess(create, arm)
        self.assertLess(arm, cancel)
        self.assertLess(arm, len(host))
        self.assertIn("local_tournament_capture_attempt_for(", host[:create])
        self.assertIn("commit_local_tournament_capture(", host[:create])


if __name__ == "__main__":
    unittest.main()
