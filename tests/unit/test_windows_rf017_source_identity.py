"""Regression guard for the actual shipping Win32 native source timing identity.

#1686: Linux QA-01 includes RF-017 but the Windows bridge previously compiled
RF-015-only committed game code. An exact-ELF original/native result cannot
certify the Windows executable when these generator sources differ.

This cheap static guard accompanies the *real* Windows step, which regenerates
the guest and proves 89 files / 15,484 reordered charges with unchanged block
totals. It does not claim a Win32 original/native complete event.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WINDOWS = ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"


def assert_windows_rf017_contract(source: str) -> None:
    stage = source.split("      - name: Stage only the verified UR native boundary\n", 1)
    if len(stage) != 2:
        raise AssertionError("Windows staging step renamed, missing or duplicated")
    body = stage[1].split("\n      - name:", 1)[0]
    steps = (
        "python tools/baldosa_dram_refresh_beam_rate_patch.py --game baldosa",
        "python tools/baldosa_io_access_clock_order_patch.py --game baldosa",
        "bash tools/regen.sh --cfg-roots",
        'python tools/baldosa_io_access_clock_order_patch.py \\\n            --game baldosa --verify-gen',
        "15484 in-order charge statements, every block total unchanged",
        "python tools/baldosa_guest_adapter_spike.py --game baldosa",
    )
    indexes = [body.find(step) for step in steps]
    if any(index < 0 for index in indexes) or indexes != sorted(indexes):
        raise AssertionError("RF-015/RF-017 generation, exact verification and host adapter must remain ordered")
    if '--rom "$GITHUB_WORKSPACE/reference/roms/retail/Uniracers_USA.sfc"' not in body:
        raise AssertionError("regeneration must use the pinned original USA ROM")
    if "grep -Fx 'verified 89 generated files:" not in body:
        raise AssertionError("generator output must fail closed on count or clock-total changes")
    if not body.count("--verify-gen") == 1:
        raise AssertionError("must verify the actual post-regeneration files exactly once")
    if "baldosa_dp_indirect_long_pointer_once_patch" in body or "baldosa_spc_bus_cycle_patch" in body:
        raise AssertionError("research-only RF-018..028 cannot silently become shipping source")


class WindowsRF017SourceIdentityTests(unittest.TestCase):
    def test_actual_windows_build_rebuilds_exact_rf017_game_source(self):
        assert_windows_rf017_contract(WINDOWS.read_text(encoding="utf-8"))

    def test_guard_rejects_rf015_only_and_unverified_regeneration(self):
        source = WINDOWS.read_text(encoding="utf-8")
        for missing in (
            "python tools/baldosa_io_access_clock_order_patch.py --game baldosa",
            "bash tools/regen.sh --cfg-roots",
            "--verify-gen",
            "15484 in-order charge statements, every block total unchanged",
        ):
            with self.subTest(missing=missing):
                with self.assertRaises(AssertionError):
                    assert_windows_rf017_contract(source.replace(missing, "REMOVED", 1))

    def test_guard_rejects_generator_after_host_bridge(self):
        source = WINDOWS.read_text(encoding="utf-8")
        stage = "python tools/baldosa_guest_adapter_spike.py --game baldosa"
        moved = source.replace("          " + stage + '\n', '', 1)
        moved = moved.replace(
            '          # No second native core, ROM or alternate product frontend.',
            '          ' + stage + '\n          # No second native core, ROM or alternate product frontend.',
            1,
        )
        with self.assertRaises(AssertionError):
            assert_windows_rf017_contract(moved)


if __name__ == "__main__":
    unittest.main()
