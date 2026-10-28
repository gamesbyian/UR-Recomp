"""RF092 pinned original SMP source and nonintrusive clock/port observer."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_rf092_original_spc_edges as m

class RF092Source(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = ROOT / "third_party" / "src" / "snes9x-libretro"
        cls.original = tuple((root / path).read_text(encoding="utf-8")
                             for path in (m.SMP, m.CORE, m.MEMORY))

    def test_real_pinned_smp_sources_and_one_time_patch(self):
        smp, core, memory = m.patch(*self.original)
        self.assertEqual(smp.count(m.STAMP), 1)
        self.assertIn('#include "../../../snes9x.h"\n#include <cstdio>', smp)
        self.assertIn('if (frame < 6054u || frame > 6059u', smp)
        self.assertIn('flag[0] != \'1\' || flag[1] != \'\\0\'', smp)
        self.assertIn('QA01RF092SPC_TRUNCATED', smp)
        self.assertIn('spc_ticks=%llu spc_next_pc=%04X clock=original_spc', smp)
        reset = smp.index(m.SMP_RESET)
        self.assertLess(smp.index('rf092_spc_ticks = 0;', reset),
                        smp.index('for(unsigned n = 0x0000', reset))
        self.assertLess(core.index('dsp.clock++;'), core.index('++rf092_spc_ticks;'))
        self.assertLess(core.index('dsp.clock += clocks;'),
                        core.index('rf092_spc_ticks += clocks;'))
        self.assertLess(memory.index('cpu.port_read(addr);'),
                        memory.index('rf092_spc_port("CPU_TO_SPC_READ"'))
        self.assertLess(memory.index('port_write(addr, data);'),
                        memory.index('rf092_spc_port("SPC_TO_CPU_WRITE"'))
        with self.assertRaisesRegex(ValueError, 'already or partly staged'):
            m.patch(smp, core, memory)

    def test_no_new_smp_bus_operations_or_clock_adjustments(self):
        _, core, memory = m.patch(*self.original)
        original_core, original_memory = self.original[1:]
        for call in ('timer0.tick();', 'timer1.tick();', 'timer2.tick();',
                     'timer0.tick(clocks);', 'timer1.tick(clocks);',
                     'timer2.tick(clocks);', 'clock++;', 'clock += clocks;',
                     'dsp.clock++;', 'dsp.clock += clocks;'):
            self.assertEqual(core.count(call), original_core.count(call), call)
        for call in ('cpu.port_read(addr)', 'port_write(addr, data)',
                     'apuram[addr] = data'):
            self.assertEqual(memory.count(call), original_memory.count(call), call)
        self.assertEqual(memory.count('rf092_spc_port('), 2)
        self.assertNotIn('S9xAPUExecute(', core + memory)
        self.assertNotIn('S9xAPUReadPort(', core + memory)

    def test_fail_closed_on_missing_or_duplicate_source_anchors(self):
        smp, core, memory = self.original
        for altered in ((smp.replace(m.SMP_HEADER, ''), core, memory),
                        (smp + m.SMP_RESET, core, memory),
                        (smp, core.replace(m.CORE_MULTI, ''), memory),
                        (smp, core + m.CORE_SINGLE, memory),
                        (smp, core, memory.replace(m.MEMORY_READ, '')),
                        (smp, core, memory + m.MEMORY_WRITE)):
            with self.subTest(altered=tuple(len(s) for s in altered)):
                with self.assertRaisesRegex(ValueError, 'drift'):
                    m.patch(*altered)

    def test_existing_campaign_stages_disposable_spc_before_clean_build(self):
        workflow = (ROOT / ".github/workflows/qa01-event-campaign.yml").read_text()
        old = 'python3 tools/qa01_rf083_original_sound_dp_first_writer.py --root "$CORE_SRC"'
        new = 'python3 tools/qa01_rf092_original_spc_edges.py --root "$CORE_SRC"'
        clean = 'make -C "$CORE_SRC/libretro" clean'
        self.assertEqual(workflow.count(new), 1)
        self.assertLess(workflow.index(old), workflow.index(new))
        self.assertLess(workflow.index(new), workflow.index(clean))
        self.assertIn('export UR_QA01_RF092_ORIGINAL_SPC=1', workflow)
        self.assertIn('QA01RF092SPC_TRUNCATED', workflow)
        self.assertIn('kind=CPU_TO_SPC_READ addr=00F4', workflow)
        self.assertIn('kind=SPC_TO_CPU_WRITE addr=00F4', workflow)

if __name__ == "__main__":
    unittest.main()
