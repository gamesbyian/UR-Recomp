"""RF072: real original physical stack read-first fate, never infer native."""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf072_original_postnmi_first_byte_fates as src


def row(seq,kind,addr,width,value,frame=1017):
    return (f"QA01RF063ORIGBUS seq={seq} f={frame} v=226 h=700"
            f" kind={kind} bank=00 addr={addr:04X} width={width}"
            f" sampled={value:04X} pc=80:B0EB S=01ED phase=getset_entry\n")


def fixture(first_writer=False):
    cp=("QA01RF063ORIGCHECKPOINT seq=1 f=1017 f1=1017"
        " phase=post_real_nmi_push stack=26F0D48226 v=225 h=78 pc=00:8588\n")
    order=[(2,"rb",0x01ed,1,0x26),
           (3,"rw",0x01ee,2,0xd4f0),
           (4,"rb",0x01f0,1,0x82),
           (5,"rb",0x01f1,1,0x26),
           (6,"ww",0x01ed,2,0x85b9),
           (7,"ww",0x01ef,2,0x0001),
           (8,"wb",0x01f1,1,0)]
    if first_writer:
        order=[(2,"wb",0x01ed,1,0x33)]+[(x+1,k,a,w,v) for x,k,a,w,v in order]
    log=cp+"".join(row(*x) for x in order)
    reads=[]
    for seq,kind,base,width,value in order:
        if kind[0]=="r":
            reads.append({"source_getset_seq":seq,"physical_bus_address":f"00:{base:04X}",
                          "bus_kind":kind,"host_frame":1017,"returned":f"{value:04X}"})
    return log,reads


class RealOriginalStackByteFates(unittest.TestCase):
    def test_all_five_true_reads_precede_first_source_writers(self):
        log,rows=fixture()
        result=src.fates(log,rows)
        self.assertTrue(result["all_five_original_bytes_have_a_real_qualified_read_before_next_observed_write"])
        expected=["26","F0","D4","82","26"]
        for address,value in zip(src.ADDRESSES,expected):
            v=result["source_original_byte_fates"][f"00:{address:04X}"]
            self.assertEqual(v["checkpoint_byte"],value)
            self.assertEqual(v["first_actual_original_byte_read"]["raw_byte"],value)
            self.assertLess(v["first_actual_original_byte_read"]["source_global_seq"],
                            v["first_observed_original_byte_write"]["source_global_seq"])
            self.assertFalse(v["no_unobserved_other_path_writers_proven"])
        self.assertFalse(result["native_first_differing_byte_actual_reader_proven"])
        self.assertFalse(result["eligible_for_QA01_causal_window"])
        self.assertEqual(result["accepted_USA_events"],0)

    def test_prior_original_stack_write_blocks_unwarranted_read_first_claim(self):
        log,rows=fixture(first_writer=True)
        out=src.fates(log,rows)
        self.assertFalse(out["all_five_original_bytes_have_a_real_qualified_read_before_next_observed_write"])
        self.assertEqual(out["source_original_byte_fates"]["00:01ED"]["fate_in_recorded_original_getset_window"],
                         "first_observed_write_precedes_read")

    def test_unbound_getset_entry_cannot_be_promoted_to_real_return(self):
        log,rows=fixture()
        for missing in (rows[0],rows[1]):
            with self.subTest(seq=missing["source_getset_seq"]),self.assertRaisesRegex(ValueError,"not qualified"):
                src.fates(log,[r for r in rows if r is not missing])

    def test_raw_return_checkpoint_conflict_or_fake_nmi_rejected(self):
        log,rows=fixture()
        for variant in (
            log.replace("sampled=0026","sampled=0027",1),
            log.replace("stack=26F0D48226","stack=27F0D48226"),
            log.replace("phase=post_real_nmi_push","phase=guess"),
            log.replace("QA01RF063ORIGCHECKPOINT","QA01RF063FAKE"),
        ):
            with self.subTest(variant=variant[:60]),self.assertRaises(ValueError):
                src.fates(variant,rows)
        tampered=[{**rows[0],"returned":"0027"}]+rows[1:]
        with self.assertRaisesRegex(ValueError,"not qualified"):
            src.fates(log,tampered)

    def test_unauthenticated_archive_is_not_a_genuine_source_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"fake-case.zip"
            p.write_bytes(b"not the frozen exact USA case")
            with self.assertRaisesRegex(ValueError,"SHA256 mismatch"):
                src.authenticated_case(p)


if __name__=="__main__":
    unittest.main()
