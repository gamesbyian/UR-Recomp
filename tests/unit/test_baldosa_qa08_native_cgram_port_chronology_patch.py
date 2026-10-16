"""One exact Uniracers native read-only results-CGRAM port hook."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import baldosa_qa08_native_cgram_port_chronology_patch as port

class NativeCgramPortChronologyTest(unittest.TestCase):
    def setUp(self):
        self.old=(
            "#include <stdio.h>\n#include <stdlib.h>\n"
            "void ppu_write(Ppu* ppu, uint8_t adr, uint8_t val) {\n"
            "  ppu_wlog_note(adr, val);\n"
            "  switch(adr) { case 0x21: break; case 0x22: break; }\n}\n"
        )

    def test_exact_opt_in_readonly_register_probe_and_idempotence(self):
        current=port.patch_source(self.old)
        self.assertEqual(current,port.patch_source(current))
        self.assertEqual(current.count(port.MARK),1)
        self.assertIn('getenv("UR_QA08_WINDOWS_CGRAM_PORT_TRACE")',current)
        self.assertIn("ppu->cgramPointer",current)
        self.assertIn("ppu->cgramSecondWrite",current)
        self.assertIn("g_snes->hPos",current)
        self.assertIn("g_ppu_wlog_src",current)
        self.assertEqual(current.replace(port.TRACE,""),self.old)
        self.assertNotIn("forcepoke",current)

    def test_fails_closed_on_tamper_or_foreign_guest(self):
        for source in (
            self.old.replace("ppu_wlog_note(adr, val);",""),
            self.old.replace("case 0x21:", "case 0x20:"),
            self.old+self.old,
            port.patch_source(self.old).replace("snes_frame_counter >= 5168",
                                                "snes_frame_counter >= 0"),
        ):
            with self.subTest(source=source[:60]),self.assertRaises(ValueError):
                port.patch_source(source)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            f=root/port.RELATIVE
            f.parent.mkdir(parents=True)
            f.write_text(self.old)
            (root/"src/gen").mkdir(parents=True)
            (root/"src/gen/dispatch_v2.c").write_text("guest")
            with patch.object(port,"pinned_revision",side_effect=["foreign",port.CORE_REV]):
                with self.assertRaises(ValueError):
                    port.apply_game(root,write=True)
            self.assertEqual(f.read_text(),self.old)

    def test_workflow_applies_only_in_pinned_title_before_compile(self):
        wf=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        cmd="python tools/baldosa_qa08_native_cgram_port_chronology_patch.py --game baldosa"
        self.assertEqual(wf.count(cmd+" --apply-candidate"),1)
        self.assertLess(wf.index(cmd),wf.index("cmake -S baldosa -B baldosa/build-ur-win"))
        cover=(ROOT/"tools/qa08_windows_full_twoplayer_source_coverage.py").read_text()
        self.assertIn("UR_QA08_WINDOWS_CGRAM_PORT_TRACE",cover)
        self.assertIn("inspect_native_cgram_port_history",cover)

if __name__=="__main__":
    unittest.main()
