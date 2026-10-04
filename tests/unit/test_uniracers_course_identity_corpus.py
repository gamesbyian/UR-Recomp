import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class UniracersCourseIdentityCorpusTests(unittest.TestCase):
    def test_all_45_manifest_headers_resolve_exactly(self):
        manifest = json.loads(
            (ROOT / "analysis" / "generated" / "course-resource-list-manifest.json")
            .read_text(encoding="utf-8")
        )
        courses = manifest["builds"]["usa-retail"]["courses"]
        self.assertEqual(len(courses), 45)

        rows = []
        for course in courses:
            a = course["spawn_or_landmark_a"]
            b = course["spawn_or_landmark_b"]
            dims = course["layout_dims"]
            rows.append(
                f'{course["stunt_time_or_mode"]} {a[0]} {a[1]} '
                f'{b[0]} {b[1]} {dims[0]} {dims[1]}'
            )

        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "course-identity-corpus"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native" / "title"),
                    str(ROOT / "native" / "title" / "uniracers_course_identity.cpp"),
                    str(ROOT / "tests" / "native" / "uniracers_course_identity_corpus.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            result = subprocess.run(
                [str(exe)],
                input="\n".join(rows) + "\n",
                text=True,
                capture_output=True,
                check=True,
            )

        resolved = [int(line) for line in result.stdout.splitlines()]
        self.assertEqual(resolved, list(range(1, 46)))


if __name__ == "__main__":
    unittest.main()
