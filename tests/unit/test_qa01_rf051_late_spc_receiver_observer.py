"""RF051 read-only source/native receiver staging, fail-closed source pin."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf041_zoo_smp_debt_observer as rf041
import qa01_rf051_late_spc_receiver_observer as rf051

class SourceReceiverTests(unittest.TestCase):
    def test_original_single_real_spc_read_and_source_unchanged_execution(self):
        source="\n"+rf041.ORIGINAL_SPC_AFTER+"\n"
        result=rf051.original(source)
        self.assertEqual(result.count("mmio_read(addr)"),source.count("mmio_read(addr)"))
        self.assertEqual(result.count("QA01RF051ORIGSPC ordinal="),1)
        self.assertIn("104485120ull",result)
        self.assertIn("104485800ull",result)
        self.assertEqual(rf051.original(result),result)

    def test_native_actual_queue_path_once_no_extra_port_write(self):
        source="\n"+rf041.NATIVE_AFTER+"\n"
        result=rf051.native(source)
        self.assertEqual(result.count("apu_writePortNow("),source.count("apu_writePortNow("))
        self.assertEqual(result.count("QA01RF051NATIVE ordinal="),1)
        self.assertIn("f >= 6110 && f <= 6140",result)
        self.assertEqual(rf051.native(result),result)

    def test_missing_prior_pin_and_partial_source_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"exact original RF041"):
            rf051.original("not an actual source")
        with self.assertRaisesRegex(ValueError,"exact native RF041"):
            rf051.native("not an actual native source")
        with self.assertRaisesRegex(ValueError,"partial/tampered"):
            rf051.original(rf051.original(rf041.ORIGINAL_SPC_AFTER).replace(
                "QA01RF051ORIGSPC ordinal=","QA01RF051BAD ordinal=",1))
        with self.assertRaisesRegex(ValueError,"partial/tampered"):
            rf051.native(rf051.native(rf041.NATIVE_AFTER).replace(
                "QA01RF051NATIVE ordinal=","QA01RF051BAD ordinal=",1))
if __name__=="__main__":unittest.main()
