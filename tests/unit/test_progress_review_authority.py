"""Exercise the authoritative v2 review/interval tests in required full unit CI.

The timing-sharded unit runner discovers tests.unit.test_* only. The original
source-bound v2 acceptance suites live in tests/test_progress_*.py; importing
their TestCase classes here makes them run with the mandatory full unit check
without moving historical tests or introducing a second CI workflow.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_review_case(stem, class_name):
    path = ROOT / "tests" / (stem + ".py")
    spec = importlib.util.spec_from_file_location("ur_review_gate_" + stem, path)
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load progress review regression: " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case = getattr(module, class_name)
    if case.__name__ != class_name:
        raise ImportError("Unexpected progress review TestCase: " + stem)
    return case


ProgressIntervalV2Tests = _load_review_case(
    "test_progress_interval_v2", "ProgressIntervalV2Tests")
ReviewedProgressCheckpointTests = _load_review_case(
    "test_progress_v2_oct26_review", "ReviewedProgressCheckpointTests")
