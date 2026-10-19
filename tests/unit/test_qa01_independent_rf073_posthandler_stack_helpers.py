"""QA01 ROM-free negative checks: late native helpers cannot masquerade as RTI reads."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_independent_rf073_posthandler_stack_helpers as qa


def synthetic():
    events=[]
    brackets=[]
    for frame in qa.rf073.FRAMES:
        base=len(events)
        def put(stage, **fields):
            item={
                "seq":str(len(events)+1),"stage":stage,"f":str(frame),
                "master":str(100000+frame*10000+len(events)*100),
                **fields,
            }
            events.append(item)
            return len(events)
        put("entry")
        push=put("after_push")
        status=put("read",bank="00",addr="01ED",value="0026",width="1",nmi="1")
        rti=put("compiled_rti")
        returned=put("handler_return")
        first=put("read",bank="00",addr="01F1",value="0026",width="1",nmi="0")
        for addr,byte in ((0x01ED,"0041"),(0x01EE,"0085"),
                          (0x01EF,"0001"),(0x01F0,"008C")):
            put("read",bank="00",addr=f"{addr:04X}",value=byte,width="1",nmi="0")
        brackets.append({
            "native_frame":frame,
            "native_after_push_seq":push,
            "native_compiled_RTI_seq":rti,
            "native_true_status_stack_helper_read_seq":status,
            "native_handler_return_seq":returned,
            "native_first_post_handler_stack_helper_read_seq":first,
            "native_after_push_raw_4_bytes":"26EED482",
            "original_post_real_NMI_raw_5_stack_bytes":"26F0D48226",
        })
    return events,brackets


class PostReturnNativeStackHelper(unittest.TestCase):
    def test_later_five_address_reads_never_make_native_RTI_consumed_PC(self):
        events,brackets=synthetic()
        report=qa.first_posthandler(events,brackets)
        self.assertEqual(report["nine_authentic_native_NMI_windows"],9)
        self.assertEqual(report["actual_first_later_stack_byte_observations"],45)
        self.assertEqual(
            report["distinct_native_helper_operations_supplying_first_later_bytes"],45)
        self.assertTrue(report["first_posthandler_read_is_01F1_26_in_all_nine"])
        self.assertFalse(report["native_saved_PC_or_PB_read_during_compiled_RTI_proven"])
        self.assertFalse(report["first_original_native_differing_consumed_stack_byte_proven"])
        self.assertEqual(report["accepted_complete_USA_events"],0)
        first=report["frames"][0]
        self.assertEqual(first["observed_first_later_stack_helper_reads"]["00:01EE"]["native_value"],"85")
        self.assertEqual(first["observed_first_later_stack_helper_reads"]["00:01F1"]["native_value"],"26")
        self.assertFalse(first["these_later_reads_are_the_compiled_RTI_saved_PC_reads"])

    def test_first_real_word_covers_two_stack_bytes_without_extra_guest_reads(self):
        events,brackets=synthetic()
        first_ed=next(e for e in events if e["f"]=="1017" and
                      e.get("addr")=="01ED" and e.get("nmi")=="0")
        first_ed.update(value="0241",width="2")
        first_ef=next(e for e in events if e["f"]=="1017" and
                      e.get("addr")=="01EF" and e.get("nmi")=="0")
        first_ef.update(value="0001",width="2")
        r=qa.first_posthandler(events,brackets)
        row=r["frames"][0]["observed_first_later_stack_helper_reads"]
        self.assertEqual(row["00:01ED"]["native_RF047_local_seq"],
                         row["00:01EE"]["native_RF047_local_seq"])
        self.assertEqual(row["00:01ED"]["native_value"],"41")
        self.assertEqual(row["00:01EE"]["native_value"],"02")
        self.assertEqual(row["00:01EE"]["actual_helper_width_bytes"],2)
        self.assertEqual(row["00:01EF"]["native_value"],"01")
        self.assertEqual(row["00:01F0"]["native_value"],"00")
        self.assertEqual(row["00:01EF"]["native_RF047_local_seq"],
                         row["00:01F0"]["native_RF047_local_seq"])
        self.assertEqual(r["actual_first_later_stack_byte_observations"],45)
        self.assertEqual(r[
            "distinct_native_helper_operations_supplying_first_later_bytes"],43)
        self.assertFalse(r["native_saved_PC_or_PB_read_during_compiled_RTI_proven"])

    def test_missing_posthandler_helper_refused_instead_of_invented(self):
        events,brackets=synthetic()
        events=[e for e in events if not
                (e["f"]=="1017" and e.get("addr")=="01EE" and e.get("nmi")=="0")]
        # Source-local sequences cannot skip a real event.
        with self.assertRaisesRegex(ValueError,"sequence incomplete"):
            qa.first_posthandler(events,brackets)
        for i,e in enumerate(events):
            e["seq"]=str(i+1)
        with self.assertRaises(ValueError):
            qa.first_posthandler(events,brackets)

    def test_posthandler_first_01f1_read_must_have_real_value_and_provenance(self):
        events,brackets=synthetic()
        for key,value in (("value","0027"),("nmi","1"),("bank","01"),
                          ("master","0")):
            changed=copy.deepcopy(events)
            item=next(e for e in changed if e["f"]=="1017" and e.get("addr")=="01F1")
            item[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                qa.first_posthandler(changed,brackets)

    def test_corrupted_native_status_qualifier_not_reinterpreted_as_late_read(self):
        events,brackets=synthetic()
        for key,value in (("addr","01EE"),("value","0027"),("nmi","0")):
            changed=copy.deepcopy(events)
            item=next(e for e in changed if e["f"]=="1017" and e.get("nmi")=="1")
            item[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(
                    ValueError,"status-only helper"):
                qa.first_posthandler(changed,brackets)

    def test_bad_real_bracket_identity_or_frame_refused(self):
        events,brackets=synthetic()
        for key,value in (("native_frame",1026),
                          ("native_true_status_stack_helper_read_seq",100),
                          ("native_handler_return_seq",999)):
            b=copy.deepcopy(brackets)
            b[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                qa.first_posthandler(events,b)

    def test_fake_source_archive_cannot_skip_rf073_source_authentication(self):
        with tempfile.TemporaryDirectory() as d:
            fake=Path(d)/"fake.zip"
            fake.write_bytes(b"not a ZIP")
            with self.assertRaisesRegex(ValueError,"SHA256 mismatch"):
                qa.authentic(fake)


if __name__=="__main__":
    unittest.main()
