"""Guard both sides of the real SNESRecomp P2 mapped-word seam."""
import hashlib
import json
import pathlib
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PATCH_PATH = ROOT / "tools/patches/snesrecomp-title-p2-input-filter.patch"
MANIFEST = ROOT / "tools/toolchain-entries/snesrecomp.json"
AUTHORITATIVE_MANIFEST = ROOT / "tools/toolchain.json"
HOST = ROOT / "native/product/uniracers_modern_host.cpp"
HEADER = ROOT / "native/product/uniracers_modern_host.h"
SCAFFOLD = ROOT / "tools/patch_modern_product_host.py"


def _parse_unified(patch):
    """Return {path: [(old_start, hunk_lines)]} for a unified diff."""
    files = {}
    current = None
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            current = files.setdefault(line[6:].strip(), [])
        elif line.startswith("--- "):
            continue
        elif line.startswith("@@"):
            start = int(re.match(r"@@ -(\d+)", line).group(1))
            current.append((start, []))
        elif current:
            current[-1][1].append(line if line else " ")
    return files


class P2GuestWordHostContract(unittest.TestCase):
    def test_pinned_framework_patch_order_and_checksum(self):
        # tools/toolchain.json is what bootstrap_toolchain.py actually applies;
        # the per-tool entry is a derived snapshot. #981 registered the patch
        # only in the snapshot, so no build ever applied it.
        authoritative = next(
            tool for tool in json.loads(AUTHORITATIVE_MANIFEST.read_text())["tools"]
            if tool["id"] == "snesrecomp")
        snapshot = json.loads(MANIFEST.read_text())
        self.assertEqual(authoritative["patches"], snapshot["patches"])
        for manifest in (authoritative, snapshot):
            patches = [p["path"] for p in manifest["patches"]]
            name = "tools/patches/snesrecomp-title-p2-input-filter.patch"
            self.assertEqual(patches.count(name), 1)
            self.assertGreater(patches.index(name), patches.index(
                "tools/patches/snesrecomp-title-input-filter.patch"))
            self.assertEqual(
                manifest["patches"][patches.index(name)]["sha256"],
                hashlib.sha256(PATCH_PATH.read_bytes()).hexdigest())

    def test_derived_toolchain_snapshots_match_authoritative_manifest(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/export_toolchain_entries.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_host_scaffold_patcher_is_importable(self):
        # A SyntaxError here broke every native build after #981.
        py_compile.compile(str(SCAFFOLD), doraise=True)

    def test_framework_patch_applies_with_git_apply_and_composes_p2_word(self):
        patch = PATCH_PATH.read_text()
        self.assertIn("g_game->filter_second_player_input(p2_human)", patch)
        self.assertIn("((human >> 12) & 0x0fffu)", patch)
        self.assertIn("(g_gamepad[1].axis_buttons & 0x0fffu)", patch)
        self.assertIn("((p2_human & 0x0fffu) << 12)", patch)
        self.assertIn("uint32_t (*filter_second_player_input)(uint32_t inputs);", patch)
        if not shutil.which("git") or not shutil.which("cc"):
            self.skipTest("requires git and a C compiler")
        # Reconstruct the pre-image purely from the patch's own context and
        # removed lines at their recorded line numbers, then apply it with the
        # same `git apply --check` + `git apply` bootstrap_toolchain.py uses.
        # A hunk without usable context (the #981 form) cannot pass this.
        with tempfile.TemporaryDirectory() as temp:
            temp_path = pathlib.Path(temp)
            hunks = _parse_unified(patch)
            self.assertEqual(sorted(hunks), [
                "runner/src/desktop/host_main.c", "runner/src/desktop/host_main.h"])
            for rel, file_hunks in hunks.items():
                for start, lines in file_hunks:
                    context = [l for l in lines if l.startswith(" ")]
                    self.assertGreaterEqual(
                        len(context), 2, f"{rel}: hunk needs real context lines")
                    del start
            directory = temp_path / "runner/src/desktop"
            directory.mkdir(parents=True)
            prelude_h = [
                "#pragma once", "#include <stdint.h>", "typedef struct {",
            ]
            (start_h, lines_h), = hunks["runner/src/desktop/host_main.h"]
            pre_h = [l[1:] for l in lines_h if l[:1] in " -"]
            # The header hunk's leading context is the tail of a block comment.
            body_h = (prelude_h + ["/* pad */"] * (start_h - 2 - len(prelude_h))
                      + ["  /* reconstructed comment head"] + pre_h)
            body_h += ["   * seam. */", "  int unused_tail;", "} Game;",
                       "extern Game *g_game;"]
            (directory / "host_main.h").write_text("\n".join(body_h) + "\n")
            prelude_c = [
                '#include "host_main.h"', "typedef uint32_t uint32;",
                "typedef struct { uint8_t axis_buttons; } Pad;",
                "static Pad g_gamepad[2];", "static Game game_object;",
                "Game *g_game = &game_object;",
                "static uint32 filter_p2(uint32 p2) { return p2 & ~0x010u; }",
                "static uint32 compose(uint32 human) {",
            ]
            (start_c, lines_c), = hunks["runner/src/desktop/host_main.c"]
            pre_c = [l[1:] for l in lines_c if l[:1] in " -"]
            body_c = prelude_c + ["/* pad */"] * (start_c - 1 - len(prelude_c)) + pre_c
            body_c += [
                "     * end of reconstructed context */",
                "    return inputs;", "}",
                "int main(void) {",
                "    g_gamepad[1].axis_buttons = 0x020u;",
                "    /* No filter bound: must equal the stock composition. */",
                "    if (compose(0xa5000000u | (0x010u << 12) | 0x456u) !=",
                "        (0xa5000000u | (0x030u << 12) | 0x456u)) return 2;",
                "    g_game->filter_second_player_input = filter_p2;",
                "    /* Mapped P2 A (0x010) is filtered; axis bit and P1/top byte kept. */",
                "    return compose(0xa5000000u | (0x010u << 12) | 0x456u) ==",
                "        (0xa5000000u | (0x020u << 12) | 0x456u) ? 0 : 1;", "}",
            ]
            (directory / "host_main.c").write_text("\n".join(body_c) + "\n")
            subprocess.run(["git", "init", "-q"], cwd=temp, check=True)
            for args in (["git", "apply", "--check", str(PATCH_PATH)],
                         ["git", "apply", str(PATCH_PATH)]):
                result = subprocess.run(args, cwd=temp, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("p2_human = ((human >> 12)",
                          (directory / "host_main.c").read_text())
            executable = temp_path / "p2-composition"
            subprocess.run(
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
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
