"""RF069 executable proof gate: no silently uninstrumented original getter."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf069_original_getset_binary_audit as rf

GROUPS={
    "read_byte":"_Z10S9xGetBytej",
    "read_word":"_Z10S9xGetWordj9s9xwrap_t",
    "write_byte":"_Z10S9xSetBytehj",
    "write_word":"_Z10S9xSetWordtj9s9xwrap_t15s9xwriteorder_t",
}

def fixture(clone=False):
    names=list(GROUPS.values())
    if clone: names.append(GROUPS["read_word"]+".constprop.0")
    nm="".join(f"{0x45200+i*4096:016x} t {n}\n" for i,n in enumerate(names))
    dis={n:f"0000000000045200 <{n}>:\n   45205: e8 28 47 fe ff    call 2fb70 <getenv@plt>\n"
         for n in names}
    return nm,dis

class SourceBuildELFProof(unittest.TestCase):
    def test_all_symbol_variants_really_instrumented(self):
        nm,dis=fixture(clone=True)
        r=rf.audit(nm,dis)
        self.assertTrue(r["all_original_read_and_write_variants_have_probe_guard"])
        self.assertEqual(len(r["original_executable_getset_variants"]["read_word"]),2)
        self.assertFalse(r["guest_ROM_executed"])
        self.assertEqual(r["accepted_USA_events"],0)

    def test_original_real_archived_elf_read_functions_uninstrumented(self):
        # Authentic RF066 original ELF (run 39219862021) had getter
        # functions with no getenv guard while S9xSetWord did have one.
        nm,dis=fixture(clone=True)
        for name in list(dis):
            if name.startswith(GROUPS["read_word"]):
                dis[name]=f"0000000000045200 <{name}>:\n   45205: 89 f8    mov %edi,%eax\n"
        with self.assertRaisesRegex(ValueError,"stale/uninstrumented"):
            rf.audit(nm,dis)

    def test_rejects_uninstrumented_byte_or_constprop_clone(self):
        nm,dis=fixture(clone=True)
        for which in (GROUPS["read_byte"],GROUPS["read_word"]+".constprop.0"):
            with self.subTest(which=which):
                d={**dis,which:f"0000000000045200 <{which}>:\n 45205: ret\n"}
                with self.assertRaises(ValueError):
                    rf.audit(nm,d)

    def test_missing_getter_is_not_assumed_compiled(self):
        nm,dis=fixture()
        nm=nm.replace(f" t {GROUPS['read_word']}\n"," t unrelated_symbol\n")
        with self.assertRaisesRegex(ValueError,"function missing"):
            rf.audit(nm,dis)

    def test_fake_string_literal_or_wrong_symbol_not_accepted(self):
        nm,dis=fixture()
        name=GROUPS["read_word"]
        for alt in ("getenv@plt", "call 2fb70 <puts@plt>"):
            d={**dis,name:f"0000000000045200 <{name}>:\n 45205: mov {alt},%eax\n"}
            with self.assertRaises(ValueError):
                rf.audit(nm,d)

    def test_missing_disassembly_or_wrong_symbol_rejected(self):
        nm,dis=fixture()
        d=dict(dis)
        d.pop(GROUPS["read_byte"])
        with self.assertRaises(ValueError):
            rf.audit(nm,d)


if __name__=="__main__":
    unittest.main()
