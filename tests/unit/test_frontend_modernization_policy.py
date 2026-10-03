import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATE = ROOT / "tools" / "validate_frontend_modernization_policy.py"
POLICY = "analysis/frontend-modernization-policy.json"


def run(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATE), "--root", str(root)],
        capture_output=True, text=True, check=False,
    )


class FrontendModernizationPolicyTests(unittest.TestCase):
    def test_repository_policy_is_valid(self) -> None:
        proc = run(ROOT)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("Frontend modernization policy valid", proc.stdout)

    def _mutated(self, mutate) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for rel in (
                POLICY,
                "analysis/ui-state-map.yml",
                "docs/UI-STATE-MAP.md",
                "docs/PROJECT-PLAN.md",
                "docs/WORK-QUEUE.md",
                "docs/MODERN-PRODUCT-LAYER.md",
            ):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / rel, root / rel)
            policy = json.loads((root / POLICY).read_text())
            mutate(policy)
            (root / POLICY).write_text(json.dumps(policy))
            return run(root)

    def _feature(self, policy: dict, fid: str) -> dict:
        return next(f for f in policy["features"] if f["id"] == fid)

    def test_presentation_artifact_cannot_be_redesigned(self) -> None:
        proc = self._mutated(
            lambda p: self._feature(p, "result-rituals-and-tallies").update(
                modern="redesign_candidate", decision_gate="x"
            )
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not allowed for class presentation_artifact", proc.stdout)

    def test_gameplay_mechanic_cannot_be_redesigned(self) -> None:
        proc = self._mutated(
            lambda p: self._feature(p, "race-simulation").update(modern="redesign_decided")
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not allowed for class gameplay_mechanic", proc.stdout)

    def test_every_state_must_be_classified(self) -> None:
        proc = self._mutated(
            lambda p: p.update(
                features=[f for f in p["features"] if f["id"] != "forbidden-name-rejection"]
            )
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("FORBIDDEN_NAME_REJECTION", proc.stdout)

    def test_decided_redesign_needs_resolvable_policy_source(self) -> None:
        proc = self._mutated(
            lambda p: self._feature(p, "racer-as-save-slot").update(
                policy_source="docs/PROJECT-PLAN.md#no-such-heading"
            )
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("no heading anchor", proc.stdout)

    def test_candidate_redesign_needs_decision_gate(self) -> None:
        proc = self._mutated(
            lambda p: self._feature(p, "records-silos").pop("decision_gate")
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("requires decision_gate", proc.stdout)


if __name__ == "__main__":
    unittest.main()
