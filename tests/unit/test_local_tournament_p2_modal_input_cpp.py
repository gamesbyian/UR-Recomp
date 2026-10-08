import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native/product/uniracers_modern_host.cpp"


class TournamentP2ModalInputTests(unittest.TestCase):
    def test_real_source_callback_uses_p2_modal_policy(self):
        source = HOST.read_text(encoding="utf-8")
        begin = source.index("ur_uniracers_modern_system_gamepad_source_button(")
        end = source.index('extern "C" int ur_uniracers_modern_system_gamepad_button(', begin)
        function = source[begin:end]
        self.assertIn("if (player_index == 1)", function)
        self.assertIn("tournament_p2_modal_input(", function)
        self.assertIn("g_local_tournament_panel_visible", function)
        self.assertIn("g_local_multiplayer_consumed_buttons[seat] = policy.consumed_buttons", function)
        self.assertIn("if (policy.consume_event) return 1;", function)

    def test_edge_masks_and_release_lifecycle(self):
        with tempfile.TemporaryDirectory() as directory:
            exe = pathlib.Path(directory) / "tournament-p2-modal-test"
            subprocess.run(
                ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-I", str(ROOT / "native/product"),
                 str(ROOT / "tests/native/local_tournament_p2_modal_input_test.cpp"),
                 "-o", str(exe)],
                cwd=ROOT, check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
