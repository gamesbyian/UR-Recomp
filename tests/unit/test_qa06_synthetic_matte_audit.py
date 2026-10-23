import unittest
from tools.qa06_synthetic_matte_audit import viewport,matte_pixel_count,audit_matte
class Matte(unittest.TestCase):
 def make(self,mode,w,h):
  return bytearray(b'\x00\x00\x00\xff'*(w*h))
 def test_4k_original_matte(self):
  self.assertEqual(viewport('original',3840,2160),(480,0,2880,2160))
  b=self.make('original',3840,2160)
  r=audit_matte('original',3840,2160,bytes(b))
  self.assertEqual(r['matte_pixels'],2073600);self.assertTrue(r['matte_consistent'])
 def test_4k_world342_matte(self):
  self.assertEqual(viewport('world342',3840,2160),(0,0,3840,2160))
  self.assertEqual(matte_pixel_count('world342',3840,2160),0)
 def test_matte_tampering_detected(self):
  w,h=384,216;b=self.make('original',w,h);b[0]=1
  self.assertEqual(audit_matte('original',w,h,bytes(b))['bad_matte_pixels'],1)
 def test_odd_host_dimensions_bounded(self):
  for mode in ('original','world342'):
   for w,h in ((513,289),(499,281),(17,11)):
    x,y,vw,vh=viewport(mode,w,h)
    self.assertTrue(0<=x and 0<=y and x+vw<=w and y+vh<=h)
 def test_bad_dimensions_and_bytes(self):
  for args in [('original',True,200),('original',200,False),('wrong',200,200)]:
   with self.assertRaises(ValueError):viewport(*args)
  with self.assertRaises(ValueError):audit_matte('original',10,10,b'bad')
if __name__=='__main__':unittest.main()
