"""Synthetic 7:6 Original-PAR matte witness; never claims real GPU pixels."""
from fractions import Fraction
MODES={'original':(256,224),'world342':(342,224)}
# The accepted world342 host-fit is 16:9; its 342x224 logical extent is
# approximately, not mathematically exactly, 16:9 under 7:6 source PAR.
HOST_RATIOS={'original':Fraction(4,3),'world342':Fraction(16,9)}
def viewport(mode,width,height):
 if mode not in MODES or type(width) is not int or type(height) is not int or width<1 or height<1:
  raise ValueError('invalid viewport')
 ratio=HOST_RATIOS[mode]
 if Fraction(width,height)>=ratio:
  h=height;w=(h*ratio.numerator)//ratio.denominator
 else:
  w=width;h=(w*ratio.denominator)//ratio.numerator
 return ((width-w)//2,(height-h)//2,w,h)
def matte_pixel_count(mode,width,height):
 _,_,w,h=viewport(mode,width,height)
 return width*height-w*h
def audit_matte(mode,width,height,rgba,matte=(0,0,0,255)):
 if type(rgba) is not bytes or len(rgba)!=width*height*4 or len(matte)!=4:
  raise ValueError('invalid host raster')
 x,y,w,h=viewport(mode,width,height);expected=bytes(matte)
 bad=0
 for row in range(height):
  for col in range(width):
   if not (x<=col<x+w and y<=row<y+h):
    i=4*(row*width+col)
    bad+=(rgba[i:i+4]!=expected)
 return {'schema':'synthetic-matte-audit/1','viewport_xywh':[x,y,w,h],
         'matte_pixels':matte_pixel_count(mode,width,height),'bad_matte_pixels':bad,
         'matte_consistent':bad==0,'gpu_capture_proven':False,'art_approved':False}
