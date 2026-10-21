#!/usr/bin/env python3
"""Exact rational host-fit geometry checks; not a physical Windows render."""
from fractions import Fraction as F
import json

def fit(w,h,host_w,host_h,par=F(7,6), horizontal_fit=F(1)):
    logical_w=F(w)*par*horizontal_fit
    scale=min(F(host_w)/logical_w,F(host_h,h))
    width=logical_w*scale
    height=F(h)*scale
    return {'source':[w,h],'par':str(par),'host':[host_w,host_h],
            'physical_extent_exact':[str(width),str(height)],
            'physical_margins_exact':[str((F(host_w)-width)/2),str((F(host_h)-height)/2)],
            'scale_exact':str(scale)}

original=fit(256,224,3840,2160)
wide=fit(342,224,3840,2160,horizontal_fit=F(512,513))
assert F(original['physical_extent_exact'][0])==2880
assert F(original['physical_extent_exact'][1])==2160
assert F(original['physical_margins_exact'][0])==480
assert F(original['physical_margins_exact'][1])==0
assert F(wide['physical_extent_exact'][0])==3840
assert F(wide['physical_extent_exact'][1])==2160
assert F(wide['physical_margins_exact'][1])==0
assert F(342*7,224*6)*F(512,513)==F(16,9)
assert F(342*7,224*6)>F(16,9)
assert F(256*7,224*6)==F(4,3)
print(json.dumps({'scope':'mathematical rational fit only, not an observed physical output',
                  'original':original,'wide':wide,'assertions_passed':9},indent=2))
