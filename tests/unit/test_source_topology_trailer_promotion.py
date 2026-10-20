"""ROM-free promotion contract checks for authentic course montage editing."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"tools/showcase/promote_source_verified_topology_trailers.py"
SPEC=importlib.util.spec_from_file_location("ur_topology_promotion",SCRIPT)
m=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

class TrailerReplacementContractTest(unittest.TestCase):
    def test_four_lengths_preserved_and_all_three_course_parts_present(self):
        for name,meta in m.FILMS.items():
            with self.subTest(name=name):
                secs,w,h,spans=meta[2],meta[3],meta[4],meta[5]
                self.assertEqual(sum(b-a for a,b,_ in spans),secs*60)
                self.assertIn("1920" if w==1920 else "1080",str(w))
                source=[(a,b) for a,b,isreel in spans if isreel]
                self.assertTrue(source)
                self.assertEqual(sum(b-a for a,b in source),600 if w==1920 else 360 if secs==27 else 300)
                self.assertEqual(len(source),2 if secs==85 else 3 if h>w else 1)
    def test_course_order_and_genuine_film_resolution_constraints(self):
        self.assertEqual(m.FEATURES,["loop","ramp","hill"])
        for name,meta in m.FILMS.items():
            graph=m.derive_feature_reel_graph(1,meta[5],meta[4]>meta[3])
            self.assertIn("trim=start_frame=",graph)
            self.assertIn("concat=n=",graph)
            self.assertNotIn("minterpolate",graph)
            self.assertNotIn("setpts=0.5",graph)
            self.assertNotIn("overlay",graph)
            if meta[4]>meta[3]:
                self.assertIn("scale=1080:608",graph)
                self.assertIn("pad=1080:1920:0:656",graph)
            else:
                self.assertNotIn("pad=1080:1920",graph)
    def test_film_names_are_new_not_overwritten_originals(self):
        for key,meta in m.FILMS.items():
            self.assertNotEqual(meta[0],meta[1])
            self.assertTrue(meta[1].endswith(".mp4"))
            self.assertIn("true-course-action",meta[1])

if __name__=="__main__":
    unittest.main()
