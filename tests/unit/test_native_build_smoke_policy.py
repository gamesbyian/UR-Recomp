from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "native-build-smoke.yml"


class NativeBuildSmokePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_uses_repository_owned_snesrecomp_source(self) -> None:
        self.assertIn(
            "python3 tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only",
            self.text,
        )
        self.assertIn("--no-submodules", self.text)
        self.assertNotIn("submodules: recursive", self.text)
        self.assertNotIn("snesrecomp/tools/new_project/setup_project.sh", self.text)

    def test_native_build_uses_system_sdl2_without_sdl3_fetch(self) -> None:
        self.assertIn("libsdl2-dev", self.text)
        self.assertIn("-DSNESRECOMP_SDL_BACKEND=SDL2", self.text)
        self.assertIn("-DSNESRECOMP_SDL3_FETCH=OFF", self.text)

    def test_does_not_reintroduce_framework_git_fetch_contract(self) -> None:
        self.assertNotIn("--snesrecomp-ref", self.text)


if __name__ == "__main__":
    unittest.main()
