import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
PATCH = ROOT / "tools" / "patches" / "snesrecomp-live-volume.patch"
HARNESS = ROOT / "tests" / "native" / "run_modern_volume_acceptance.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "modern-onboarding-practice-acceptance.yml"
STATE_CPP = ROOT / "native" / "product" / "host_product_state.cpp"


def _body(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


class ModernVolumeContractTests(unittest.TestCase):
    def test_patch_reuses_the_framework_volume_path(self):
        text = PATCH.read_text(encoding="utf-8")
        self.assertIn("int snesrecomp_desktop_get_volume(void)", text)
        self.assertIn("int snesrecomp_desktop_step_volume(int direction)", text)
        self.assertIn("HandleVolumeAdjustment(direction > 0 ? 1 : -1);", text)
        for forbidden in ("Rtl", "g_ram", "g_sram"):
            self.assertNotIn(forbidden, text)

    def test_patch_is_registered_in_both_manifests(self):
        for manifest_path in (
            ROOT / "tools" / "toolchain-entries" / "snesrecomp.json",
        ):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            paths = [entry["path"] for entry in manifest["patches"]]
            self.assertIn("tools/patches/snesrecomp-live-volume.patch", paths)
        self.assertIn(
            "tools/patches/snesrecomp-live-volume.patch",
            (ROOT / "tools" / "toolchain.json").read_text(encoding="utf-8"),
        )

    def test_options_row_steps_framework_authority_only(self):
        source = HOST.read_text(encoding="utf-8")
        step = _body(source, "bool step_volume_setting(", "\n}\n")
        self.assertIn("if (!modern_mode()) return false;", step)
        self.assertIn("snesrecomp_desktop_step_volume(direction)", step)
        for forbidden in ("persist_product_state", "g_product_state", "g_ram[", "g_config"):
            self.assertNotIn(forbidden, step)
        self.assertIn("case UR_MODERN_OPTIONS_VOLUME:\n        return step_volume_setting(1);", source)
        self.assertEqual(source.count("step_volume_setting(key == SDLK_RIGHT ? 1 : -1)"), 1)
        self.assertIn("button == kGamepadBtn_DpadRight ? 1 : -1", source)
        # Modern keeps no second copy of the volume.
        self.assertNotIn('"volume', STATE_CPP.read_text(encoding="utf-8"))

    def test_native_acceptance_is_wired(self):
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)
        harness = HARNESS.read_text(encoding="utf-8")
        for marker in (
            "UR_VOLUME_OPTIONS_ACCEPTANCE=adjust",
            "UR_VOLUME_OPTIONS_ACCEPTANCE=verify",
            'grep -q "^Volume = $EXPECTED$" "$WORK/user/config.ini"',
            'cmp -s "$STATE" "$WORK/host-state-before.txt"',
            'test "$LOADED" -eq "$EXPECTED"',
        ):
            self.assertIn(marker, harness)
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("run_modern_volume_acceptance.sh", workflow)
        self.assertIn('"tools/patches/snesrecomp-live-volume.patch"', workflow)


if __name__ == "__main__":
    unittest.main()
