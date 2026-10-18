"""RF056: source-qualified input frames are not a substitute for actual CPU reads."""
from pathlib import Path
import sys, unittest
from tempfile import TemporaryDirectory
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf056_bowl_supplied_input_onset_bridge as rf

class RF056SuppliedInput(unittest.TestCase):
    def input_rows(self):
        prefix=[(i,1,0x80) for i in range(586)]
        tail=[(4687,1,0x80),(4688,1,0x40),(4689,7,0x80),
              (4696,2,0x280),(4698,1,0x80),(4699,1,0x280),(4700,9,0x80)]
        return prefix+tail
    def test_593_identical_masks_and_one_native_host_frame_shift(self):
        source=self.input_rows()
        native=[(f+1,n,m) for f,n,m in source]
        result=rf.crosswalk(source,native)
        self.assertEqual(result["original_to_native_supplied_input_host_frame_offset"],1)
        self.assertEqual(result["raw_fresh_original_to_native_mutation_onset_frame_displacement"],3)
        self.assertEqual(result["state_mutation_onset_lag_beyond_supplied_input_shift"],2)
        self.assertFalse(result["actual_guest_CPU_controller_bus_consumption_observed"])
        self.assertEqual(result["source_guest_frame_input_windows"]["fresh_native_first_mutation"]["elapsed_host_frames_since_segment_start"],2)
        self.assertEqual(result["complete_USA_event_acceptance_credit"],0)
        rows="\n".join(f"{f}:{n}:{m:03X}" for f,n,m in source).encode()
        self.assertEqual(rf.parse_events(rows),source)
    def test_bad_offset_duration_mask_and_missing_frame_are_rejected(self):
        ref=self.input_rows()
        native=[(f+1,n,m) for f,n,m in ref]
        for label,changed in (
            ("wrong native shift",native[:-7]+[(f+1,n,m) for f,n,m in native[-7:]]),
            ("wrong native mask",native[:-5]+[(4690,7,0x81)]+native[-4:]),
            ("wrong native duration",native[:-5]+[(4690,6,0x80)]+native[-4:]),
            ("missing native event",native[:-1])
        ):
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError,"not exact|incomplete|classification"):
                    rf.crosswalk(ref,changed)
        with self.assertRaisesRegex(ValueError,"target guest frame"):
            rf.supplying(native,4660)
    def test_bad_input_source_rows_rejected_before_evidence(self):
        for sample,reason in (
            (b"1:1:080\n1:1:080","overlap"),
            (b"1:0:080","invalid"),
            (b"X:1:080","nonnumeric"),
            (b"1:1","malformed"),
            (b"1:1:080","count changed")
        ):
            with self.subTest(sample=sample):
                with self.assertRaisesRegex(ValueError,reason):
                    rf.parse_events(sample)
    def test_full_Wram_stored_controller_candidate_bytes_not_cpu_reads(self):
        a=bytearray(131072); b=bytearray(131072)
        a[0x72:0x76]=b[0x72:0x76]=bytes.fromhex("80A48580")
        values=rf.raw_cross_guest_candidate_input_state(bytes(a),bytes(b))
        self.assertEqual(values["7E:0072..0075"]["source_original_hex"],"80A48580")
        self.assertEqual(values["7E:030D..0310"]["native_guest_hex"],"00000000")
        self.assertTrue(values["7E:008F"]["identical_full_raw_bytes"])
        b[0x30d]=0x80
        with self.assertRaisesRegex(ValueError,"already unequal"):
            rf.raw_cross_guest_candidate_input_state(bytes(a),bytes(b))
        with self.assertRaisesRegex(ValueError,"complete unmasked"):
            rf.raw_cross_guest_candidate_input_state(bytes(a[:-1]),bytes(b))
    def test_no_unpinned_real_archives_are_admitted(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)/"spoof.zip"
            p.write_bytes(b"fake")
            with self.assertRaisesRegex(ValueError,"artifact SHA256 mismatch"):
                rf.report(p,p)

if __name__=="__main__":unittest.main()
