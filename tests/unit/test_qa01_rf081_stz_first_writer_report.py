"""RF081 first actual STZ setter/commit after NMI: adversarial source proof tests."""
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf081_stz_first_writer_report as m
import qa01_rf079_real_bit_bpl_report as previous
from tests.unit.test_qa01_rf079_real_bit_bpl_report import sample

def fixture():
    original,native=sample()
    o=[]
    ordinal=0
    for line in original.splitlines():
        o.append(line)
        if line.startswith("QA01RF079ORIG ") and "before=82D4F0 " in line:
            frame=int(re.search(r"f=(\\d+)",line).group(1))
            o.append(f"QA01RF076ORIGPC seq={frame-1016} stage=fetch f={frame}"
                     " actualFetchedPC=82D4F2 fetchedOpcode=64 S=01F0 v=226 h=964 wai=0")
            ordinal+=1
            o.append(f"QA01RF081ORIG seq={ordinal} stage=setbyte_enter f={frame} pc=82D4F2"
                     " D=0000 addr=000059 value=00 committed=0 v=226 h=970 phase=source_local")
            ordinal+=1
            o.append(f"QA01RF081ORIG seq={ordinal} stage=after_stz_opcode f={frame} pc=82D4F2"
                     " D=0000 addr=000059 value=00 committed=1 v=226 h=995 phase=source_local")
    n=[]
    for line in native.splitlines():
        n.append(line)
        if "stage=bpl_actual_input" in line:
            frame=int(re.search(r" f=(\d+)",line).group(1))
            n.append(f"QA01RF047NATIVE seq=0 stage=opcode f={frame} master=201 guestPC=82D4F2 tier=aot")
            n.append(f"QA01RF047NATIVE seq=0 stage=stz_real_commit f={frame} master=209"
                     " guestPC=82D4F2 D=0000 bank=00 addr=0059 written=00 rawAfter=00")
            n.append(f"QA01RF047NATIVE seq=0 stage=opcode f={frame} master=217 guestPC=82D4F4 tier=aot")
    for i,line in enumerate(n,1):
        n[i-1]=re.sub(r"seq=\d+",f"seq={i}",line, count=1)
    return "\n".join(o)+"\n","\n".join(n)+"\n"

class StzFirstWriter(unittest.TestCase):
    def test_true_first_writer_and_after_commit_for_both_frames(self):
        o,n=fixture()
        data=m.parse(o,n)
        self.assertEqual(data["real_common_direct_page_STZ_write_count_qualified"],2)
        self.assertTrue(data["same_guest_operands_and_committed_zero_values_proven_locally"])
        self.assertFalse(data["equivalent_original_native_instruction_phase_proven"])
        self.assertFalse(data["first_persistent_gameplay_state_divergence_proven"])
        self.assertEqual(data["accepted_USA_events"],0)
        self.assertEqual(data["frames"][0]["original_true_STZ_dispatch_completed"]["host_physical_RAM_mirror"],"00")
        self.assertEqual(data["frames"][0]["native_true_paced_STZ_committed"]["source_master_cycle"],209)
        self.assertEqual(data["frames"][0]["original_local_vh_ticks_first_BPL_post_execution_to_true_setbyte_entry"],26)
        self.assertFalse(data["frames"][0]["cross_emulator_subtraction_valid"])

    def test_wrong_source_actual_write_value_or_effective_address_is_a_failure(self):
        o,n=fixture()
        for oo,nn in (
            (o.replace("stage=setbyte_enter f=1017 pc=82D4F2 D=0000 addr=000059",
                       "stage=setbyte_enter f=1017 pc=82D4F2 D=0000 addr=00005A",1),n),
            (o.replace("stage=setbyte_enter f=1017 pc=82D4F2 D=0000 addr=000059 value=00",
                       "stage=setbyte_enter f=1017 pc=82D4F2 D=0000 addr=000059 value=01",1),n),
            (o.replace("stage=after_stz_opcode f=1017 pc=82D4F2 D=0000 addr=000059 value=00",
                       "stage=after_stz_opcode f=1017 pc=82D4F2 D=0000 addr=000059 value=FF",1),n),
            (o.replace("committed=1","committed=0",1),n),
            (o.replace("actualFetchedPC=82D4F2 fetchedOpcode=64",
                       "actualFetchedPC=82D4F3 fetchedOpcode=64",1),n),
            (o,n.replace("guestPC=82D4F2 D=0000 bank=00",
                         "guestPC=82D4F2 D=0001 bank=00",1)),
            (o,n.replace("addr=0059 written=00","addr=0058 written=00",1)),
            (o,n.replace("written=00 rawAfter=00","written=00 rawAfter=FF",1)),
            (o,n.replace("guestPC=82D4F2 D=0000 bank=00","guestPC=82D4F2 D=0000 bank=01",1))
        ):
            with self.subTest(case=oo[:35]+nn[:35]),self.assertRaises(ValueError):
                m.parse(oo,nn)

    def test_missing_actual_source_does_not_turn_marker_into_write(self):
        o,n=fixture()
        for oo,nn in (
            (o.replace("QA01RF081ORIG seq=1 stage=setbyte_enter","QA01RF081_FAKE seq=1 stage=setbyte_enter",1),n),
            (o,n.replace("stage=stz_real_commit","stage=stz_unproved_marker",1)),
            (o,n.replace("stage=opcode f=1017 master=217 guestPC=82D4F4",
                         "stage=opcode f=1017 master=217 guestPC=82D4F5",1)),
            (o+"QA01RF081ORIG_TRUNCATED\n",n),
            (o,n+"QA01RF081NATIVE_STZ_MISSING_WRITE\n"),
        ):
            with self.assertRaises(ValueError):
                m.parse(oo,nn)

    def test_archive_requires_isolated_native_sidecar_and_preserves_stderr(self):
        o,n=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"case.zip"
            with zipfile.ZipFile(path,"w") as z:
                z.writestr(previous.ORIG,o)
                z.writestr(previous.NATIVE,"OLD_PREFIX_FRAGMENT "+n)
                z.writestr(previous.STRICT_SIDECAR,n)
            report=m.inspect_archive(path)
            self.assertTrue(report["previous_two_frame_real_BIT_BPL_read_report_qualified"])
            self.assertFalse(report["raw_native_stderr_RF047_ordinal_continuity_assumed"])
            self.assertEqual(report["real_common_direct_page_STZ_write_count_qualified"],2)

if __name__=="__main__":
    unittest.main()
