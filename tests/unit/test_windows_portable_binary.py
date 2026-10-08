"""Release PE/Windows-inbox import gate, independent of runner tools."""
from __future__ import annotations

import pathlib
import struct
import tempfile
import unittest

from tools import check_windows_portable_binary as binary


def dumpbin(*names: str, delay: tuple[str, ...] = ()) -> str:
    normal = "\n".join(f"    {name}" for name in names)
    late = (
        "\n  Image has the following delay load dependencies:\n\n"
        + "\n".join(f"    {name}" for name in delay)
    ) if delay else ""
    return (
        "Microsoft (R) COFF/PE Dumper Version 14\n"
        "Dump of file UniracersSNESRecomp.exe\n"
        "File Type: EXECUTABLE IMAGE\n\n"
        "  Image has the following dependencies:\n\n"
        + normal + late + "\n\n  Summary\n"
    )


def fake_pe(path: pathlib.Path, *, machine: int = 0x8664,
            magic: int = 0x20B) -> None:
    payload = bytearray(160)
    payload[:2] = b"MZ"
    struct.pack_into("<I", payload, 0x3C, 0x80)
    payload[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<H", payload, 0x84, machine)
    struct.pack_into("<H", payload, 0x98, magic)
    path.write_bytes(payload)


class WindowsPortableBinaryTests(unittest.TestCase):
    def test_accepts_stock_windows_imports_and_api_sets(self):
        actual = binary.check_dependencies(dumpbin(
            "KERNEL32.dll", "USER32.dll", "DWMAPI.dll", "ucrtbase.dll",
            "api-ms-win-core-file-l1-1-0.dll",
            delay=("XINPUT1_4.DLL", "ext-ms-win-ntuser-window-l1-1-0.dll"),
        ))
        self.assertIn("xinput1_4.dll", actual)
        self.assertEqual(len(actual), 7)

    def test_rejects_unbundled_sdl_and_compiler_dlls(self):
        for name in (
            "SDL3.dll", "libwinpthread-1.dll", "libomp.dll",
            "VCRUNTIME140.dll", "MSVCP140.dll", "vcomp140.dll",
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, name.lower().replace(".", r"\.")):
                    binary.check_dependencies(dumpbin("KERNEL32.dll", name))

    def test_rejects_delayed_non_system_dependency(self):
        with self.assertRaisesRegex(ValueError, "sdl3.dll"):
            binary.check_dependencies(dumpbin(
                "KERNEL32.dll", delay=("SDL3.dll",)
            ))

    def test_rejects_empty_or_unparseable_dumpbin_output(self):
        for data in ("", "dumpbin: error: cannot open executable",
                     "Image has the following dependencies:\n\n Summary"):
            with self.subTest(data=data):
                with self.assertRaisesRegex(ValueError, "no readable PE dependency"):
                    binary.check_dependencies(data)

    def test_deduplicates_imports_case_insensitively(self):
        self.assertEqual(
            binary.imported_dlls(dumpbin("kernel32.dll", "KERNEL32.DLL")),
            ("kernel32.dll",),
        )

    def test_accepts_real_x64_pe_header(self):
        with tempfile.TemporaryDirectory() as directory:
            exe = pathlib.Path(directory) / "game.exe"
            fake_pe(exe)
            binary.check_pe_x64(exe)

    def test_rejects_32_bit_and_invalid_pe_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            exe = pathlib.Path(directory) / "game.exe"
            for machine, magic in ((0x14C, 0x10B), (0x8664, 0x10B)):
                with self.subTest(machine=machine, magic=magic):
                    fake_pe(exe, machine=machine, magic=magic)
                    with self.assertRaisesRegex(ValueError, "AMD64 PE32"):
                        binary.check_pe_x64(exe)
            exe.write_bytes(b"not a PE")
            with self.assertRaisesRegex(ValueError, "not a Windows PE"):
                binary.check_pe_x64(exe)

    def test_release_workflow_checks_imports_before_assembly(self):
        root = pathlib.Path(__file__).resolve().parents[2]
        workflow = (root / ".github/workflows/windows-native-smoke.yml").read_text()
        check = workflow.index("python tools/check_windows_portable_binary.py")
        assemble = workflow.index("python tools/assemble_windows_package.py assemble")
        self.assertLess(check, assemble)
        self.assertIn("--exe \"$EXE\"", workflow)
        self.assertIn(
            '--dependencies "$RUNNER_TEMP/windows-runtime-dependencies.log"',
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
