import json
from pathlib import Path
import unittest

from tools.measure_racer_hd_fallback_frequency import build_report as build_frequency_report
from tools.summarize_racer_semantic_trace import (
    row_matches_registration,
    validate_registration_guard_scope,
    validate_registry_guard_scopes,
)


def player_local_entry(player="p1"):
    other = "p2" if player == "p1" else "p1"
    return {
        "representation_id": f"test-{player}-player-local",
        "semantic_frame_id": "0x1234",
        "player": player,
        "guard_scope": "player_local",
        "composition_guards": {
            f"{player}_primary": "0x1234",
            f"{other}_primary": "0x5678",
            f"{player}_companion": "0x0000",
            f"{other}_companion": "0x1111",
            f"{player}_selector": 0,
            f"{other}_selector": 1,
            f"{player}_companion_gate_word": "0x0000",
            f"{other}_companion_gate_word": "0x0001",
        },
        "registration": {
            "guard_scope_proof": {
                "scope": "player_local",
                "structural_basis": "players occupy disjoint object columns",
                "empirical_basis": "multiple exact witnesses collapse to one local raster",
                "workflow_run": 123,
                "artifact_id": 456,
            }
        },
    }


def row_for(entry):
    g = entry["composition_guards"]
    return {
        "frame": 10,
        "p1_primary": g["p1_primary"],
        "p2_primary": g["p2_primary"],
        "p1_companion": g["p1_companion"],
        "p2_companion": g["p2_companion"],
        "p1_selector": g["p1_selector"],
        "p2_selector": g["p2_selector"],
        "p1_gate": g["p1_companion_gate_word"],
        "p2_gate": g["p2_companion_gate_word"],
    }


ROOT = Path(__file__).resolve().parents[2]


class RacerHdGuardScopeContractTests(unittest.TestCase):
    def test_valid_player_local_scope_matches_only_local_fields(self):
        entry = player_local_entry("p2")
        row = row_for(entry)
        self.assertTrue(row_matches_registration(row, entry))

        row["p1_primary"] = "0x9999"
        row["p1_companion"] = "0xAAAA"
        row["p1_selector"] = 7
        row["p1_gate"] = "0xBBBB"
        self.assertTrue(row_matches_registration(row, entry))

        row["p2_companion"] = "0x0001"
        self.assertFalse(row_matches_registration(row, entry))

    def test_nested_guard_scope_fails_closed(self):
        entry = player_local_entry()
        entry.pop("guard_scope")
        entry["registration"]["guard_scope"] = "player_local"
        with self.assertRaisesRegex(
            ValueError, "guard_scope must be representation-level"
        ):
            validate_registration_guard_scope(entry)

    def test_unknown_guard_scope_fails_closed(self):
        entry = player_local_entry()
        entry["guard_scope"] = "opponent_agnostic"
        with self.assertRaisesRegex(ValueError, "unsupported guard_scope"):
            validate_registration_guard_scope(entry)

    def test_player_local_scope_requires_matching_proof(self):
        entry = player_local_entry()
        entry["registration"]["guard_scope_proof"]["scope"] = "exact"
        with self.assertRaisesRegex(ValueError, "requires matching"):
            validate_registration_guard_scope(entry)

    def test_player_local_scope_requires_local_guard_keys(self):
        entry = player_local_entry("p1")
        del entry["composition_guards"]["p1_companion_gate_word"]
        with self.assertRaisesRegex(ValueError, "missing local keys"):
            validate_registration_guard_scope(entry)

    def test_exact_scope_must_not_carry_player_local_proof(self):
        entry = player_local_entry()
        entry.pop("guard_scope")
        with self.assertRaisesRegex(ValueError, "guard_scope_proof requires"):
            validate_registration_guard_scope(entry)

    def test_registry_validation_catches_malformed_unobserved_entry(self):
        valid = player_local_entry()
        malformed = player_local_entry()
        malformed["representation_id"] = "malformed-unobserved"
        malformed["semantic_frame_id"] = "0x9999"
        malformed.pop("guard_scope")
        malformed["registration"]["guard_scope"] = "player_local"
        registry = {"entries": [valid, malformed]}
        with self.assertRaisesRegex(
            ValueError, "malformed-unobserved.*representation-level"
        ):
            validate_registry_guard_scopes(registry)

    def test_canonical_registry_and_p2_rescue_entry_obey_contract(self):
        registry = json.loads(
            (ROOT / "analysis/data/racer-hd-replacement-prototype.json").read_text()
        )
        validate_registry_guard_scopes(registry)
        entry = next(
            item
            for item in registry["entries"]
            if item["representation_id"]
            == "ordinary-racer-0x0546-p2-companion-0EB2-broader-frequency-reference"
        )
        self.assertEqual(entry["guard_scope"], "player_local")
        self.assertNotIn("guard_scope", entry["registration"])
        self.assertEqual(
            entry["registration"]["guard_scope_proof"]["scope"], "player_local"
        )

        row = row_for(entry)
        self.assertTrue(row_matches_registration(row, entry))
        row["p1_primary"] = "0xAAAA"
        row["p1_companion"] = "0xBBBB"
        row["p1_selector"] = 7
        row["p1_gate"] = "0xCCCC"
        self.assertTrue(row_matches_registration(row, entry))

    def test_frequency_measurement_validates_registry_before_counting(self):
        entry = player_local_entry()
        row = row_for(entry)
        malformed = player_local_entry()
        malformed["representation_id"] = "malformed-unobserved"
        malformed["semantic_frame_id"] = "0x9999"
        malformed.pop("guard_scope")
        malformed["registration"]["guard_scope"] = "player_local"
        with self.assertRaisesRegex(
            ValueError, "malformed-unobserved.*representation-level"
        ):
            build_frequency_report([row], {"entries": [entry, malformed]})


if __name__ == "__main__":
    unittest.main()
