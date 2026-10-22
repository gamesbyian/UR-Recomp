"""ROM-free host-filesystem observation for Records Win32 ADS namespace review.

This is an independent platform discriminator, not an earned-run export fix,
release qualification, or proof of exploitability. See issue #2103.
"""
import os
from pathlib import Path
import tempfile
import unittest


class WindowsAdsNamespaceObservation(unittest.TestCase):
    def test_colon_qualified_sidecar_and_current_census(self):
        with tempfile.TemporaryDirectory(prefix="ur-records-ads-") as temp:
            root = Path(temp)
            canonical = root / "earned.urrun"
            canonical.write_bytes(b"synthetic fixture, not a game record")
            colon_path = root / "shadow:stream.urrun"
            try:
                colon_path.write_bytes(b"synthetic ADS marker")
            except OSError as exc:
                if os.name == "nt":
                    self.skipTest(f"Windows filesystem does not permit ADS probe: {exc}")
                raise

            names = {entry.name for entry in root.iterdir()}
            # This is the exact historical enumeration expression in the
            # exporter, intentionally reproduced here without changing it.
            candidates = [
                entry.name for entry in root.iterdir()
                if entry.name.split(":", 1)[0].rstrip(" .").casefold().endswith(".urrun")
            ]
            self.assertEqual(candidates, ["earned.urrun"])
            self.assertEqual(canonical.read_bytes(), b"synthetic fixture, not a game record")
            if os.name == "nt":
                # NTFS stream syntax creates a stream on the 'shadow' base;
                # directory enumeration does not expose the stream spelling.
                self.assertIn("shadow", names)
                self.assertNotIn("shadow:stream.urrun", names)
                self.assertEqual(colon_path.read_bytes(), b"synthetic ADS marker")
            else:
                # POSIX treats the same spelling as a separate directory entry,
                # which the exporter census currently ignores.
                self.assertIn("shadow:stream.urrun", names)
                self.assertNotIn("shadow", names)


if __name__ == "__main__":
    unittest.main()
