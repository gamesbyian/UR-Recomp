"""RF044 actual bus-only first-stack writer ancestry fail-closed tests."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf044_stack_bus_report as m

ORIG="""QA01RF044ORIGBUS f=1017 v=210 h=320 kind=ww bank=00 addr=01ED w=2 value=F026 pb=82 pc=5521 S=01EE
QA01RF044ORIGBUS f=1018 v=2 h=204 kind=rb bank=00 addr=01ED w=1 value=26 pb=82 pc=5531 S=01EF
QA01RF044ORIGNMI f=1018 f1=1018 pc=825521 S0=01EF S1=01EB old=26F0D48255 new=26F0D48255
"""
NATIVE="""f1017  00:01ED=F026 w2 I_NMI_M1X1 rf044_S=01EE IPC=825521
QA01RF044NATIVEREAD f=1018 kind=r1 bank=00 addr=01ED value=0026 S=01EF IPC=825531 scope=I_NMI_M1X1
"""
class Bus(unittest.TestCase):
 def test_real_writer_reader_and_nmi_are_distinct(self):
  r=m.resolve(ORIG,NATIVE)
  self.assertEqual(r["original_bus_events_count"],2)
  self.assertEqual(r["native_read_and_writer_events_count"],2)
  self.assertEqual(r["original_nmi_events_count"],1)
  o=r["actual_first_host1017_1018_bus_writers_and_readers"]["original"]
  n=r["actual_first_host1017_1018_bus_writers_and_readers"]["native"]
  self.assertEqual(o["01ED"]["last_observed_early_write"]["value"],"F026")
  self.assertEqual(n["01ED"]["last_observed_early_write"]["scope"],"I_NMI_M1X1")
  self.assertEqual(o["01ED"]["first_observed_early_read"]["value"],"26")
  self.assertFalse(r["complete_last_writer_and_next_reader_NMI_causality_proven"])
  self.assertEqual(r["complete_usa_events_accepted"],0)
 def test_early_read_or_snapshot_alone_cannot_invent_writer(self):
  r=m.resolve("QA01RF044ORIGBUS f=1018 kind=rb addr=01ED w=1 value=26 S=01EF pc=5531",
              "QA01RF044NATIVEREAD f=1018 kind=r1 addr=01ED value=26 S=01EF IPC=5531 scope=x")
  self.assertFalse(r["all_four_stack_bytes_both_guest_early_writers_observed"])
  self.assertIsNone(r["actual_first_host1017_1018_bus_writers_and_readers"]["original"]["01ED"]["last_observed_early_write"])
 def test_missing_truncated_or_ungated_logs_rejected(self):
  with self.assertRaisesRegex(ValueError,"overflow"):
   m.resolve(ORIG+"QA01RF044ORIGBUS_TRUNCATED\n",NATIVE)
  with self.assertRaisesRegex(ValueError,"framegate"):
   m.resolve(ORIG,NATIVE.replace("f1017","f9999"))
  with self.assertRaisesRegex(ValueError,"incomplete"):
   m.resolve("QA01RF044ORIGBUS f=1018 addr=01ED\n",NATIVE)
 def test_all_five_addresses_are_present_and_zero_credit(self):
  r=m.resolve("", "")
  self.assertEqual(sorted(r["actual_first_host1017_1018_bus_writers_and_readers"]["native"].keys()),
                   ["01ED","01EE","01EF","01F0","01F1"])
  self.assertFalse(r["physical_byte_comparison_masked"])
  self.assertEqual(r["complete_usa_events_accepted"],0)
if __name__=="__main__":unittest.main()
