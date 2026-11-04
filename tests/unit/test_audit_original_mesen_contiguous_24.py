"""ROM-free math/provenance guards for exact historical Mesen24 auditor."""
import hashlib
import unittest

from tools.art.audit_original_mesen_contiguous_24 import (
    compare_masks,compare_rgba,summarize,audit,TICKS,ZIP_SHA,ANCHORS,SCHEMA,
)


class Source24UnitTests(unittest.TestCase):
    def test_all_archive_identity_pins_and_proof_types(self):
        self.assertEqual(len(TICKS),24)
        self.assertEqual(TICKS,tuple(range(1601,1625)))
        self.assertEqual(sorted(ANCHORS),[1601,1607,1618])
        self.assertTrue(all(len(x)==64 and set(x)<=set("0123456789abcdef")
                            for r in ANCHORS.values() for x in r))
        self.assertEqual(len(ZIP_SHA),64)
        self.assertTrue(SCHEMA.endswith("/1"))

    def test_mask_and_rgba_census_are_not_metadata_only(self):
        a=bytes([1,0])+bytes(4094)
        b=bytes([0,1])+bytes(4094)
        self.assertEqual(compare_masks(a,b),2)
        self.assertEqual(compare_masks(a,a),0)
        self.assertEqual(compare_rgba(b"\x00\x00\x00\x00"*4096,
                                      b"\x00\x00\x00\x00"*4096),0)
        red=bytearray(4*4096);red[3]=255
        self.assertEqual(compare_rgba(bytes(4*4096),bytes(red)),1)
        for broken in (a[:-1],bytes([2])+a[1:]):
            with self.assertRaisesRegex(ValueError,"binary"):
                compare_masks(a,broken)
        with self.assertRaisesRegex(ValueError,"RGBA"):
            compare_rgba(b"",bytes(4096*4))

    def test_temporal_reducer_uses_actual_adjacent_bytes_and_counts_holds(self):
        rows=[]
        for i,t in enumerate(TICKS):
            alpha=bytearray(4096);alpha[i]=1
            plane=bytes(alpha)
            rgba=bytearray(4096*4);rgba[4*i:4*i+4]=b"\x10\x20\x30\xff"
            rows.append({"tick":t,"source_alpha_sha256":hashlib.sha256(alpha).hexdigest(),
                         "source_rgba_sha256":hashlib.sha256(rgba).hexdigest(),
                         "_alpha":bytes(alpha),"_rgba":bytes(rgba),"_plane":plane,
                         "_descriptor":("unchanged",)})
        stats=summarize(rows)
        self.assertEqual(stats["source_alpha_changed_edges"],23)
        self.assertEqual(stats["source_alpha_held_edges"],0)
        self.assertEqual(stats["alpha_changed_pixels_median"],2)
        self.assertEqual(stats["distinct_source_alpha_masks"],24)
        self.assertEqual(stats["source_rgba_changed_edges"],23)
        self.assertFalse(any(x["source_oam_descriptor_changed"]
                             for x in stats["authentic_adjacent_source_2d_transitions"]))
        rows[1]=dict(rows[0],tick=TICKS[1])
        held=summarize(rows)
        self.assertEqual(held["source_alpha_held_edges"],1)
        self.assertEqual(held["distinct_source_alpha_masks"],23)
        with self.assertRaisesRegex(ValueError,"authentic contiguous"):
            summarize(rows[1:])

    def test_unknown_archive_or_wrong_bytes_fail_closed(self):
        for raw in (b"",b"PK\x03\x04"+bytes(100),bytes(1000001)):
            with self.assertRaisesRegex(ValueError,"preserved actual"):
                audit(raw)


if __name__=="__main__":
    unittest.main()
