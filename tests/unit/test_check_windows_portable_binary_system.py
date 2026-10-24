"""ROM-free Windows PE Characteristics acceptance for user-mode portable launch."""
from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from tools.check_windows_portable_binary import check_pe_x64


def pe_fixture(characteristics: int) -> bytes:
    image = bytearray(512)
    image[:2] = b"MZ"
    struct.pack_into("<I", image, 0x3C, 0x80)
    image[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<H", image, 0x84, 0x8664)  # AMD64
    struct.pack_into("<H", image, 0x94, 2)  # declared optional magic
    struct.pack_into("<H", image, 0x96, characteristics)
    struct.pack_into("<H", image, 0x98, 0x20B)  # PE32+
    return bytes(image)


class WindowsPortableSystemImageContract(unittest.TestCase):
    def test_only_user_executable_image_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "game.exe"
            path.write_bytes(pe_fixture(0x0002))
            check_pe_x64(path)
            for characteristics, diagnostic in (
                (0x1002, "system image"),
                (0x3002, "DLL"),
                (0x2002, "DLL"),
                (0x1000, "not a DLL"),
            ):
                with self.subTest(characteristics=hex(characteristics)):
                    path.write_bytes(pe_fixture(characteristics))
                    with self.assertRaisesRegex(ValueError, diagnostic):
                        check_pe_x64(path)


if __name__ == "__main__":
    unittest.main()
