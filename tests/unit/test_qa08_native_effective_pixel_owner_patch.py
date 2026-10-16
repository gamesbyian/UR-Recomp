"""Read-only effective 2P pixel/OBJ provenance is exact and opt-in only."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import baldosa_qa08_native_effective_pixel_owner_patch as pixel
import baldosa_qa08_native_ppu_register_trace_patch as previous
import qa08_windows_effective_pixel_owner as witness

class ExactNativePixelOwnerSourceTest(unittest.TestCase):
    def setUp(self):
        self.source=(
          '#include <stdint.h>\n#include <stdbool.h>\n'
          '#include <stdio.h>\n#include <stdlib.h>\n'
          '#include "snes.h"\n'
          +previous.LEGACY_MARK+'\n'
          +previous.ENTRY+previous.TRACE+'}\n'
          +pixel.INTRO+
          '  int r = 0, r2 = 0;\n  int g = 0, g2 = 0;\n'
          '  int b = 0, b2 = 0;\n'
          '  if (!PPU_forcedBlank(ppu)) {\n'+pixel.MAIN+
          pixel.WINDOW+
          '    bool mathEnabled = mainLayer < 6 && (PPU_mathEnabled(ppu) >> mainLayer & 1) && !(\n'
          '      PPU_preventMathMode(ppu) == 3 ||\n'
          '      (PPU_preventMathMode(ppu) == 2 && colorWindowState) ||\n'
          +pixel.MATH_END+
          '    int secondLayer = 5;\n'
          '    if (true) {\n'+pixel.SUB+'    }\n'
          '  }\n  int row = y - 1;\n'
          '  uint8 *pixelBuffer = ppu->renderBuffer;\n'
          +pixel.END+'}\n'
        )

    def test_instrument_only_the_existing_PPU_resolved_pixel_and_output(self):
        modified=pixel.patch_source(self.source)
        self.assertEqual(pixel.patch_source(modified),modified)
        self.assertEqual(modified.count(pixel.MARK),1)
        self.assertIn('UR_QA08_WINDOWS_PIXEL_OWNER_TRACE',modified)
        self.assertIn('ppu_resolve_pixel(ppu, x, y, false',modified)
        self.assertIn('ppu_resolve_pixel(ppu, x, y, true',modified)
        self.assertEqual(modified.count("ppu_resolve_pixel(ppu, x, y, false"),1)
        self.assertEqual(modified.count("ppu_resolve_pixel(ppu, x, y, true"),1)
        self.assertIn("raster_y=%d ppu_line=%d",modified)
        self.assertIn("UR_QA08_WIN_OAM_LINE",modified)
        self.assertIn("(x == 225 && (y == 97 || y == 121))",modified)
        self.assertIn("(x == 205 && (y == 116 || y == 140))",modified)
        for render in (pixel.MAIN,pixel.WINDOW,pixel.MATH_END,pixel.SUB,pixel.END):
            self.assertIn(render,modified)
        clean=(modified.replace(pixel.INTRO+pixel.DECL,pixel.INTRO)
            .replace(pixel.MAIN+pixel.CAPTURE_MAIN,pixel.MAIN)
            .replace(pixel.WINDOW+pixel.CAPTURE_WINDOW,pixel.WINDOW)
            .replace(pixel.MATH_END+pixel.CAPTURE_MATH,pixel.MATH_END)
            .replace(pixel.SUB+pixel.CAPTURE_SUB,pixel.SUB)
            .replace(pixel.END+pixel.TRACE,pixel.END))
        self.assertEqual(clean,self.source)

    def test_refuse_tampered_old_PPU_and_double_probes(self):
        bads=[self.source.replace(previous.LEGACY_MARK,"MISSING"),
              self.source.replace(previous.TRACE,""),
              self.source.replace(pixel.SUB,""),
              self.source+self.source,
              pixel.patch_source(self.source).replace("qa08_main_layer = mainLayer;","qa08_main_layer = 0;")]
        for bad in bads:
            with self.subTest(source=bad[:60]),self.assertRaises(ValueError):
                pixel.patch_source(bad)

    def test_other_title_or_invalid_source_pin_never_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=Path(tmp)
            f=game/pixel.RELATIVE
            f.parent.mkdir(parents=True)
            f.write_text(self.source,encoding="utf-8")
            (game/"src/gen").mkdir(parents=True)
            (game/"src/gen/dispatch_v2.c").write_text("native")
            with patch.object(pixel.previous,"pinned_revision",side_effect=["other",previous.CORE_REV]):
                with self.assertRaisesRegex(ValueError,"guest"):
                    pixel.apply_game(game,write=True)
            self.assertEqual(f.read_text(),self.source)
            with patch.object(pixel.previous,"pinned_revision",side_effect=[previous.GAME_REV,previous.CORE_REV]):
                pixel.apply_game(game,write=True)
            self.assertEqual(f.read_text(),pixel.patch_source(self.source))

    def test_workflow_stages_only_after_original_renderer_and_never_on_other_PR(self):
        s=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        for name in ("baldosa_qa08_native_ppu_register_trace_patch.py",
                     "baldosa_qa08_native_effective_pixel_owner_patch.py"):
            self.assertIn("python tools/"+name+" --game baldosa --apply-candidate",s)
        self.assertLess(s.index("baldosa_qa08_native_ppu_register_trace_patch.py"),
                        s.index("baldosa_qa08_native_effective_pixel_owner_patch.py"))
        self.assertLess(s.index("baldosa_qa08_native_effective_pixel_owner_patch.py"),
                        s.index("cmake -S baldosa -B baldosa/build-ur-win"))
        self.assertIn("python tools/qa08_windows_effective_pixel_owner.py",s)
        self.assertIn("github.event.pull_request.number == 1641",s)
        self.assertEqual(s.count("python tests/unit/test_qa08_native_effective_pixel_owner_patch.py"),1)
        self.assertIn("Retain bounded medal pixel-owner source lines",s)

class RuntimeGuardTest(unittest.TestCase):
    def setUp(self):
        self.guest=["0x00000000"]*5484
        self.guestsha=witness.sha256(("\n".join(self.guest)+"\n").encode())
        self.pixel=[]
        self.oam=[]
        for (frame,x,y),rgb in sorted(witness.POINTS.items()):
            line=(f"UR_QA08_WIN_PIXEL_OWNER frame={frame} x={x} raster_y={y} "
                f"ppu_line={y+1} main=4 sub=5 math=1 window=0 "
                f"premain=13,14,15 presub=0,0,0 postmath=13,14,15 "
                f"final={rgb[0]},{rgb[1]},{rgb[2]} obj=02d1 "
                f"obj_cgram_index=d1 obj_word=16ad inidisp=0e "
                f"cgadsub=7f cgwsel=02 fixed=0000 tm=13 ts=10 obsel=63")
            self.pixel.append(line)
            if frame!=1280:
                for slot in witness.SLOTS:
                    self.oam.append(
                        f"UR_QA08_WIN_OAM_LINE frame={frame} x={x} ppu_line={y+1} "
                        f"slot={slot} xy=5bc8 attrs=1ba2 high=0")
        self.text="\n".join(self.pixel+self.oam)+"\n"

    def inspect(self,text):
        with patch.object(witness,"GUEST_CRC_SHA",self.guestsha):
            return witness.inspect(text,self.guest)

    def test_full_real_native_telemetry_shape_requires_exact_11_and_70(self):
        report=self.inspect(self.text)
        self.assertEqual(report["independently_source_qualified_native_pixels"],11)
        self.assertEqual(report["independently_source_qualified_native_scanline_OAM_snapshots"],70)
        self.assertEqual(report["real_native_2p_guest_frames"],5484)
        self.assertFalse(report["original_snes9x_2014_same_field_pixel_priority_proven"])
        self.assertFalse(report["release_graphics_accepted"])

    def test_missing_duplicate_extra_and_wrong_pixel_rejected(self):
        for data in (self.text.replace(self.pixel[0]+"\n",""),
                     self.text+self.pixel[0]+"\n",
                     self.text.replace(self.pixel[1],"UR_QA08_WIN_PIXEL_OWNER frame=4032 x=207 raster_y=91"),
                     self.text.replace(self.pixel[1],self.pixel[1].replace("main=4","main=99")),
                     self.text.replace(self.pixel[1],self.pixel[1].replace("obj=02d1","obj=wrong")),
                     self.text.replace(self.pixel[0],self.pixel[0].replace("final=90,66,74","final=90,74,82")),
                     self.text.replace(self.oam[0]+"\n",""),
                     self.text+self.oam[0]+"\n"):
            with self.subTest(err=data[-80:]),self.assertRaises(ValueError):
                self.inspect(data)

    def test_single_win32_route_can_emit_full_source_and_ppu_port_chronology(self):
        host=(ROOT/"tools/qa08_windows_effective_pixel_owner.py").read_text()
        workflow=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertIn('ap.add_argument("--collect-2p-fullroute"',host)
        self.assertIn('"UR_QA08_WINDOWS_ORIGINAL_SOURCE_CASE":"twoplayer-fullroute"',host)
        self.assertIn('"UR_QA08_WINDOWS_CGRAM_PORT_TRACE":"1"',host)
        self.assertIn('capture=fullroute.inspect(source_dir,log,crcs)',host)
        self.assertIn('capture["actual_native_guest_CRC_sha256"]!=GUEST_CRC_SHA',host)
        self.assertIn('same_unmodified_exe_and_native_guest_execution_as_pixel_owner',host)
        step=workflow.split("- name: Capture source-qualified medal pixel owners from real Win32 2P",1)[1].split("\n      - name: ",1)[0]
        self.assertIn("github.event.pull_request.number == 1641",step)
        self.assertIn("--collect-2p-fullroute",step)
        self.assertEqual(step.count("python tools/qa08_windows_effective_pixel_owner.py"),1)
        self.assertNotIn("python tools/qa08_windows_full_twoplayer_source_coverage.py",step)
        upload=workflow.split("- name: Retain bounded medal pixel-owner source lines",1)[1].split("\n      - name: ",1)[0]
        for needle in ("qa08-windows-2p-fullroute.json","qa08-native-ppu-source-phase-log.txt","source/*.pam"):
            self.assertIn(needle,upload)
        self.assertIn("retention-days: 4",upload)

    def test_unverified_guest_crc_and_missing_guest_frames_refused(self):
        for crc in (self.guest[:-1],["broken"]*5484):
            with self.assertRaises(ValueError):
                witness.inspect(self.text,crc)
        with self.assertRaisesRegex(ValueError,"guest CRC history"):
            witness.inspect(self.text,self.guest)

if __name__=="__main__":
    unittest.main()
