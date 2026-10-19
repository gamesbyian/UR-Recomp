"""RF059: independent exact-producer and full-image source archive negatives."""
from pathlib import Path
import sys,unittest
from tempfile import TemporaryDirectory
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf059_authentic_original_native_scene_case_audit as rf

class RF059FullSourceArchive(unittest.TestCase):
    def producers(self):
        old={"reference_core_sha256":rf.OLD_CORE_SHA,
             "comparison":{"next_bowl_relative":267,"same_frame_Wram_equal":False},
             "rom_sha256":"exact-rom","input_sha256":"exact-script",
             "bowl_next_switcher_handoff":{"original":341,"native":344}}
        new=dict(old,reference_core_sha256=rf.NEW_CORE_SHA,
                 comparison=dict(old["comparison"],
                                  **{rf.DIAGNOSTIC_KEY:False}),
                 dragster_next_zoo_handoff=None)
        return new,old
    def test_only_qualified_original_core_and_two_additive_metadata_changes(self):
        new,old=self.producers()
        rf.certify_producer(new,old)
        changes=(
           (dict(new,rom_sha256="changed"),"source ROM"),
           (dict(new,input_sha256="other"),"source ROM"),
           (dict(new,reference_core_sha256="unknown"),"core rebuild"),
           (dict(new,dragster_next_zoo_handoff={"fake":1}),"Dragster"),
           (dict(new,extra="other"),"source ROM"),
           (dict(new,comparison=dict(new["comparison"],
              **{rf.DIAGNOSTIC_KEY:True})),"comparison"),
           (dict(new,bowl_next_switcher_handoff={"original":341,"native":345}),"source ROM"),
        )
        for altered,error in changes:
            with self.subTest(error=error):
                with self.assertRaisesRegex(ValueError,error):
                    rf.certify_producer(altered,old)
    def memory(self):
        data={}
        for kind,size in (("wram",131072),("sram",8192)):
            for mode in ("ref","native"):
                for f in (334,338,339,340,341,342,343,344,345,346,349,354):
                    data[f"bowl/replay/{mode}/bowl-next-switcher-{f}.{kind}.bin"]=bytes(size)
            for f in (334,339,340,341,342,343,344,354):
                data[f"bowl/source/source-bowl-switcher-{f}.{kind}.bin"]=bytes(size)
        return data
    def test_all_64_unmasked_entire_original_native_movie_images(self):
        raw=self.memory()
        self.assertEqual(rf.certify_images(raw,raw)["raw_original_native_historical_whole_images_equal"],64)
        k="bowl/replay/ref/bowl-next-switcher-340.wram.bin"
        corrupt=dict(raw);b=bytearray(raw[k]);b[0x126B]=1;corrupt[k]=bytes(b)
        with self.assertRaisesRegex(ValueError,"entire guest"):
            rf.certify_images(corrupt,raw)
        with self.assertRaisesRegex(ValueError,"missing original"):
            rf.certify_images({k:v for k,v in raw.items() if k!="bowl/source/source-bowl-switcher-334.wram.bin"},raw)
        with self.assertRaisesRegex(ValueError,"incomplete full"):
            rf.certify_images(dict(raw,**{k:raw[k][:-1]}),raw)
    def test_reject_untrusted_original_or_native_artifacts(self):
        with TemporaryDirectory() as folder:
            fake=Path(folder)/"case.zip";fake.write_bytes(b"wrong source")
            with self.assertRaisesRegex(ValueError,"ZIP SHA256"):
                rf.certify_archive(fake,fake)

if __name__=="__main__":unittest.main()
