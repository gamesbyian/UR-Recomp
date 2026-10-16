"""Exact native PPU $2100 source writer recorder is observation only."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import baldosa_qa08_native_cgram_port_chronology_patch as previous
import baldosa_qa08_native_inidisp_port_trace_patch as trace

class NativeINIDISPWriteTraceTest(unittest.TestCase):
    def setUp(self):
        self.source=(
            "#include <stdio.h>\n#include <stdlib.h>\n"
            +previous.ANCHOR+previous.TRACE+
            "switch(adr) { case INIDISP & 0xff: break;"
            " case 0x21: break; case 0x22: break; }\n"
        )
    def test_exact_title_readonly_writes_only_and_idempotent(self):
        x=trace.patch_source(self.source)
        self.assertEqual(trace.patch_source(x),x)
        self.assertEqual(x.count(trace.MARK),1)
        self.assertIn('getenv("UR_QA08_WINDOWS_INIDISP_PORT_TRACE")',x)
        self.assertIn("g_snes->vPos",x)
        self.assertIn("g_snes->hPos",x)
        self.assertIn("(unsigned)g_ppu_wlog_src",x)
        self.assertIn("(unsigned)ppu->inidisp",x)
        self.assertEqual(x.replace(trace.TRACE,""),self.source)
    def test_source_gates_reject_altered_guest_cpu_or_renderer(self):
        for changed in (
            self.source.replace(previous.TRACE,""),
            self.source.replace(previous.ANCHOR,"void untrusted() {\n"),
            self.source+self.source,
            trace.patch_source(self.source).replace("snes_frame_counter >= 4008",
                                                    "snes_frame_counter >= 0"),
        ):
            with self.subTest(prefix=changed[:60]),self.assertRaises(ValueError):
                trace.patch_source(changed)
        wf=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        cmd="python tools/baldosa_qa08_native_inidisp_port_trace_patch.py --game baldosa"
        self.assertEqual(wf.count(cmd+" --apply-candidate"),1)
        self.assertLess(wf.index(cmd),wf.index("cmake -S baldosa -B baldosa/build-ur-win"))

if __name__=="__main__":
    unittest.main()
