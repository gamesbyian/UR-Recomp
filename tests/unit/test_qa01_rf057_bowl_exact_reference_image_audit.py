"""RF057 genuine-run exact archive comparison rejects masks, drift, missing samples."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf057_bowl_exact_reference_image_audit as rf

class RealBowlNoninvasiveness(unittest.TestCase):
    def images(self):
        out={}
        for kind,size in (("wram",131072),("sram",8192)):
            for g in ("ref","native"):
                for offset in (334,338,339,340,341,342,343,344,345,346,349,354):
                    out[f"bowl/replay/{g}/bowl-next-switcher-{offset}.{kind}.bin"]=bytes(size)
            for offset in (334,339,340,341,342,343,344,354):
                out[f"bowl/source/source-bowl-switcher-{offset}.{kind}.bin"]=bytes(size)
        return out
    def test_all_64_real_raw_images_must_be_equal(self):
        data=self.images()
        x=rf.compare_raw(data,data)
        self.assertEqual(x["original_native_full_WRAM_SRAM_raw_images_exact"],48)
        self.assertEqual(x["historical_source_movie_full_WRAM_SRAM_raw_images_exact"],16)
        self.assertEqual(x["unmasked_bytes_excluded"],0)
        p="bowl/replay/ref/bowl-next-switcher-340.wram.bin"
        bad=dict(data)
        c=bytearray(data[p]);c[0xC6]=1
        bad[p]=bytes(c)
        with self.assertRaisesRegex(ValueError,"raw image diverged"):
            rf.compare_raw(data,bad)
        with self.assertRaisesRegex(ValueError,"missing or extra"):
            rf.compare_raw(data,{k:v for k,v in data.items() if k!=p})
        with self.assertRaisesRegex(ValueError,"incomplete full"):
            rf.compare_raw(data,dict(data,**{p:data[p][:-1]}))
    def test_untrusted_source_baseline_rejected(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as d:
            p=Path(d)/"case.zip";p.write_bytes(b"no real USA case")
            with self.assertRaisesRegex(ValueError,"baseline SHA256"):
                rf.report(p,p)

if __name__=="__main__":unittest.main()
