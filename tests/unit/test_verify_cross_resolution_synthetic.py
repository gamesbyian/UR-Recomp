"""Synthetic two-resolution SDL witness controls; no ROM, private captures or release credit."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

try:
    import numpy as np
    from PIL import Image
    HAS_OPTIONAL_DEPS = True
except ImportError:
    HAS_OPTIONAL_DEPS = False

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
if HAS_OPTIONAL_DEPS:
    import verify_cross_resolution as witness


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def png(arr):
    out = io.BytesIO()
    Image.fromarray(arr).save(out, format='PNG')
    return out.getvalue()


@unittest.skipUnless(HAS_OPTIONAL_DEPS, 'optional NumPy/Pillow cross-resolution research')
class CrossResolutionSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.a, self.b = root / '856.zip', root / '1280.zip'
        yy, xx = np.meshgrid(np.arange(224, dtype=np.uint16),
                             np.arange(342, dtype=np.uint16), indexing='ij')
        src = np.stack(((xx*37+yy*11)%256, (xx*17+yy*43)%256,
                        (xx*19+yy*7)%256), axis=-1).astype(np.uint8)

        def frame(w, h):
            sx, sy, vx, vy = witness.viewport(w, h, 342)
            ix = np.clip(np.floor((np.arange(w)+.5-vx)/sx).astype(int), 0, 341)
            iy = np.clip(np.floor((np.arange(h)+.5-vy)/sy).astype(int), 0, 223)
            return src[iy[:, None], ix[None, :]]

        self.png_a, self.png_b = png(frame(856, 480)), png(frame(1280, 720))
        self.log_a = (witness.ROOT_LINE+'\n'+witness.CAPTURE_856+'\n').encode()
        self.log_b = (witness.ROOT_LINE+'\n'+witness.CAPTURE_1280+'\n').encode()
        self.pam_a, self.pam_b = b'synthetic-P7-856', b'synthetic-P7-1280'
        def receipt(w,h,log,pam,png_bytes):
            return dict(source_sha='a'*40,exe_sha256='b'*64,
                        native_semantic_route='root-quit',
                        actual_sdl_renderer_output=[w,h],
                        native_process_log_sha256=digest(log),
                        p7_sha256=digest(pam),png_sha256=digest(png_bytes))
        self.rec_a = receipt(856,480,self.log_a,self.pam_a,self.png_a)
        self.rec_b = receipt(1280,720,self.log_b,self.pam_b,self.png_b)
        self.pack()

    def pack(self, *, log=None, receipt=None, png_data=None):
        log = self.log_a if log is None else log
        receipt = self.rec_a if receipt is None else receipt
        png_data = self.png_a if png_data is None else png_data
        with zipfile.ZipFile(self.a, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('readback-receipt.json', json.dumps(receipt).encode())
            z.writestr('capture_observed/native-process.log', log)
            z.writestr('capture_observed/actual-sdl-drawable.pam', self.pam_a)
            z.writestr('actual-sdl-drawable.png', png_data)
        prefix = 'ur-modern-win32-visual-1280x720/'
        with zipfile.ZipFile(self.b, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(prefix+'readback-receipt.json',json.dumps(self.rec_b).encode())
            z.writestr(prefix+'probe_first/native-process.log',self.log_b)
            z.writestr(prefix+'probe_first/actual-sdl-drawable.pam',self.pam_b)
            z.writestr(prefix+'actual-sdl-drawable.png',self.png_b)

    def test_synthetic_same_source_and_pe_prefers_342_canvas(self):
        result = witness.verify(self.a,self.b)
        self.assertEqual(result['candidate_342']['different_pixels'],0)
        self.assertGreater(result['candidate_256']['different_pixels'],0)
        self.assertEqual(result['root_source_log'],[342,224])
        self.assertIn('no release gate credit',result['scope'])

    def test_rejects_different_executable_receipt(self):
        self.pack(receipt={**self.rec_a,'exe_sha256':'c'*64})
        with self.assertRaisesRegex(ValueError,'same PE/source'):
            witness.verify(self.a,self.b)

    def test_rejects_mutated_native_log_and_rehashed_wrong_stage(self):
        changed = self.log_a.replace(b'raster=342x224',b'raster=256x224')
        self.pack(log=changed)
        with self.assertRaisesRegex(ValueError,'source artifact hash mismatch'):
            witness.verify(self.a,self.b)
        self.pack(log=changed,receipt={**self.rec_a,'native_process_log_sha256':digest(changed)})
        with self.assertRaisesRegex(ValueError,'missing source-verified'):
            witness.verify(self.a,self.b)

    def test_rejects_mutated_rgb_artifact(self):
        self.pack(png_data=self.png_a+b'changed')
        with self.assertRaisesRegex(ValueError,'source artifact hash mismatch'):
            witness.verify(self.a,self.b)


if __name__ == '__main__':
    unittest.main()
