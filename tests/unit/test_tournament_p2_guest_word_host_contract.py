"""Guard both sides of the real SNESRecomp P2 mapped-word seam."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PATCH_PATH = ROOT / "tools/patches/snesrecomp-title-p2-input-filter.patch"
MANIFEST = ROOT / "tools/toolchain-entries/snesrecomp.json"
HOST = ROOT / "native/product/uniracers_modern_host.cpp"
HEADER = ROOT / "native/product/uniracers_modern_host.h"
SCAFFOLD = ROOT / "tools/patch_modern_product_host.py"


class P2GuestWordHostContract(unittest.TestCase):
    def test_pinned_framework_patch_order_and_checksum(self):
        manifest = json.loads(MANIFEST.read_text())
        patches = [p["path"] for p in manifest["patches"]]
        name = "tools/patches/snesrecomp-title-p2-input-filter.patch"
        self.assertEqual(patches.count(name), 1)
        self.assertGreater(patches.index(name), patches.index(
            "tools/patches/snesrecomp-title-input-filter.patch"))
        self.assertEqual(
            manifest["patches"][patches.index(name)]["sha256"],
            hashlib.sha256(PATCH_PATH.read_bytes()).hexdigest())

    def test_framework_patch_can_be_applied_to_exact_source_seams(self):
        patch = PATCH_PATH.read_text()
        self.assertIn("g_gamepad[1].axis_buttons", patch)
        self.assertIn("g_game->filter_second_player_input(p2_human)", patch)
        self.assertIn("((human >> 12) & 0x0fffu)", patch)
        self.assertIn("(g_gamepad[1].axis_buttons & 0x0fffu)", patch)
        self.assertIn("((p2_human & 0x0fffu) << 12)", patch)
        self.assertIn("uint32_t (*filter_second_player_input)(uint32_t inputs);", patch)
        if not shutil.which("patch") or not shutil.which("cc"):
            self.skipTest("requires POSIX patch and C compiler")
        with tempfile.TemporaryDirectory() as temp:
            directory = pathlib.Path(temp) / "runner/src/desktop"
            directory.mkdir(parents=True)
            (directory / "host_main.h").write_text(
                "#pragma once\n#include <stdint.h>\n"
                "typedef struct {\n"
                "  uint32_t (*filter_player_input)(uint32_t inputs);\n"
                "\n"
                "  /* Optional title-owned source-aware physical gamepad seam. The framework\n"
                "   * already exposes the source callback below. */\n"
                "} Game;\nextern Game* g_game;\n"
            )
            (directory / "host_main.c").write_text(
                '#include "host_main.h"\n'
                "#include <stdint.h>\n"
                "typedef uint32_t uint32;\n"
                "typedef struct { uint32 axis_buttons; } Pad;\n"
                "static Pad g_gamepad[2];\n"
                "static Game game_object;\n"
                "Game *g_game = &game_object;\n"
                "static uint32 filter_p2(uint32 p2) { return p2 & ~0x010u; }\n"
                "static uint32 compose(uint32 human) {\n"
                "    uint32 inputs = human | (g_gamepad[1].axis_buttons << 12);\n"
                "    return inputs;\n}\n"
                "int main(void) {\n"
                "    g_game->filter_second_player_input = filter_p2;\n"
                "    g_gamepad[1].axis_buttons = 0x020u;\n"
                "    const uint32 actual = compose(0xa5000000u | (0x010u << 12) | 0x456u);\n"
                "    const uint32 expected = 0xa5000000u | (0x020u << 12) | 0x456u;\n"
                "    return actual == expected ? 0 : 1;\n}\n"
            )
            # The patch uses the original framework line as its only hunk
            # context, deliberately independent of other host hunk offsets.
            result = subprocess.run(
                ["patch", "-p1", "--fuzz=0", "--batch", "--forward"], cwd=temp,
                input=patch, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("p2_human = ((human >> 12)",
                          (directory / "host_main.c").read_text())
            executable = pathlib.Path(temp) / "p2-composition"
            subprocess.run(
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 str(directory / "host_main.c"), "-o", str(executable)],
                cwd=temp, check=True)
            subprocess.run([str(executable)], cwd=temp, check=True)

    def test_tournament_open_arms_latch_without_requiring_guest_frame(self):
        host = HOST.read_text()
        start = host.index("bool open_local_tournament_panel()")
        end = host.index("void create_local_tournament_from_panel(", start)
        body = host[start:end]
        self.assertIn("tournament_p2_guest_arm()", body)
        self.assertLess(body.index("tournament_p2_guest_arm()"),
                        body.index("g_local_tournament_panel_visible = true"))
        pos = host.index("ur_uniracers_modern_filter_second_player_input(")
        filt = host[pos:host.index(
            'extern "C" uint32_t ur_uniracers_modern_filter_player_input(', pos)]
        self.assertIn("if (!modern_mode())", filt)
        self.assertIn("tournament_p2_guest_filter(", filt)
        self.assertIn("g_local_tournament_panel_visible", filt)
        self.assertIn("ur_uniracers_modern_filter_second_player_input(", HEADER.read_text())

    def test_scaffold_binds_p2_on_new_and_existing_projects(self):
        from tools.patch_modern_product_host import patch_main_text
        fresh = (
            '#include "snesrecomp_rom_identity.h"  /* generated from rom_identity.txt */\n'
            'static const SnesDesktopHostGame kHost = {\n'
            '    .game_info           = &kGameInfo,\n'
            '};\n'
        )
        old = (
            'static const SnesDesktopHostGame kHost = {\n'
            '    .game_info           = &kGameInfo,\n'
            '    .after_run_frame       = &ur_uniracers_modern_after_run_frame,\n'
            '    .system_key_down       = &ur_uniracers_modern_system_key_down,\n'
            '    .system_gamepad_button = &ur_uniracers_modern_system_gamepad_button,\n'
            '    .system_overlay         = &ur_uniracers_modern_system_overlay,\n'
            '};\n'
        )
        for source in (fresh, old):
            patched = patch_main_text(source)
            self.assertEqual(patched.count(
                ".filter_second_player_input = "
                "&ur_uniracers_modern_filter_second_player_input"), 1)
            self.assertEqual(patch_main_text(patched), patched)


if __name__ == "__main__":
    unittest.main()
