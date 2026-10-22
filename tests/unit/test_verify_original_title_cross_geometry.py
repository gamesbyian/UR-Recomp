#!/usr/bin/env python3
"""ROM-free negative for UR-UHD-01 H31 candidate: equal nonblack count != same P6.

Uses only synthetic pixels and the recovered source verifier, with a complete
provenance-consistent ZIP. Expected secure behavior: reject differing P6 bytes
between two geometry captures that claim the same guest frame and source epoch.
"""
import hashlib
import importlib.util
import io
import json
import unittest
import tempfile
import zipfile
from pathlib import Path

RECOVERED = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('mapping', RECOVERED/'tools/verify_original_title_sdl_rgb_mapping.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
tspec = importlib.util.spec_from_file_location('synthetic_test', RECOVERED/'tests/unit/test_verify_original_title_sdl_rgb_mapping.py')
t = importlib.util.module_from_spec(tspec)
tspec.loader.exec_module(t)

class CrossGeometryMappingTest(unittest.TestCase):
    def test_same_source_frame_digest_required(self):
        cases = {}
        for mode in m.CASES:
            src, host, offset = t.synthetic(mode)
            if mode == '4by3':
                # One nonblack source pixel changes, and all its true SDL nearest pixels
                # change with it. Every individual P6/P7 mapping remains exact.
                sx0, sy0 = 100, 100
                p = (sy0*256+sx0)*3
                src = bytearray(src)
                source_offset = len(b'P6\n256 224\n255\n')
                src[source_offset+p] ^= 1
                src = bytes(src)
                host = bytearray(host)
                (hw,hh),(left,top,vw,vh)=m.CASES[mode]
                for y in range(vh):
                    sy=((2*y+1)*224)//(2*vh)
                    if sy != sy0: continue
                    for x in range(vw):
                        sx=((2*x+1)*256)//(2*vw)
                        if sx==sx0:
                            host[offset+((y+top)*hw+(x+left))*4] ^= 1
                host=bytes(host)
            self.assertEqual(m.compare(src,host,mode)['viewport_rgb_mismatches'], 0)
            cases[mode]=(src,host)
        self.assertNotEqual(m.digest(cases['wide'][0]), m.digest(cases['4by3'][0]))
        self.assertEqual(m.compare(*cases['wide'],'wide')['source_nonblack_pixels'],m.compare(*cases['4by3'],'4by3')['source_nonblack_pixels'])

        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'two-source-frames.zip'
            with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
                for mode,(src,host) in cases.items():
                    prefix=f'modern-title-original-attract-sdl-{mode}-pr2043/'
                    base=prefix+'original-title/'
                    dims=m.CASES[mode][0]
                    witness={'guest_frame':1200,'original_rendered_before_sdl':{'sha256':m.digest(src)},'actual_sdl_pixel_buffer_sha256':m.digest(m._pam(host,dims))}
                    receipt={'exact_native_source_sha':'synthetic-source-epoch','one_actual_windows_aot_pe_sha256':'synthetic-pe','actual_native_sdl_output':list(dims),'real_original_guest_and_controller_source_stage_log':[{'stage':'original-title','sdl_raw_p7_sha256':m.digest(host)}]}
                    for name,payload in [('original-presdl.ppm',src),('native-sdl.pam',host),('original-title-source-vs-sdl.json',json.dumps(witness).encode())]:
                        z.writestr(base+name,payload)
                    z.writestr(prefix+'real-stock-title-demo-wake-sdl-receipt.json',json.dumps(receipt).encode())
            try:
                m.audit(path,m.digest(path.read_bytes()),'synthetic-source-epoch','synthetic-pe')
            except ValueError as exc:
                self.assertIn('P6 source frame differs', str(exc))
            else:
                self.fail('FAIL-OPEN: different same-frame P6 SHA256 accepted across geometry')


if __name__ == "__main__":
    unittest.main()
