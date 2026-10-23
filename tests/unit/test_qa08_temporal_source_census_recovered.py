"""Run preserved QA08 temporal census negative controls in standard tooling CI."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "qa08"))
from test_qa08_temporal_source_census import TemporalSourceCensusTests
