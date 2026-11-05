"""Authenticate the original 4bpp index inspector against retained real PNG bytes.

No original ROM execution, index guessing, or 3D-part labels needed: every
loaded 1994 source pixel must reproduce its previously verified ROM index SHA.
"""
import hashlib
import json
from pathlib import Path
import unittest

from tools.art.racer_source_pixels import decode_rgba_png

ROOT=Path(__file__).resolve().parents[2]
LOOKUP=ROOT/"analysis/data/racer-original-index-lookup-20261102.json"
STOCK=ROOT/"media/showcase/art-reconstruction/2026-10-10"
HEX="0123456789abcdef"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def source_plane(rgba, mapping):
    if len(rgba)!=64*64*4:
        raise ValueError("original source must be 64x64 RGBA")
    if any(len(c)!=6 or any(x not in HEX for x in c)
           or type(idx) is not int or not 1<=idx<=15
           for c,idx in mapping.items()) or len(set(mapping.values()))!=len(mapping):
        raise ValueError("ambiguous source palette")
    plane=bytearray(4096)
    for i in range(4096):
        p=rgba[4*i:4*i+4]
        if p[3] == 0:
            continue
        if p[3] != 255:
            raise ValueError("nonbinary source alpha")
        colour=p[:3].hex()
        if colour not in mapping:
            raise ValueError("original pixel colour missing from ROM palette")
        plane[i]=mapping[colour]
    return bytes(plane)


class SourceIndexLookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(LOOKUP.read_text())

    def test_immutable_original_source_authority(self):
        d=self.data
        self.assertEqual(d["schema"],"UR-ART4K-SOURCE-RGBA-TO-4BPP-INDEX-LOOKUP/1")
        self.assertEqual(d["original_usa_rom_sha256"],"859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478")
        self.assertEqual(d["original_source_manifest_sha256"],"e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e")
        self.assertEqual(d["original_source_registry_sha256"],"05372395d04d5403c7b80859c171f06d754f1322a676d66f4ce5d7b3aec948ad")
        self.assertEqual(d["authenticated_full_index_report_sha256"],"b6f59fc5f9030b44ca9345bf308e5df83901f8b9534a6f33b215fa39f8e3079e")
        self.assertEqual((d["source_images_verified"],d["unique_index_planes_verified"]),(41,35))
        self.assertEqual((len(d["representations"]),len(d["rgba_to_index"])),(59,41))
        self.assertEqual(len({v["original_4bpp_index_plane_sha256"] for v in d["rgba_to_index"].values()}),35)
        for key in ("original_3d_part_identity_verified","original_live_ppu_timing_verified","owner_likeness_approved"):
            self.assertIs(d[key],False)

    def test_every_actual_original_first_family_png_recovers_rom_index_plane(self):
        d=self.data
        observed=0
        for player in ("p1","p2"):
            manifest=json.loads((STOCK/("inputs-"+player+".json")).read_text())
            self.assertEqual(len(manifest["frames"]),16)
            for row in manifest["frames"]:
                self.assertEqual(row["player"],player)
                self.assertIn(row["registered_representation_id"],d["representations"])
                self.assertEqual(d["representations"][row["registered_representation_id"]],row["stock_rgba_sha256"])
                spec=d["rgba_to_index"][row["stock_rgba_sha256"]]
                path=STOCK/row["stock_png"]
                w,h,rgba,_=decode_rgba_png(path)
                self.assertEqual((w,h),(64,64))
                self.assertEqual(digest(rgba),row["stock_rgba_sha256"])
                plane=source_plane(rgba,spec["palette_rgb_to_index"])
                self.assertEqual(digest(plane),spec["original_4bpp_index_plane_sha256"])
                mask=bytes(int(v!=0) for v in plane)
                self.assertEqual(digest(mask),spec["source_binary_mask_sha256"])
                observed+=1
        self.assertEqual(observed,32)

    def test_bad_palette_is_rejected_without_original_part_inference(self):
        pixels=bytes([0,0,0,0])*4094+bytes([8,18,28,255])+bytes([255,1,1,255])
        self.assertEqual(source_plane(pixels,{"08121c":3,"ff0101":7})[-2:],bytes([3,7]))
        with self.assertRaises(ValueError):
            source_plane(pixels,{"08121c":3,"ff0101":3})
        with self.assertRaises(ValueError):
            source_plane(pixels,{"08121c":3})


if __name__=="__main__":
    unittest.main()
