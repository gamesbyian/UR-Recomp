"""Synthetic source-identity tests for a reproducible Original art contact sheet."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from tools.art import build_qa08_original_contact_sheet as art


def fake_originals(destination: Path, *, corrupt: bool = False):
    title = bytes((10, 12, 14, 255)) * (256 * 224)
    race = bytes((17, 18, 19, 255)) * (342 * 224)
    items = {
        "title.pam": (256, 224, title),
        "race.pam": (342, 224, race),
    }
    slots = {}
    for slot in (96, 97, 98, 99):
        data = bytearray(342 * 224 * 4)
        i = 4 * (342 * 60 + 50 + (slot - 96) * 10)
        data[i:i+4] = bytes((31, 41, 51, 255))
        data = bytes(data)
        name = ("baldosa-ws342-obj-slots/"
                f"ur-baldosa-ws342-obj-slot{slot}-frame002208.pam")
        items[name] = (342, 224, data)
        slots[slot] = (1, hashlib.sha256(data).hexdigest())
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as z:
        for name, (w, h, data) in items.items():
            if name == "title.pam" and corrupt:
                data = bytes((7, 8, 9, 255)) * (w * h)
            z.writestr(name, art.header(w, h) + data)
    return ((("title.pam", 256, 224, hashlib.sha256(title).hexdigest()),
             ("race.pam", 342, 224, hashlib.sha256(race).hexdigest()),
             slots))


class OriginalReferenceSheetTests(unittest.TestCase):
    def test_six_exact_authentic_structure_sources_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "fixture.zip"
            title, race, slots = fake_originals(archive)
            out = root / "sheet.html"
            with (patch.object(art, "TITLE", title),
                  patch.object(art, "RACE", race),
                  patch.object(art, "SLOTS", slots)):
                result = art.build(archive, out)
            self.assertTrue(out.exists())
            text = out.read_text()
            self.assertEqual(text.count('src="data:image/png;base64,'), 7)
            self.assertIn("CSS-only exposure x4", text)
            self.assertIn("SNES 7:6 pixel aspect", text)
            self.assertEqual(result["title_max_original_RGB8"], 14)
            self.assertEqual(result["isolated_source_slots"]["96"]
                             ["crop_native_xyxy_inclusive"], [45, 55, 55, 65])
            self.assertFalse(result["HD_character_likeness_approved"])
            self.assertEqual(json.loads(out.with_suffix(".json").read_text()),
                             result)

    def test_original_source_RGBA_hash_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "altered.zip"
            title, race, slots = fake_originals(archive, corrupt=True)
            with (patch.object(art, "TITLE", title),
                  patch.object(art, "RACE", race),
                  patch.object(art, "SLOTS", slots)):
                with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                    art.build(archive, root / "out.html")
            self.assertFalse((root / "out.html").exists())

    def test_absent_racer_alpha_and_malformed_P7_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "empty original"):
            art.source_crop(bytes(342*224*4), 342, 224)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "wrong.zip"
            with zipfile.ZipFile(dest, "w") as z:
                z.writestr("x.pam", b"junk")
            with zipfile.ZipFile(dest) as z:
                with self.assertRaisesRegex(ValueError, "byte size"):
                    art.read_exact(z, "x.pam", 342, 224, "0"*64)


if __name__ == "__main__":
    unittest.main()
