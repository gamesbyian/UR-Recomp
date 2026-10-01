#!/usr/bin/env python3
import unittest

from tools.run_pal_da65_adjudication import PROBES, info_text


class PalDa65AdjudicationTests(unittest.TestCase):
    def test_info_file_contains_bounded_code_ranges_and_modes(self):
        p=next(x for x in PROBES if x['id']=='reset-init')
        t=info_text(p)
        self.assertIn('RANGE { START $91D1; END $91D4; TYPE CODE; ADDRMODE "MX"', t)
        self.assertIn('RANGE { START $9318; END $932E; TYPE CODE; ADDRMODE "mx"', t)

    def test_selected_probes_do_not_overlap_invalidly(self):
        for p in PROBES:
            prev=None
            for a,b,mode,_ in p['ranges']:
                self.assertLessEqual(a,b)
                self.assertIn(mode, {'MX','Mx','mX','mx'})
                if prev is not None:
                    self.assertEqual(a,prev+1)
                prev=b
            self.assertEqual(p['ranges'][0][0],p['start'])
            self.assertEqual(p['ranges'][-1][1],p['end'])


if __name__=="__main__": unittest.main()
