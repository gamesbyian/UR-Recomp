import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LocalTournamentHostQueryContract(unittest.TestCase):
    def test_c_consumers_can_use_bounded_read_only_abi(self):
        source = """
#include "uniracers_modern_host.h"
int tournament_panel(void) {
    struct UrModernTournamentOverview overview = {0};
    struct UrModernTournamentFixtureInfo fixture = {0};
    struct UrModernTournamentStandingInfo standing = {0};
    return ur_uniracers_modern_local_tournament_overview(&overview) +
           ur_uniracers_modern_local_tournament_fixture(0, &fixture) +
           ur_uniracers_modern_local_tournament_standing(0, &standing);
}
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "tournament_query_abi.c"
            path.write_text(source, encoding="utf-8")
            subprocess.run(
                [
                    "gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-fsyntax-only",
                    "-I", str(ROOT / "native/product"), str(path),
                ], cwd=ROOT, check=True
            )

    def test_product_projection_is_evidence_only_and_modern_only(self):
        text = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        start = text.index(
            'extern "C" int ur_uniracers_modern_local_tournament_overview('
        )
        query = text[start:]
        self.assertIn("ensure_local_tournament_session_loaded()", query)
        self.assertIn("local_tournament_coordinator_complete(", query)
        self.assertIn("local_tournament_standings(", query)
        self.assertIn("result.seats_swapped", query)
        self.assertEqual(query.count("!ensure_session() || !modern_mode()"), 3)
        for prohibited in (
            "append_multiplayer_match_pair(",
            "record_local_tournament_result(",
            "local_tournament_arm_fixture(",
            "persist_product_state(",
            "g_sram[",
            "g_ram[",
        ):
            self.assertNotIn(prohibited, query)


if __name__ == "__main__":
    unittest.main()
