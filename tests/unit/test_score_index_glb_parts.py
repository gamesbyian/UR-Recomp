"""No-ROM synthetic holdout, index-reuse and abstention tests."""
import unittest
from tools.art.score_index_glb_parts import propose_index_part_correspondence as score
NAMES={1:"tire",2:"rim_and_hub"}
def square(x,y):return [(x+a,y+b) for a in range(5) for b in range(5)]
def sample(name,family,index,parts,witness=True):
    src=bytearray(4096);model=bytearray(4096)
    for label,coords in index.items():
        for x,y in coords:src[64*y+x]=label
    for label,coords in parts.items():
        for x,y in coords:model[64*y+x]=label
    return {"id":name,"family":family,"source_index_plane":bytes(src),
            "glb_part_ids":bytes(model),"glb_part_id_names":NAMES,
            "independent_pose_alignment_witness":witness}
class SourceGLBMatcherTests(unittest.TestCase):
    def test_two_indices_can_map_to_same_part(self):
        a,b,c=square(2,2),square(10,2),square(30,20)
        d,e,f=square(2,12),square(10,12),square(30,30)
        p=sample("A","upright",{3:a,4:b,7:c},{1:a+b,2:c})
        q=sample("B","wheelie",{3:d,4:e,7:f},{1:d+e,2:f})
        r=score([p,q],["wheelie"],min_margin=.03)
        by={x["original_source_palette_index"]:x for x in r["hypotheses"]}
        self.assertEqual(by[3]["candidate_experimental_3d_parts"],["tire"])
        self.assertEqual(by[4]["candidate_experimental_3d_parts"],["tire"])
        self.assertEqual(by[7]["candidate_experimental_3d_parts"],["rim_and_hub"])
        self.assertFalse(r["source_1994_part_identity_verified"])
    def test_one_index_may_span_two_parts(self):
        a,b,c,d=square(2,2),square(30,20),square(2,12),square(30,30)
        p=sample("A","upright",{3:a+b},{1:a,2:b})
        q=sample("B","wheelie",{3:c+d},{1:c,2:d})
        r=score([p,q],["wheelie"],min_margin=.03)["hypotheses"][0]
        self.assertEqual(set(r["candidate_experimental_3d_parts"]),{"tire","rim_and_hub"})
    def test_heldout_reversal_must_abstain(self):
        a,b,c,d=square(2,2),square(25,20),square(2,12),square(25,30)
        p=sample("A","upright",{3:a,4:b},{1:a,2:b})
        q=sample("B","wheelie",{3:c,4:d},{1:d,2:c})
        r=score([p,q],["wheelie"],min_margin=.03)["hypotheses"][0]
        self.assertEqual(r["classification"],"unresolved")
        self.assertIn("heldout_pose_disagrees",r["reasons"])
    def test_colourway_duplicates_are_not_new_evidence(self):
        a,b=square(2,2),square(25,20)
        p=sample("A","upright",{3:a,4:b},{1:a,2:b})
        q=sample("B","wheelie",{3:a,4:b},{1:a,2:b})
        with self.assertRaisesRegex(ValueError,"duplicate original"):
            score([p,q],["wheelie"])
    def test_unwitnessed_alignment_is_rejected(self):
        a,b,c=square(2,2),square(25,20),square(2,12)
        p=sample("A","upright",{3:a,4:b},{1:a,2:b},witness=False)
        q=sample("B","wheelie",{3:c},{1:c,2:b})
        with self.assertRaisesRegex(ValueError,"independent pose alignment"):
            score([p,q],["wheelie"])
if __name__=="__main__":
    unittest.main()
