"""RF041 original/native executed SMP clock-debt scope cannot mutate I/O."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf041_zoo_smp_debt_observer as m

class TestSmpDebtSourceOnly(unittest.TestCase):
    def test_original_cpu_preserves_one_sync_one_publish(self):
        old = m.ORIGINAL_CPU_BEFORE
        new = m.original_cpu(old)
        self.assertEqual(m.original_cpu(new), new)
        self.assertEqual(old.count("S9xAPUExecute();"), new.count("S9xAPUExecute();"))
        self.assertEqual(old.count("SNES::cpu.port_write(port & 3, byte);"),
                         new.count("SNES::cpu.port_write(port & 3, byte);"))
        for phase in ("before-sync", "after-sync-before-publish", "after-publish"):
            self.assertIn(phase, new)

    def test_rf037_nested_writer_staging_is_preserved(self):
        import qa01_rf034_spc_opcode_boundary_observer as rf034
        import qa01_rf037_upstream_writer_observer as upstream
        writer = "    SNES::cpu.port_write(port & 3, byte);\n"
        self.assertEqual(rf034.ORIGINAL_AFTER.count(writer), 1)
        staged = rf034.ORIGINAL_AFTER.replace(writer, writer + upstream.NEW_ORIG, 1)
        new = m.original_cpu(staged)
        self.assertEqual(new.count(upstream.NEW_ORIG), 1)
        self.assertEqual(new.count("S9xAPUExecute();"), 1)
        self.assertEqual(new.count("SNES::cpu.port_write(port & 3, byte);"), 1)
        self.assertIn("rf034_debt_before", new)
        self.assertEqual(m.original_cpu(new), new)

    def test_original_spc_f6_does_not_duplicate_read_or_tick(self):
        old = m.ORIGINAL_SPC_BEFORE
        new = m.original_spc(old)
        self.assertEqual(m.original_spc(new), new)
        self.assertEqual(old.count("mmio_read(addr)"), new.count("mmio_read(addr)"))
        self.assertEqual(old.count("return observed;"), new.count("return observed;"))
        self.assertEqual(old.count("tick();"), new.count("tick();"))
        self.assertIn("QA01RF041ORIGF6_TRUNCATED", new)
        self.assertIn("opcode_cycle", new)

    def test_native_preserves_queue_and_receiver_call_sites(self):
        old = m.NATIVE_BEFORE
        new = m.native_spc(old)
        self.assertEqual(m.native_spc(new), new)
        for source in ("apu_writePortNow(", "QA01RF037NATIVEBUS_TRUNCATED",
                       "static void ur_qa01_rf037_port("):
            self.assertEqual(old.count(source), new.count(source))
        self.assertGreater(new.count("apu->portClock"), old.count("apu->portClock"))
        self.assertIn("apu->cpuCyclesLeft", new)
        self.assertIn("QA01RF041NATIVE_TRUNCATED", new)
        self.assertIn("103919420ull", new)

    def test_reject_unstaged_and_tampered_guest(self):
        for fn in (m.original_cpu, m.original_spc, m.native_spc):
            with self.assertRaisesRegex(ValueError, "missing/duplicated"):
                fn("void unrelated() {}")
        with self.assertRaisesRegex(ValueError, "partial/tampered"):
            m.original_cpu(m.original_cpu(m.ORIGINAL_CPU_BEFORE).replace(
                "phase=after-publish", "phase=other"))

    def test_no_timing_scheduling_or_release_edits(self):
        body = (m.ORIGINAL_CPU_REPLACEMENT + m.ORIGINAL_SPC_INSERT +
                m.NATIVE_INSERT)
        for forbidden in ("cpuCyclesLeft +=", "master_cycles +=",
                          "portQHead++", "S9xAPUExecute();\n    S9xAPUExecute();",
                          "apu_runCycles(", "mmio_write(", "sleep("):
            self.assertNotIn(forbidden, body)

if __name__ == "__main__":
    unittest.main()
