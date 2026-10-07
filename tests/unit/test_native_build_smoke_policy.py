from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "native-build-smoke.yml"
NATIVE_UI_WORKFLOW = ROOT / ".github" / "workflows" / "native-ui-evidence.yml"


class NativeBuildSmokePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.native_ui_text = NATIVE_UI_WORKFLOW.read_text(encoding="utf-8")

    def test_uses_repository_owned_snesrecomp_source(self) -> None:
        self.assertIn(
            "python3 tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only",
            self.text,
        )
        self.assertIn("--no-submodules", self.text)
        self.assertNotIn("submodules: recursive", self.text)
        self.assertNotIn("sh snesrecomp/tools/new_project/setup_project.sh", self.text)

    def test_native_build_uses_repository_owned_sdl3(self) -> None:
        # docs/PLATFORM-TARGETS.md: SDL3 is the canonical desktop backend, built
        # from the repository-owned source so FetchContent never downloads.
        self.assertIn(
            "python3 tools/bootstrap_toolchain.py --offline --tool sdl3 --clone-only",
            self.text,
        )
        self.assertIn("-DSNESRECOMP_SDL_BACKEND=SDL3", self.text)
        self.assertNotIn("-DSNESRECOMP_SDL_BACKEND=SDL2", self.text)
        self.assertIn(
            '-DSNESRECOMP_SDL3_SOURCE_DIR="$GITHUB_WORKSPACE/.tools/src/sdl3/SDL3-3.4.10"',
            self.text,
        )
        self.assertNotIn("libsdl2-dev", self.text)

    def test_does_not_reintroduce_framework_git_fetch_contract(self) -> None:
        self.assertNotIn("--snesrecomp-ref", self.text)

    def test_modern_settings_acceptance_covers_internal_render_scale(self) -> None:
        # The end-to-end settings/render-scale proof remains durable, but it
        # lives in the already-built Native UI core shard rather than regrowing
        # the fast native smoke gate.
        self.assertNotIn("Internal Render Scale compositor acceptance", self.text)
        self.assertIn("# Internal Render Scale: 4x -> 1x.", self.native_ui_text)
        self.assertIn('grep -q "^internal_render_scale=1x$"', self.native_ui_text)
        self.assertGreaterEqual(
            self.native_ui_text.count('grep -q "UR_RENDER_SCALE APPLIED scale=1x"'),
            2,
        )
        self.assertIn(
            "Authentic mode touched modern Internal Render Scale policy",
            self.native_ui_text,
        )
        self.assertIn(
            "Internal Render Scale compositor acceptance",
            self.native_ui_text,
        )
        self.assertIn(
            "if: matrix.shard == 'core'",
            self.native_ui_text,
        )
        self.assertIn(
            'grep -q "UR_RACER_HD_DRAW PASS .*output_scale=2"',
            self.native_ui_text,
        )
        self.assertIn(
            'tools/check_ppm.py "$SHOT" --width 512 --height 448 --min-colors 2',
            self.native_ui_text,
        )
        for artifact in (
            "render-scale-2x.state",
            "render-scale-2x.ppm",
            "render-scale-2x-dumps/",
        ):
            self.assertIn(f"${{{{ runner.temp }}}}/{artifact}", self.native_ui_text)


if __name__ == "__main__":
    unittest.main()
