"""Keep the vendored reference core's embedded version independent of host PR SHA."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class Snes9xVendoredVersionTests(unittest.TestCase):
    def test_pinned_make_override_matches_exact_vendored_revision(self):
        entry = json.loads((ROOT / 'tools/toolchain-entries/snes9x-libretro.json').read_text())
        island = json.loads((ROOT / 'third_party/manifest.json').read_text())
        vendor = next(c for c in island['components'] if c['id'] == 'snes9x-libretro')
        self.assertEqual(vendor['mode'], 'vendored')
        self.assertEqual(entry['revision'], vendor['revision'])
        self.assertEqual(entry['build'], [
            ['make', '-C', 'libretro', '-j{jobs}',
             'GIT_VERSION=+' + entry['revision'][:7]],
        ])
        makefile = (ROOT / vendor['source_path'] / 'libretro/Makefile').read_text()
        source = (ROOT / vendor['source_path'] / 'libretro/libretro.cpp').read_text()
        self.assertIn('GIT_VERSION := " $(shell git rev-parse --short HEAD || echo unknown)"', makefile)
        self.assertIn('info->library_version = VERSION GIT_VERSION;', source)

    @unittest.skipUnless(shutil.which('make') and shutil.which('git'), 'requires make and git')
    def test_make_command_line_override_beats_host_repository_sha(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / 'host'
            vendor = repo / '.tools/src/snes9x-libretro/libretro'
            vendor.mkdir(parents=True)
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Test',
                            '-c', 'user.email=test@example.invalid', 'commit',
                            '--allow-empty', '-qm', 'host revision'], check=True)
            (vendor / 'Makefile').write_text(
                'GIT_VERSION := " $(shell git rev-parse --short HEAD || echo unknown)"\n'
                'all:\n\t@printf "%s\\n" "$(GIT_VERSION)"\n')
            def run(*args):
                return subprocess.check_output(['make', '-s', '-C', str(vendor), *args],
                                               text=True).strip()
            host_sha = subprocess.check_output(
                ['git', '-C', str(repo), 'rev-parse', '--short', 'HEAD'], text=True).strip()
            self.assertIn(host_sha, run())
            self.assertEqual(run('GIT_VERSION=+1bcc369'), '+1bcc369')
            self.assertNotIn(host_sha, run('GIT_VERSION=+1bcc369'))


if __name__ == '__main__':
    unittest.main()
