import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "prepare_ws_product", ROOT / "tools/prepare_native_widescreen_product.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class PrepareNativeWidescreenProductTests(unittest.TestCase):
    def test_generation_command_is_project_relative_and_cfg_rooted(self):
        command = MOD.generation_command(
            Path("/framework"), Path("/project"), Path("/rom.sfc")
        )
        self.assertIn("/framework/snesrecomp_cli.py", command)
        self.assertEqual(command[command.index("--project-root") + 1], "/project")
        self.assertEqual(command[command.index("--cfg-dir") + 1], "recomp")
        self.assertEqual(command[command.index("--out-dir") + 1], "src/gen")
        self.assertIn("--cfg-roots", command)

    def test_prepare_seeds_regenerates_then_applies_accepted_hook(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            framework = root / "framework"
            project = root / "project"
            rom = root / "game.sfc"
            framework.mkdir()
            (framework / "snesrecomp_cli.py").write_text("# stub\n")
            (project / "recomp").mkdir(parents=True)
            rom.write_bytes(b"rom")
            calls = []

            def fake_run(command, check):
                self.assertTrue(check)
                calls.append(command)
                (project / "src/gen").mkdir(parents=True)

            with mock.patch.object(
                MOD, "ensure_seed", return_value={"symbols": True, "bank03": True}
            ) as seed, mock.patch.object(
                MOD,
                "apply_widescreen_hook",
                return_value={"changed": True, "margin72_supported": True},
            ) as apply:
                report = MOD.prepare(framework, project, rom, run=fake_run)

            seed.assert_called_once_with((project / "recomp").resolve())
            apply.assert_called_once_with((project / "src/gen").resolve())
            self.assertEqual(len(calls), 1)
            self.assertTrue(report["product_ready"])
            self.assertTrue(report["hook"]["margin72_supported"])

    def test_prepare_fails_closed_when_capacity_contract_regresses(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            framework = root / "framework"
            project = root / "project"
            rom = root / "game.sfc"
            framework.mkdir()
            (framework / "snesrecomp_cli.py").write_text("# stub\n")
            (project / "recomp").mkdir(parents=True)
            (project / "src/gen").mkdir(parents=True)
            rom.write_bytes(b"rom")

            with mock.patch.object(MOD, "ensure_seed", return_value={}), \
                 mock.patch.object(
                     MOD, "apply_widescreen_hook",
                     return_value={"changed": True, "margin72_supported": False},
                 ):
                with self.assertRaisesRegex(ValueError, "retain \+72 capacity"):
                    MOD.prepare(
                        framework,
                        project,
                        rom,
                        run=lambda command, check: None,
                    )


    def test_regression_baseline_seeds_and_generates_without_hook(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            framework = root / "framework"
            project = root / "project"
            rom = root / "game.sfc"
            framework.mkdir()
            (framework / "snesrecomp_cli.py").write_text("# stub\n")
            (project / "recomp").mkdir(parents=True)
            rom.write_bytes(b"rom")
            calls = []

            def fake_run(command, check):
                calls.append(command)
                (project / "src/gen").mkdir(parents=True)

            with mock.patch.object(
                MOD, "ensure_seed", return_value={"symbols": True, "bank03": True}
            ) as seed, mock.patch.object(MOD, "apply_widescreen_hook") as apply:
                report = MOD.prepare(
                    framework, project, rom, run=fake_run, regression_baseline=True
                )

            seed.assert_called_once_with((project / "recomp").resolve())
            apply.assert_not_called()
            self.assertEqual(len(calls), 1)
            self.assertTrue(report["regression_baseline"])
            self.assertFalse(report["product_ready"])


if __name__ == "__main__":
    unittest.main()
