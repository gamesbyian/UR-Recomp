"""RF040: preserve genuine single source CPU read and SPC echo writes."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf040_cpu_echo_transport_observer as m
import qa01_ipl_echo_trace_patch as rf030
import qa01_rf032_native_port_target_observer as rf032


class Echo(unittest.TestCase):
    def test_original_cpu_reads_preserve_execute_and_return(self):
        old = rf030.CPU_READ_NEW
        new = m.original_apu(old)
        self.assertEqual(m.original_apu(new), new)
        self.assertEqual(old.count("S9xAPUExecute();"), new.count("S9xAPUExecute();"))
        self.assertEqual(old.count("smp.port_read(port & 3)"), new.count("smp.port_read(port & 3)"))
        self.assertEqual(old.count("return observed;"), new.count("return observed;"))
        self.assertIn("QA01RF040ORIGCPU", new)
        self.assertIn("QA01RF040ORIGCPU_TRUNCATED", new)

    def test_original_spc_preserves_true_io_write_once(self):
        old = rf030.WRITE_NEW
        new = m.original_spc(old)
        self.assertEqual(m.original_spc(new), new)
        self.assertEqual(old.count("mmio_write(addr, data)"), new.count("mmio_write(addr, data)"))
        self.assertEqual(old.count("apuram[addr] = data"), new.count("apuram[addr] = data"))
        self.assertIn("QA01RF040ORIGSPCECHO", new)

    def test_native_cpu_post_sync_post_filter_once(self):
        old = rf032.SNES_READ_NEW
        new = m.native_snes(old)
        self.assertEqual(m.native_snes(new), new)
        for op in ("rtl_apu_port_observers_read", "audio_trace_on_cpu_port_read", "RtlApuUnlock();"):
            self.assertEqual(old.count(op), new.count(op))
        self.assertIn("raw_apu_value", new)
        self.assertIn("returned=%02X", new)
        self.assertIn("QA01RF040NATIVECPU_TRUNCATED", new)

    def test_native_spc_echo_single_store(self):
        old = rf030.NATIVE_ECHO_NEW
        new = m.native_apu(old)
        self.assertEqual(m.native_apu(new), new)
        self.assertEqual(old.count("apu->outPorts[adr - 0xf4] = val;"),
                         new.count("apu->outPorts[adr - 0xf4] = val;"))
        self.assertEqual(old.count("audio_trace_on_spc_port_write("),
                         new.count("audio_trace_on_spc_port_write("))
        self.assertIn("QA01RF040NATIVESPCECHO", new)

    def test_fail_closed_on_unstaged_or_partial_source(self):
        for fn in (m.original_apu, m.original_spc, m.native_snes, m.native_apu):
            with self.assertRaisesRegex(ValueError, "needs staged"):
                fn("int fake;")
        incomplete = m.original_apu(rf030.CPU_READ_NEW)
        with self.assertRaisesRegex(ValueError, "partial/tampered"):
            m.original_apu(incomplete.replace("103919510ull", "103919511ull"))

    def test_scope_and_no_cycle_or_release_authority(self):
        self.assertEqual(str(m.O_APU), "apu/apu.cpp")
        self.assertEqual(str(m.O_SPC), "apu/bapu/smp/core.cpp")
        self.assertEqual(str(m.N_SNES), "snesrecomp/runner/src/snes/snes.c")
        self.assertEqual(str(m.N_APU), "snesrecomp/runner/src/snes/apu.c")
        all_loggers = (m.CPU_ORIG_APPEND + m.SPC_ORIG_APPEND +
                       m.CPU_NATIVE_APPEND + m.SPC_NATIVE_APPEND)
        for forbidden in ("master_cycles +=", "cpuCyclesLeft +=", "portQHead++",
                          "S9xAPUExecute();", "mmio_write(addr, data);"):
            self.assertNotIn(forbidden, all_loggers)


if __name__ == "__main__":
    unittest.main()
