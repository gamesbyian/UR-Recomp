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
    dis={n:(f"0000000000045200 <{n}>:\n"
            "   45205: e8 28 47 fe ff    call 2fb70 <getenv@plt>\n"
            "   45215: e8 28 47 fe ff    call 2fb70 <getenv@plt>\n"
            "   45225: 48 8b 05  mov 0x3486cf(%rip),%rax # <ur_rf063_source_bus_seq>\n"
            "   45235: e8 8e dc fe ff  call 2fd10 <__fprintf_chk@plt>\n")
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

    def test_genuine_clean_LTO_word_getter_calls_audited_outlined_helper(self):
        # Actual freshly clean rebuilt Snes9x has two S9xGetWord variants
        # that call the local 2014 RF044/RF063 recorder helper rather than
        # invoking getenv directly. Verify the entire call edge + helper.
        nm,dis=fixture(clone=True)
        helper=rf.HELPER_PREFIX+".lto_priv.0"
        nm+="0000000000041ef0 t "+helper+"\n"
        for name in list(dis):
            if name.startswith(GROUPS["read_word"]):
                dis[name]=(f"0000000000046160 <{name}>:\n"
                           f"  461ae: e8 3d bd ff ff  call 41ef0 <{helper}>\n")
        dis[helper]=(f"0000000000041ef0 <{helper}>:\n"
                     " 41f13: e8 58 dc fe ff  call 2fb70 <getenv@plt>\n"
                     " 41f78: e8 f3 db fe ff  call 2fb70 <getenv@plt>\n"
                     " 41f82: 48 8b 05   mov 0x3486cf(%rip),%rax  # <ur_rf063_source_bus_seq>\n"
                     " 4207d: e8 8e dc fe ff  call 2fd10 <__fprintf_chk@plt>\n")
        result=rf.audit(nm,dis)
        self.assertEqual(result["verified_outlined_RF044_RF063_helper_symbols"],[helper])
        for name in (GROUPS["read_word"],GROUPS["read_word"]+".constprop.0"):
            self.assertEqual(
                result["per_original_executable_variant_probe_mechanism"]["read_word"][name],
                "call_verified_outlined_original_RF044_RF063_recorder")
        for defect in (
                dis[helper].replace("<ur_rf063_source_bus_seq>","<unrelated>"),
                dis[helper].replace("call 2fb70 <getenv@plt>","call 2fb70 <getenv@plt>",1)
                .replace(" 41f78: e8 f3 db fe ff  call 2fb70 <getenv@plt>\n",""),
                dis[helper].replace("<__fprintf_chk@plt>","<no_log>"),
                dis[helper].replace(f"<{helper}>:","<different_helper>:")
            ):
            with self.subTest(defect=defect[:60]), self.assertRaisesRegex(ValueError,"stale/uninstrumented"):
                rf.audit(nm,{**dis,helper:defect})

    def test_unrelated_helper_call_cannot_impersonate_verified_original(self):
        nm,dis=fixture()
        name=GROUPS["read_word"]
        dis[name]=(f"0000000000046160 <{name}>:\n"
                   " 461ae: e8 3d bd ff ff  call 41ef0 <any_helper>\n")
        with self.assertRaisesRegex(ValueError,"stale/uninstrumented"):
            rf.audit(nm,dis)

    def test_direct_incidental_getenv_without_ordinal_or_real_logger_rejected(self):
        nm,dis=fixture()
        name=GROUPS["read_byte"]
        for altered in (
                dis[name].replace("<ur_rf063_source_bus_seq>","<unrelated>"),
                dis[name].replace("<__fprintf_chk@plt>","<irrelevant>"),
                dis[name].replace("   45215: e8 28 47 fe ff    call 2fb70 <getenv@plt>\n","")):
            with self.subTest(mode=altered[:45]),self.assertRaisesRegex(ValueError,"stale/uninstrumented"):
                rf.audit(nm,{**dis,name:altered})

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
