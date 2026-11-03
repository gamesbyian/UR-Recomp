"""Synthetic adversarial source topology cases: no ROM, GLB or viewer required."""
import unittest
from tools.art.index_region_descriptors import describe_index_regions

def fixture(points, transparent=()):
    indices=bytearray(4096); touched=bytearray(4096)
    for x,y,value in points:
        i=64*y+x;indices[i]=value;touched[i]=1
    for x,y in transparent:touched[64*y+x]=1
    return bytes(indices),bytes(touched)

class SourceTopologyTests(unittest.TestCase):
    def test_connected_components_and_exact_perimeters(self):
        a,b=fixture([(10,10,3),(11,10,3),(20,20,3),(12,10,7)])
        x=describe_index_regions(a,b,[[10,10,7],[20,20,7]])["regions"]["3"]
        self.assertEqual(x["component_areas"],[2,1])
        self.assertEqual(x["four_connected_perimeter"],10)
        self.assertEqual(x["adjacency_edges"]["7"],1)
        self.assertEqual([r["in_source_disc"] for r in x["source_wheel_centre_hypotheses"]],[2,1])
    def test_palette_zero_written_and_untouched_remain_distinct(self):
        a,b=fixture([(8,8,4)],[(9,9),(10,10)])
        r=describe_index_regions(a,b,[[8,8,7]])["regions"]
        self.assertEqual(r["16"]["pixels"],2)
        self.assertEqual(r["17"]["pixels"],4093)
        self.assertEqual(sum(x["pixels"] for x in r.values()),4096)
    def test_colours_cannot_affect_index_topology(self):
        a,b=fixture([(8,8,3),(9,8,3)])
        self.assertEqual(describe_index_regions(a,b,[[8,8,7]]),
                         describe_index_regions(a,b,[[8,8,7]]))
    def test_diagonal_contact_not_four_connected(self):
        a,b=fixture([(8,8,4),(9,9,4)])
        self.assertEqual(describe_index_regions(a,b,[[8,8,7]])["regions"]["4"]["component_areas"],[1,1])
    def test_invalid_source_provenance_fails_closed(self):
        a,b=fixture([(8,8,4)])
        for i,t,c in ((bytes([16])+a[1:],b,[[8,8,7]]),
                      (a,bytes(4096),[[8,8,7]]),
                      (a,b,[]),(a,b,[[8,8,6]]),(a,b,[[64,8,7]])):
            with self.assertRaises(ValueError):
                describe_index_regions(i,t,c)

if __name__ == "__main__":
    unittest.main()
