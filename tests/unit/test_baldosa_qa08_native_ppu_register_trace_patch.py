"""Exact active-legacy source-only INIDISP/CGRAM probe, never a PPU fix."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import baldosa_qa08_native_ppu_register_trace_patch as state
import baldosa_uniracers_brightness_pixel_lut_patch as brightness


class RealNativePpuRegisterTraceTest(unittest.TestCase):
    def setUp(self):
        self.source=(
            "#include <stdint.h>\n#include <stdbool.h>\n#include \"snes.h\"\n"
            +state.ENTRY+"  for (int x=0;x<256;++x) {}\n}\n"
            +brightness.LEGACY_MARK+"\n"
        )

    def test_probe_is_after_exact_pinned_brightness_semantics(self):
        changed=state.patch_source(self.source)
        self.assertEqual(state.patch_source(changed),changed)
        self.assertEqual(changed.count(state.MARK),1)
        self.assertIn('getenv("UR_QA08_WINDOWS_PPU_STATE_TRACE")',changed)
        self.assertIn("const int frame = snes_frame_counter",changed)
        self.assertIn("PPU_brightness(ppu)",changed)
        self.assertIn("ppu->cgram[j]",changed)
        self.assertIn("ppu->cgram[0x6c]",changed)
        self.assertIn("ppu->cgram[0x6f]",changed)
        self.assertIn("cg6c=%04x cg6d=%04x cg6e=%04x cg6f=%04x",changed)
        self.assertIn("line == 112 || line == 114",changed)
        self.assertEqual(changed.replace(state.TRACE,"")
                         .replace("#include <stdio.h>\n#include <stdlib.h>\n",""),self.source)

    def test_unqualified_or_tampered_source_and_shared_cpu_rejected(self):
        for bad in (self.source.replace(brightness.LEGACY_MARK,""),
                    self.source.replace(state.ENTRY,"void unrelated() {}\n"),
                    self.source+self.source,
                    state.patch_source(self.source).replace(
                        "const int frame = snes_frame_counter",
                        "const int frame = 0")):
            with self.subTest(source=bad[:80]),self.assertRaises(ValueError):
                state.patch_source(bad)

    def test_exact_other_title_pin_rejected_without_any_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            p=root/state.RELATIVE
            p.parent.mkdir(parents=True)
            p.write_text(self.source)
            (root/"src/gen").mkdir(parents=True)
            (root/"src/gen/dispatch_v2.c").write_text("guest")
            with patch.object(state,"pinned_revision",side_effect=["other",state.CORE_REV]):
                with self.assertRaisesRegex(ValueError,"game"):
                    state.apply_game(root,write=True)
            self.assertEqual(p.read_text(),self.source)
            with patch.object(state,"pinned_revision",
                              side_effect=[state.GAME_REV,state.CORE_REV]):
                state.apply_game(root,write=True)
            self.assertEqual(p.read_text(),state.patch_source(self.source))

    def test_real_windows_source_probe_only_in_2p_qa_route(self):
        wf=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertEqual(wf.count(
            "python tools/baldosa_qa08_native_ppu_register_trace_patch.py --game baldosa --apply-candidate"),1)
        self.assertLess(wf.index("python tools/baldosa_uniracers_brightness_pixel_lut_patch.py"),
                        wf.index("python tools/baldosa_qa08_native_ppu_register_trace_patch.py"))
        self.assertLess(wf.index("python tools/baldosa_qa08_native_ppu_register_trace_patch.py"),
                        wf.index("cmake -S baldosa -B baldosa/build-ur-win"))


if __name__=="__main__":
    unittest.main()
