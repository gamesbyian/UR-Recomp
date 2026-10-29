"""Windows legacy-migration smoke must preserve unowned fixed-name stages."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/windows-native-smoke.yml"
STAGES = (
    ".ur-recomp-saves.migrate.tmp/stale.srm",
    ".ur-recomp-config.ini.migrate.tmp",
    ".ur-recomp-keybinds.ini.migrate.tmp",
    ".ur-recomp-mod-state.toml.migrate.tmp",
)


class WindowsLegacyStageSmokeContract(unittest.TestCase):
    def test_both_migration_launches_preserve_fixed_stage_bytes(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        block = source.split("- name: Legacy portable state migrates once", 1)[1].split(
            "- name: Boot to main menu", 1
        )[0]
        for path in STAGES:
            with self.subTest(path=path):
                target = '"$MIGRATED/' + path + '"'
                self.assertEqual(
                    block.count("printf 'stale-temp\\n' | cmp -s - " + target), 2
                )
                self.assertNotIn("test ! -e " + target, block)
        self.assertEqual(
            block.count('test -d "$MIGRATED/.ur-recomp-saves.migrate.tmp"'), 2
        )
        self.assertIn('echo "WINDOWS_PACKAGE_LEGACY_MIGRATION ok"', block)


if __name__ == "__main__":
    unittest.main()
