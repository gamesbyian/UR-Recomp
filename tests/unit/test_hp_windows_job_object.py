"""Native Windows Job Object process-tree qualification. No service changes."""
import ctypes
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "hp_windows_job_object.py"
spec = importlib.util.spec_from_file_location("hp_windows_job_object", SCRIPT)
jobs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jobs)


@unittest.skipUnless(os.name == "nt", "requires actual Windows Job Object APIs")
class WindowsJobObjectTests(unittest.TestCase):
    def test_suspended_launch_and_exit(self):
        with jobs.ContainedProcess([sys.executable, "-c", "print('containment-ok')"]) as child:
            stdout, stderr = child.communicate(timeout=5)
            self.assertEqual(child.returncode, 0)
            self.assertEqual(stdout.decode().strip(), "containment-ok")
            self.assertEqual(stderr, b"")

    def test_kill_on_close_terminates_grandchild(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "grandchild.pid"
            child_code = "import time; time.sleep(30)"
            parent_code = (
                "import subprocess,sys,time,pathlib;"
                "p=subprocess.Popen([sys.executable,'-c'," + repr(child_code) + "]);"
                "pathlib.Path(" + repr(str(path)) + ").write_text(str(p.pid));"
                "time.sleep(30)"
            )
            parent = jobs.ContainedProcess([sys.executable, "-c", parent_code])
            grandchild_handle = None
            k = jobs.kernel()
            k.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
            k.OpenProcess.restype = ctypes.c_void_p
            k.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
            k.WaitForSingleObject.restype = ctypes.c_ulong
            try:
                until = time.monotonic() + 8
                while not path.exists() and time.monotonic() < until:
                    time.sleep(0.05)
                self.assertTrue(path.exists(), "grandchild never started")
                grand_pid = int(path.read_text())
                grandchild_handle = k.OpenProcess(0x00100000, False, grand_pid)
                self.assertTrue(grandchild_handle)
                self.assertEqual(k.WaitForSingleObject(grandchild_handle, 0), 0x102,
                                 "grandchild should still be alive before job closure")
                parent.close()
                self.assertEqual(k.WaitForSingleObject(grandchild_handle, 5000), 0,
                                 "Job Object closure must terminate grandchild")
            finally:
                parent.close()
                if grandchild_handle:
                    k.CloseHandle(grandchild_handle)

    def test_failed_resume_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "must-not-exist"
            code = "from pathlib import Path; Path(" + repr(str(marker)) + ").write_text('ran')"
            with patch.object(jobs, "resume_initial_thread",
                              side_effect=RuntimeError("test")):
                with self.assertRaisesRegex(RuntimeError, "test"):
                    jobs.ContainedProcess([sys.executable, "-c", code])
            self.assertFalse(marker.exists(), "suspended child ran before assignment")


if __name__ == "__main__":
    unittest.main()
