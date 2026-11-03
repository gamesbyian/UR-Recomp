"""ROM-free colourway tie-preservation and index-provenance source tests."""
import unittest
from tools.art.audit_original_index_regions import grouped_descriptors
from tools.art.audit_original_racer_palette_indices import digest

def example(indices,touched,rgba,centres):
    return {"indices":indices,"touched":touched,
            "expected_index_sha256":digest(indices),
            "expected_touched_sha256":digest(touched),
            "rgba_sha256":rgba,"centres":centres}

class AuthenticatedSourceGroupTests(unittest.TestCase):
    def test_palette_variants_do_not_erase_tied_source_ring_hypotheses(self):
        indices=bytearray(4096);touched=bytearray(4096)
        indices[10*64+10]=7;touched[10*64+10]=1
        i=bytes(indices);t=bytes(touched)
        first=example(i,t,"a"*64,[[10,10,7]])
        second=example(i,t,"b"*64,[[11,10,7],[10,10,7]])
        grouped=grouped_descriptors([first,second])
        self.assertEqual(len(grouped),1)
        row=next(iter(grouped.values()))
        self.assertEqual(row["source_colourway_image_count"],2)
        self.assertEqual(len(row["regions"]["7"]["source_wheel_centre_hypotheses"]),2)
        self.assertTrue(row["all_colourway_2d_ring_hypotheses_retained"])
    def test_identical_plane_with_different_written_provenance_refused(self):
        indices=bytearray(4096);indices[10*64+10]=7
        touched=bytearray(4096);touched[10*64+10]=1
        first=example(bytes(indices),bytes(touched),"a"*64,[[10,10,7]])
        touched[11*64+11]=1
        other=example(bytes(indices),bytes(touched),"b"*64,[[10,10,7]])
        with self.assertRaisesRegex(ValueError,"divergent"):
            grouped_descriptors([first,other])
    def test_sha_mismatch_refused(self):
        plane=bytes(4096);touched=bytes(4096)
        row=example(plane,touched,"a"*64,[[10,10,7]])
        row["expected_index_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"changed"):
            grouped_descriptors([row])
if __name__=="__main__":
    unittest.main()
