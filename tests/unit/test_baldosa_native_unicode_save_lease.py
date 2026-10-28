"""Regression for real Win32 non-ACP Modern profile save leases.

A UTF-8 string must not be passed through std::filesystem::path(string)
on Windows: that constructor uses the active ANSI code page. The source
already holds a native filesystem::path and the lock exposes a native overload.
The actual Windows P1/P2 cold-boot test remains the product oracle.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
ACTIVATION = ROOT / "tools" / "baldosa_modern_profile_activation.cpp"
LOCK = ROOT / "native" / "product" / "local_tournament_launch_path_lock.hpp"

LOCK_CONSTRUCTION = re.compile(
    r"(?:std::make_unique<ur::product::TournamentLaunchPathLock>\\s*\\("
    r"|(?:ur::product::)?TournamentLaunchPathLock\\s+\\w+\\s*\\()"
)


def lock_arguments(source: str) -> list[str]:
    arguments = []
    for match in LOCK_CONSTRUCTION.finditer(source):
        start = match.end()
        depth = 1
        end = start
        while end < len(source) and depth:
            if source[end] == "(":
                depth += 1
            elif source[end] == ")":
                depth -= 1
            end += 1
        if depth:
            raise AssertionError("unclosed TournamentLaunchPathLock constructor")
        arguments.append(source[start:end - 1])
    return arguments


class NativeUnicodeSaveLeaseTests(unittest.TestCase):
    def test_all_modern_activation_leases_keep_native_paths(self):
        source = ACTIVATION.read_text(encoding="utf-8")
        arguments = lock_arguments(source)
        # These 13 include selector/catalog/profile save leases plus
        # result, checkpoint and two-player publication paths.
        self.assertEqual(len(arguments), 13)
        for args in arguments:
            with self.subTest(args=args):
                self.assertIn(", true", args)
                self.assertNotIn(".u8string()", args)
                self.assertNotIn(".string()", args)
        self.assertIn('g_native_user_root / "host-state-v1.txt"', source)
        self.assertIn("profile_path, true", source)

    def test_native_lock_preserves_os_exclusion_and_failure_semantics(self):
        source = LOCK.read_text(encoding="utf-8")
        self.assertIn(
            "TournamentLaunchPathLock(const std::filesystem::path& target,",
            source,
        )
        self.assertIn("CreateFileW(", source)
        self.assertIn("LOCKFILE_FAIL_IMMEDIATELY", source)
        self.assertIn("LOCKFILE_EXCLUSIVE_LOCK", source)
        self.assertIn("UnlockFileEx(", source)
        self.assertIn("flock(fd_, LOCK_EX", source)


if __name__ == "__main__":
    unittest.main()
