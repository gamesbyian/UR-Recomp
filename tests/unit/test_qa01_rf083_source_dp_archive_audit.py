"""RF083 offline auditor fail-closed schema and corrupted-evidence controls."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf083_source_dp_archive_audit as m

HEARTS="".join("QA01RF083ORIG_HEART frame=%d v=0 h=0\n"%f
               for f in range(6069,6080))
EVENT=("QA01RF083ORIG seq=1 type=opcode_delta frame=6072"
       " pc=8280E0 op=E6 pre_v=0 pre_h=12 post_v=0 post_h=42"
       " slot=0069 old=9F new=A0 setterCount=0 setterAddr=FFFFFFFF"
       " setterVal=00 clock=original_cpu\n")

class RealOriginalObserverAudit(unittest.TestCase):
    def test_real_opcode_event_and_source_local_coverage(self):
        e,h=m.parse_trace(HEARTS+EVENT)
        self.assertEqual(len(e),1)
        self.assertEqual(h,list(range(6069,6080)))
        self.assertEqual(e[0]["pc"],"8280E0")

    def test_false_original_trace_evidence_rejected(self):
        variants=(
            HEARTS+EVENT.replace("seq=1","seq=2"),
            HEARTS+EVENT+EVENT,
            HEARTS+EVENT.replace("slot=0069","slot=0079"),
            HEARTS+EVENT.replace("pc=8280E0","pc=BAD"),
            HEARTS+EVENT.replace("clock=original_cpu","clock=native_host"),
            HEARTS+EVENT.replace("old=9F new=A0","old=9F new=9F"),
            HEARTS+EVENT+"QA01RF083ORIG_TRUNCATED\n",
            HEARTS.replace("frame=6073","frame=6069")+EVENT,
            HEARTS.replace("frame=6073 v=0 h=0\n","")+EVENT,
            HEARTS+EVENT.replace("op=E6","op=E6 extra=yes"),
            HEARTS+EVENT.replace("op=E6","op=E6 op=E6"),
        )
        for text in variants:
            with self.subTest(text=text[-75:]),self.assertRaises(ValueError):
                m.parse_trace(text)

    def test_zip_sha_and_raw_counter_fail_closed(self):
        import hashlib,json,tempfile,zipfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            paths=[Path(td)/s for s in ("before.zip","after.zip")]
            for i,p in enumerate(paths):
                with zipfile.ZipFile(p,"w") as z:
                    z.writestr("producer-report.json",json.dumps({
                        "rom_sha256":"a","original_movie_sha256":"b",
                        "source_sram_sha256":"c","native_executable_sha256":"d",
                        "reference_core_sha256":str(i),
                        "zoo_race_mesh":{"release_complete_usa_event_credit":0}}))
                    z.writestr(m.PREFIX+"reference.log",HEARTS+EVENT)
                    z.writestr(m.PREFIX+"ref/scene-05039.wram.bin",
                               bytes(131072))
            ha=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
            with self.assertRaisesRegex(ValueError,"SHA drift"):
                m.audit(*paths,"0"*64,ha[1],1)
            with self.assertRaisesRegex(ValueError,"number of original"):
                m.audit(*paths,*ha,320)
            with self.assertRaisesRegex(ValueError,"missing genuine"):
                m.audit(*paths,*ha,1)

if __name__=="__main__":unittest.main()
