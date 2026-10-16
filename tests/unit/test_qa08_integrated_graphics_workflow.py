"""Graphics draft must retain integrated Windows production and manual-only source capture."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"


def step(text: str, name: str) -> str:
    marker = "      - name: " + name + "\n"
    if text.count(marker) != 1:
        raise AssertionError(f"missing or duplicated workflow step: {name}")
    after = text.split(marker, 1)[1]
    return after.split("\n      - name: ", 1)[0]


class IntegratedGraphicsWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.source = WORKFLOW.read_text(encoding="utf-8")

    def test_current_main_windows_reproducibility_and_player_journeys_survive(self):
        s = self.source
        self.assertIn("fetch_toolchain.sh --artifact windows-x64 --tag v1.0.14", s)
        self.assertIn("export SOURCE_DATE_EPOCH=", s)
        self.assertIn("python tools/check_windows_pe_timestamp.py", s)
        self.assertIn("Native Options change, restore, defaults and damaged settings across four games", s)
        self.assertIn("Native Practice enters ten original courses across both unlock states", s)
        self.assertIn("Retain bounded extracted-CMD source transcripts separately", s)
        self.assertIn("Assemble verified ROM-free Baldosa Modern Windows candidate", s)
        self.assertIn("Bind journeys to the nominated ZIP and executable hashes", s)

    def test_ordered_title_only_raster_staging_inside_single_real_windows_build(self):
        s = self.source
        order = (
            "python tools/baldosa_dram_refresh_beam_rate_patch.py --game baldosa",
            "python tools/baldosa_uniracers_hdma_firstline_patch.py --game baldosa --apply-candidate",
            "python tools/baldosa_uniracers_v0_raster_before_hdma_patch.py --game baldosa --apply-candidate",
            "python tools/baldosa_uniracers_brightness_pixel_lut_patch.py --game baldosa --apply-candidate",
            "python tools/baldosa_qa08_native_ppu_register_trace_patch.py --game baldosa --apply-candidate",
            "python tools/baldosa_qa08_native_cgram_port_chronology_patch.py --game baldosa --apply-candidate",
            "python tools/baldosa_qa08_native_inidisp_port_trace_patch.py --game baldosa --apply-candidate",
            "python tools/baldosa_guest_adapter_spike.py --game baldosa",
            "python tools/baldosa_product_pause_spike.py --game baldosa",
            "python tools/baldosa_qa08_windows_source_capture_patch.py --game baldosa",
            "python tools/baldosa_modern_options_spike.py --game baldosa",
            "cmake -S baldosa -B baldosa/build-ur-win",
        )
        cursor = -1
        for name in order:
            self.assertEqual(s.count(name), 1 if "--apply-candidate" in name else s.count(name))
            index = s.find(name, cursor + 1)
            self.assertGreater(index, cursor, f"staging misordered: {name}")
            cursor = index
        self.assertIn("test \"$(git -C baldosa/snesrecomp rev-parse HEAD)\"", s)

    def test_archival_graphics_capture_manual_only_and_all_57344_pixels(self):
        s = self.source
        self.assertIn("      qa08_source_capture:\n", s)
        self.assertIn("        default: false\n", s)
        manual = "if: ${{ github.event_name == 'workflow_dispatch' && inputs.qa08_source_capture }}"
        manual_upload = "if: ${{ always() && github.event_name == 'workflow_dispatch' && inputs.qa08_source_capture }}"
        for name in (
            "Capture original 2P PPU from same corrected Windows executable",
            "Observe race entry, moving camera, and result/return in real 1P Windows PPU",
            "Capture authentic split-screen 2P race, results and menu return",
        ):
            self.assertIn(manual, step(s, name))
        for name in (
            "Preserve real Windows PPU raster evidence even on negative result",
            "Retain bounded genuine 1P Windows PPU source and phase receipt",
            "Retain real Windows two-pad 2P split and terminal source images",
        ):
            self.assertIn(manual_upload, step(s, name))
        self.assertNotIn("github.event.pull_request.number == 1641", s)
        self.assertIn("python tools/qa08_windows_full_oneplayer_source_coverage.py", s)
        self.assertIn("python tools/qa08_windows_full_twoplayer_source_coverage.py", s)

    def test_graphics_invalidations_and_unit_guard_are_explicit(self):
        s = self.source
        self.assertIn('      - "tools/baldosa_uniracers_hdma_firstline_patch.py"', s)
        self.assertIn('      - "tools/baldosa_uniracers_v0_raster_before_hdma_patch.py"', s)
        self.assertIn('      - "tests/unit/test_qa08_integrated_graphics_workflow.py"', s)
        self.assertEqual(s.count("python tests/unit/test_qa08_integrated_graphics_workflow.py"), 1)


if __name__ == "__main__":
    unittest.main()
