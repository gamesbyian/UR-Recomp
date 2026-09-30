import json
from pathlib import Path
import tempfile
import unittest

from tools.measure_source_closure import collect, parse_depfile


class MeasureSourceClosureTests(unittest.TestCase):
    def test_depfile_continuation_and_external_header_filter(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "src"
            build = root / "libretro"
            build.mkdir(parents=True)
            (root / "a.cpp").write_text("int a;\n", encoding="utf-8")
            (root / "a.h").write_text("#pragma once\n", encoding="utf-8")
            (root / "LICENSE").write_text("license\n", encoding="utf-8")
            dep = build / "a.d"
            dep.write_text(
                "a.o: ../a.cpp ../a.h \\\n /usr/include/stdio.h\n",
                encoding="utf-8",
            )

            parsed = parse_depfile(dep)
            self.assertIn("../a.cpp", parsed)
            self.assertIn("../a.h", parsed)

            result = collect(root, [dep], ["LICENSE"], dependency_base=build)
            self.assertEqual(
                [entry["path"] for entry in result["files"]],
                ["LICENSE", "a.cpp", "a.h"],
            )
            self.assertEqual(result["file_count"], 3)
            self.assertEqual(
                result["source_bytes"],
                sum((root / name).stat().st_size for name in ["LICENSE", "a.cpp", "a.h"]),
            )

    def test_output_shape_is_json_serializable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "x.c").write_text("int x;\n", encoding="utf-8")
            dep = root / "x.d"
            dep.write_text("x.o: x.c\n", encoding="utf-8")
            payload = collect(root, [dep], [], dependency_base=root)
            encoded = json.dumps(payload)
            self.assertIn('"closure_sha256"', encoded)


if __name__ == "__main__":
    unittest.main()
