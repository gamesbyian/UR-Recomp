"""ROM-free QA08 future chromatic probe identifiability, not pixel evidence."""
from fractions import Fraction
from itertools import permutations
MODELS={'renderer_14_over_15':Fraction(14,15),'alternative_187_over_200':Fraction(187,200)}
def expanded(v):
 if type(v) is not int or not 0<=v<=31:raise ValueError('RGB5 channel out of range')
 return (v<<3)|(v>>2)
def predicted(v,model):
 if model not in MODELS:raise ValueError('unknown brightness model')
 return expanded(v)*MODELS[model].numerator//MODELS[model].denominator
def interval(value,tolerance):
 if type(value) is not int or type(tolerance) is not int or tolerance<0:raise ValueError('invalid observation bound')
 return (max(0,value-tolerance),min(255,value+tolerance))
def distinguishable(v,tolerance=1):
 a,b=(interval(predicted(v,m),tolerance) for m in MODELS)
 return a[1]<b[0] or b[1]<a[0]
def census():
 delta=max(abs(predicted(v,'renderer_14_over_15')-predicted(v,'alternative_187_over_200')) for v in range(32))
 return {'schema':'qa08-chromatic-probe-identifiability/1','rgb5_channels_checked':32,
         'largest_quantized_model_gap':delta,
         'all_single_channel_probes_ambiguous_at_plus_minus_one':all(not distinguishable(v,1) for v in range(32)),
         'max_unquantized_model_gap':str(Fraction(255,600)),
         'all_six_channel_orders_ambiguous_under_bounded_noise':all(
             not any(distinguishable(v,1) for v in (0,17,31)) for _ in permutations((0,17,31))),
         'native_ppu_pixel_observed':False,'release_gate_credit':0}
