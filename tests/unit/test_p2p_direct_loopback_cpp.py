#!/usr/bin/env python3
"""Two REAL process local UDP probe; NOT network netplay or an auth proof."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'tools/p2p/direct_udp_loopback_lab.cpp'
NONCE = '1234567890abcdef1234567890abcdef'
SIM = 'ab' * 16
WRONG_SIM = 'cd' * 16


class DirectLoopbackOnlyLabTests(unittest.TestCase):
    def test_explicit_two_process_one_way_contact(self):
        compiler = shutil.which('g++') or shutil.which('clang++')
        if not compiler:
            self.skipTest('C++17 compiler unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / ('loopback_probe.exe' if os.name == 'nt' else 'loopback_probe')
            command = [compiler, '-std=c++17', '-O1', '-Wall', '-Wextra',
                       '-Werror', '-pedantic', str(SOURCE), '-o', str(exe)]
            if os.name == 'nt':
                command.append('-lws2_32')
            compiled = subprocess.run(command, capture_output=True, text=True,
                                      timeout=35)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            missing_consent = subprocess.run([str(exe), 'listen', NONCE, SIM],
                  text=True, capture_output=True, timeout=5)
            self.assertEqual(missing_consent.returncode, 2)
            # There is no service daemon: the listener is just the other
            # temporary peer process with a one-time OS-assigned port.
            listener = subprocess.Popen(
                [str(exe), '--allow-loopback-only', 'listen', NONCE, SIM],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                self.assertIsNotNone(listener.stdout)
                ready = listener.stdout.readline().strip()
                result = re.fullmatch(r'READY udp@127\.0\.0\.1:([1-9][0-9]{0,4})',ready)
                self.assertIsNotNone(result,ready)
                dial = subprocess.run(
                    [str(exe), '--allow-loopback-only', 'dial', NONCE, SIM,
                     result.group(1)], text=True, capture_output=True, timeout=5)
                self.assertEqual(dial.returncode, 0, dial.stderr)
                self.assertIn('DIRECT local-two-process-probe-only',dial.stdout)
                remaining, errors = listener.communicate(timeout=5)
                self.assertEqual(listener.returncode,0,errors)
                self.assertIn('ACCEPTED local-direct-probe-only',remaining)
                # A distinct simulation identity is refused rather than
                # treating a reachable peer as a compatible game.
                incompatible = subprocess.Popen(
                    [str(exe), '--allow-loopback-only', 'listen', NONCE, SIM],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                try:
                    self.assertIsNotNone(incompatible.stdout)
                    ready2 = incompatible.stdout.readline().strip()
                    found2 = re.fullmatch(
                        r'READY udp@127\\.0\\.0\\.1:([1-9][0-9]{0,4})',ready2)
                    self.assertIsNotNone(found2, ready2)
                    mismatch = subprocess.run(
                        [str(exe), '--allow-loopback-only', 'dial', NONCE,
                         WRONG_SIM, found2.group(1)], text=True,
                        capture_output=True, timeout=6)
                    self.assertNotEqual(mismatch.returncode, 0)
                    incompatible.communicate(timeout=6)
                    self.assertEqual(incompatible.returncode, 6)
                finally:
                    if incompatible.poll() is None:
                        incompatible.kill()
                        incompatible.communicate(timeout=5)
            finally:
                if listener.poll() is None:
                    listener.kill()
                    listener.communicate(timeout=5)

if __name__=='__main__':
    unittest.main()
