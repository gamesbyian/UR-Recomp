"""RF095 disposable producer must not truncate existing PCM/map evidence."""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "tools/qa01_rf095_event_pcm.py"
spec = importlib.util.spec_from_file_location("qa01_rf095_event_pcm", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExclusiveOutputTests(unittest.TestCase):
    def test_original_frame_map_is_exclusive(self):
        self.assertIn('fopen(path, "wx")', module.REF_DECL)
        self.assertNotIn('fopen(path, "w")', module.REF_DECL)

    def test_native_pcm_and_frame_map_are_exclusive(self):
        self.assertIn('fopen(pcm, "wbx")', module.NATIVE_DECL)
        self.assertIn('fopen(map, "wx")', module.NATIVE_DECL)
        self.assertNotIn('fopen(pcm, "wb")', module.NATIVE_DECL)
        self.assertNotIn('fopen(map, "w")', module.NATIVE_DECL)

    def test_exclusive_modes_preserve_existing_bytes_in_c_and_cpp(self):
        code = r'''
#include <stdio.h>
#include <string.h>
int main(int argc, char **argv) {
  if (argc != 2) return 1;
  const char *path = argv[1];
  FILE *fp = fopen(path, "wx");
  if (fp) { fclose(fp); return 2; }
  fp = fopen(path, "wbx");
  if (fp) { fclose(fp); return 3; }
  fp = fopen(path, "rb");
  if (!fp) return 4;
  char bytes[16] = {0};
  size_t n = fread(bytes, 1, sizeof(bytes), fp);
  fclose(fp);
  return n == 8 && memcmp(bytes, "SENTINEL", 8) == 0 ? 0 : 5;
}
'''
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            src = root / "probe.c"
            src.write_text(code, encoding="utf-8")
            protected = root / "protected.bin"
            for compiler, language in (("cc", "c11"), ("c++", "c++11")):
                if shutil.which(compiler) is None:
                    continue
                protected.write_bytes(b"SENTINEL")
                exe = root / ("probe_c" if compiler == "cc" else "probe_cpp")
                subprocess.run([compiler, "-std=" + language, "-Wall", "-Wextra",
                                "-Werror", str(src), "-o", str(exe)],
                               check=True, timeout=10, capture_output=True)
                subprocess.run([str(exe), str(protected)], check=True,
                               timeout=10, capture_output=True)
                self.assertEqual(protected.read_bytes(), b"SENTINEL")


if __name__ == "__main__":
    unittest.main()
