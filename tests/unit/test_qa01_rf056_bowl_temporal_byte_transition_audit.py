"""RF056: only genuine complete-byte mutation triples qualify displaced Bowl state."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf056_bowl_temporal_byte_transition_audit as rf

class BowlCrossFrame(unittest.TestCase):
    def test_full_byte_transition_values_are_authoritative(self):
        original0=bytes((1,2,3,4,5))
        original1=bytes((1,7,3,8,5))
        native0=bytes((1,2,3,4,5))
        native1=bytes((1,7,3,8,5))
        self.assertEqual(rf.transitions(original0,original1),
                         rf.transitions(native0,native1))
        self.assertEqual(rf.transitions(original0,original1),
                         [(1,2,7),(3,4,8)])
        native1_wrong=bytes((1,7,3,9,5))
        self.assertNotEqual(rf.transitions(original0,original1),
                            rf.transitions(native0,native1_wrong))
        with self.assertRaisesRegex(ValueError,"length"):
            rf.full_diff(original0,original1[:-1])
    def test_no_unverified_missing_snapshots_or_partial_guest_memory(self):
        blank=bytes(rf.W_BYTES)
        seed={f:blank for f in rf.FRAMES}
        seed_sram={f:bytes(rf.S_BYTES) for f in rf.FRAMES}
        movie={f:blank for f in rf.MOVIE_FRAMES}
        movie_sram={f:bytes(rf.S_BYTES) for f in rf.MOVIE_FRAMES}
        with self.assertRaisesRegex(ValueError,"SRAM changed"):
            rf.certify(seed,seed,seed_sram,seed_sram,movie,movie_sram)
        with self.assertRaisesRegex(ValueError,"offset set incomplete"):
            rf.certify({f:v for f,v in seed.items() if f!=340},
                       seed,seed_sram,seed_sram,movie,movie_sram)
        with self.assertRaisesRegex(ValueError,"full WRAM"):
            rf.certify({f:(v[:-1] if f==340 else v) for f,v in seed.items()},
                       seed,seed_sram,seed_sram,movie,movie_sram)
    def test_altered_case_zip_is_not_promoted(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"not-a-genuine-case.zip"
            p.write_bytes(b"1234")
            with self.assertRaisesRegex(ValueError,"artifact SHA256 mismatch"):
                rf.report(p)

if __name__=="__main__":unittest.main()
