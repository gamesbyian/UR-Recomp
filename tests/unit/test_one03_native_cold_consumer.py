"""ROM-free production C++ cold-load/replay-stage controls for ONE-03."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROM = '859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478'
BUILD = 'snesrecomp-cd5875cbdaf19f5e324272b1f8051d671fce9215-ur-sim-v1'


def record(rom=ROM, *, corrupt=False):
    body = (f'URRUN 1\ngame uniracers-usa\nrom_sha256 {rom}\n'
            f'build_compat {BUILD}\ncourse course:00\nmode race-1p\n'
            'elapsed_ticks60 1505\nframe_count 2090\nterminal_digest -\n'
            'split finish 1505\ninput 0 1 100 0\nEND\n').encode('ascii')
    value = 14695981039346656037
    for byte in body:
        value = ((value ^ byte) * 1099511628211) & 0xffffffffffffffff
    raw = body + f'checksum {value:016x}\n'.encode('ascii')
    return raw.replace(b'1505', b'1506', 1) if corrupt else raw


class One03NativeColdConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which('c++')
        if not compiler:
            raise unittest.SkipTest('C++ compiler unavailable')
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.tool = Path(cls.tmp.name) / 'one03-cold-consumer'
        subprocess.run([
            compiler, '-std=c++17', '-O0', '-Wall', '-Wextra',
            '-I' + str(ROOT / 'native/product'),
            str(ROOT / 'tests/native/one03_saved_run_native_cold_consumer.cpp'),
            str(ROOT / 'native/product/completed_run_record.cpp'),
            str(ROOT / 'native/product/completed_run_replay.cpp'),
            '-o', str(cls.tool),
        ], check=True, capture_output=True, text=True)

    def setUp(self):
        self.path = Path(self.tmp.name) / 'earned.urrun'
        self.staged = Path(self.tmp.name) / 'staged.input'
        self.path.write_bytes(record())
        self.staged.unlink(missing_ok=True)

    def invoke(self):
        return subprocess.run([str(self.tool), str(self.path), str(self.staged)],
                              capture_output=True, text=True)

    def test_native_cold_load_and_replay_stage(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('ONE03_NATIVE_COLD_CONSUMER PASS', result.stdout)
        self.assertEqual(self.staged.read_bytes(), b'0:1:100:0\n')
        self.assertEqual(self.path.read_bytes(), record())

    def test_native_rejects_foreign_rom_even_with_valid_checksum(self):
        self.path.write_bytes(record(rom='a' * 64))
        result = self.invoke()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(self.staged.exists())

    def test_native_rejects_corrupted_record(self):
        self.path.write_bytes(record(corrupt=True))
        result = self.invoke()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(self.staged.exists())

    def test_native_rejects_missing_record(self):
        self.path.unlink()
        result = self.invoke()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(self.staged.exists())


if __name__ == '__main__':
    unittest.main()
