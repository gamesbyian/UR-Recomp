import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class RecentCourseOriginCppTests(unittest.TestCase):
    def test_attract_demo_origin_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "recent-course-origin-test"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native/product"),
                    str(ROOT / "tests/native/recent_course_origin_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)

    def test_host_gates_recent_course_on_origin(self):
        source = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8")
        start = source.index("void observe_recent_course_identity()")
        end = source.index("ur::product::FastNavigationContext", start)
        body = source[start:end]
        observe = body.index("observe_recent_course_origin(")
        gate = body.index("recent_course_origin_admits(")
        track = body.index("authoritative_active_track_id()")
        self.assertLess(observe, gate)
        self.assertLess(gate, track)
        self.assertIn("UR_FAST_NAV RECENT_IGNORED_ATTRACT", body)


if __name__ == "__main__":
    unittest.main()
