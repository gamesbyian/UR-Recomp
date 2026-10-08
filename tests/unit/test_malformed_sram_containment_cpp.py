import pathlib
import re
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native" / "product"
TITLE = ROOT / "native" / "title"
HOST = (PRODUCT / "uniracers_modern_host.cpp").read_text(encoding="utf-8")
ROM = ROOT / "reference" / "roms" / "retail" / "Uniracers_USA.sfc"
CLEAN = ROOT / "reference/imported/reverse-engineering/dessyreqt/SRAM/Clean.srm"


def function_body(name: str) -> str:
    start = HOST.index(name)
    end = HOST.index("\n}\n", start)
    return HOST[start:end]


class MalformedSramContainmentCppTests(unittest.TestCase):
    def test_host_layer_classes(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "malformed-sram-containment"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(PRODUCT), "-I", str(TITLE),
                    str(PRODUCT / "host_product_state.cpp"),
                    str(PRODUCT / "output_resolution_policy.cpp"),
                    str(PRODUCT / "modern_racer_identity.cpp"),
                    str(PRODUCT / "clean_stock_sram.cpp"),
                    str(PRODUCT / "host_profile_state.cpp"),
                    str(PRODUCT / "host_profile_store.cpp"),
                    str(PRODUCT / "host_profile_ghost_target.cpp"),
                    str(TITLE / "uniracers_tour_resume.cpp"),
                    str(ROOT / "tests" / "native" / "malformed_sram_containment_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            run = subprocess.run(
                [str(exe), tmp], cwd=ROOT, check=True, capture_output=True, text=True
            )
        for cls in (
            "wrong_size", "checksum_mismatch", "out_of_range_values",
            "tour_flag_play_mode", "damaged_signature",
        ):
            self.assertIn(f"MALFORMED_SRAM_HOST class={cls} ", run.stdout)

    def test_signature_prefix_is_the_rom_bytes_the_stock_boot_compares(self):
        # 80:8C4E compares six SRAM words with ROM 83:8000 (LoROM file 0x18000).
        rom = ROM.read_bytes()
        self.assertEqual(rom[0x18000:0x1800C], b"ASJIver3.30\xff")
        self.assertEqual(CLEAN.read_bytes()[:12], rom[0x18000:0x1800C])
        # LDX #0; LDY #5; LDA $770000,X; CMP $838000,X (80:8C5D..8C67).
        boot_check = bytes.fromhex("a20000a00500bf000077df008083")
        self.assertEqual(rom[0x0C5D:0x0C5D + len(boot_check)], boot_check)
        header = (PRODUCT / "clean_stock_sram.hpp").read_text(encoding="utf-8")
        self.assertIn("kStockSramFormatSignatureBytes = 12;", header)

    def test_live_install_paths_apply_the_stock_format_check_first(self):
        activate = function_body("bool activate_profile_id(")
        guard = activate.index("stock_sram_format_signature_present(")
        self.assertLess(activate.index("REJECTED_METADATA"), guard)
        self.assertLess(guard, activate.index("persist_live_profile_snapshot()"))
        self.assertLess(guard, activate.index("restore_stock_sram_from_profile("))
        self.assertIn("UR_PROFILE_SELECT REJECTED_UNFORMATTED_SNAPSHOT", activate)

        rollback = function_body("bool rollback_tour_entry_to_profile_snapshot(")
        self.assertLess(
            rollback.index("stock_sram_format_signature_present("),
            rollback.index("restore_stock_sram_from_profile("),
        )
        # Every live install of a profile mirror goes through one of the two
        # guarded paths; Reset Progress installs the formatted clean image.
        self.assertEqual(len(re.findall(r"restore_stock_sram_from_profile\(", HOST)), 2)


if __name__ == "__main__":
    unittest.main()
