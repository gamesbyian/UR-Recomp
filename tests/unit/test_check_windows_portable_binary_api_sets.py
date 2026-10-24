"""ROM-free import policy regression for the Windows portable PE.

An API-set namespace prefix alone does not prove that an arbitrary named
contract is present on stock Windows 10/11. This checks the source-level
preflight, not a physical Windows launch or release acceptance.
"""
from __future__ import annotations

import unittest

from tools.check_windows_portable_binary import check_dependencies


def dumpbin(*names: str, delay: tuple[str, ...] = ()) -> str:
    lines = ["Dump of file UniracersSNESRecomp.exe", "Image has the following dependencies:"]
    lines.extend("    " + name for name in names)
    if delay:
        lines.append("Image has the following delay load dependencies:")
        lines.extend("    " + name for name in delay)
    lines.append("Summary")
    return "\n".join(lines) + "\n"


class WindowsPortableApiSetImportContract(unittest.TestCase):
    def test_exact_windows_candidate_imports_remain_accepted(self):
        # Observed from the successful 2026-10-22 Windows build job
        # 119978303187, workflow run 39822833034; no API-set imports.
        observed = (
            "KERNEL32.dll", "COMDLG32.dll", "USER32.dll", "dbghelp.dll",
            "bcrypt.dll", "WINMM.dll", "ADVAPI32.dll", "ole32.dll",
            "SETUPAPI.dll", "SHELL32.dll", "GDI32.dll", "OLEAUT32.dll",
            "IMM32.dll", "VERSION.dll",
        )
        self.assertEqual(check_dependencies(dumpbin(*observed)),
                         tuple(sorted(name.lower() for name in observed)))

    def test_fabricated_api_set_names_do_not_bypass_inbox_check(self):
        for name in (
            "api-ms-win-nonexistent-l1-1-0.dll",
            "ext-ms-win-nonexistent-l1-1-0.dll",
            "API-MS-WIN-UNREVIEWED-L1-1-0.DLL",
            "api-ms-win-crt-runtime-l1-1-0.dll",
        ):
            with self.subTest(name=name), self.assertRaisesRegex(
                    ValueError, "non-inbox DLLs"):
                check_dependencies(dumpbin("KERNEL32.dll", name))

    def test_unqualified_delay_import_is_also_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-inbox DLLs"):
            check_dependencies(dumpbin("KERNEL32.dll", delay=(
                "ext-ms-win-not-a-real-contract-l1-1-0.dll",)))
        self.assertEqual(check_dependencies(dumpbin(
            "KERNEL32.dll", delay=("USER32.dll",))),
            ("kernel32.dll", "user32.dll"))


if __name__ == "__main__":
    unittest.main()
