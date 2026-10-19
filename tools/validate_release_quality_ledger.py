#!/usr/bin/env python3
"""Validate explicit release QA gate claims without consulting GitHub or CI.

This is intentionally separate from developer-package smoke acceptance.
A user can run it against a source tree before labeling an alpha or beta.
Passing validates honest bookkeeping, not the underlying game or a release.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
VALID_STATUSES = {"unverified", "in_progress", "passed", "failed", "blocked", "waived"}
RELEASE_DECISIONS = {"not_assessed", "playtest_alpha", "beta", "release_candidate", "public_release"}
REQUIRED_IDS = {f"QA-{n:02d}" for n in range(1, 13)}
REQUIRED_LAYERS = {"L4", "L5"}
VALID_PRIORITIES = {"P0", "P1", "P2"}
GATE_ID = re.compile(r"QA-[0-9]{2}\Z")
JOURNEY_ID = re.compile(r"J-[0-9]{2}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
LAYER_RANK = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}

def valid_evidence_timestamp(value: object) -> bool:
    """Require a timezone-aware ISO-8601 witness/review instant."""
    if not isinstance(value, str) or "T" not in value:
        return False
    try:
        instant = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return instant.tzinfo is not None and instant.utcoffset() is not None


def source_event_register_summary(repo_root: pathlib.Path) -> dict:
    """Derive release counts from the independent, existing course-event census.

    This checks consistency of two local evidence records. It never certifies
    the provenance or truth of an original/native emulator observation.
    """
    producer_path = repo_root / "tools" / "audit_original_course_event_coverage.py"
    spec = importlib.util.spec_from_file_location("qa01_release_source_census", producer_path)
    if spec is None or spec.loader is None:
        raise ValueError("QA-01 source census producer is unavailable")
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    catalog = json.loads((repo_root / "analysis/data/course-corpus.json").read_text(encoding="utf-8"))
    source = json.loads((repo_root / "analysis/data/course-event-runtime-evidence.json").read_text(encoding="utf-8"))
    report = producer.build_census(catalog, source)
    entries = report["entries"]
    primary = [r for r in entries if r["rom"] == "usa-retail"]
    comparison = [r for r in entries if r["rom"] != "usa-retail"]
    if len(primary) != 45 or len(comparison) != 90:
        raise ValueError("QA-01 source census has unexpected regional population")
    return {
        "complete_event_passes": sum(r["status"] == "passed" for r in primary),
        "partial": sum(r["status"] == "partial" for r in primary),
        # Failed/blocked cases also remain unaccepted by the release gate.
        "unverified": sum(r["status"] not in ("passed", "partial") for r in primary),
        "regional_comparison_complete": sum(r["status"] == "passed" for r in comparison),
        "regional_comparison_unverified": sum(r["status"] != "passed" for r in comparison),
        "primary_pass_candidates": {
            observation.get("candidate_sha")
            for observation in source["observations"]
            if observation["rom"] == "usa-retail" and observation["status"] == "passed"
        },
    }


def check_registry(registry: object, repo_root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(registry, dict):
        return ["root must be an object"]
    if registry.get("schema") != "UR-RELEASE-QUALITY-LEDGER/1":
        errors.append("unexpected schema")
    candidate = registry.get("candidate")
    if not isinstance(candidate, dict):
        return errors + ["candidate must be an object"]
    commit = candidate.get("commit_sha")
    artifact = candidate.get("zip_sha256")
    decision = candidate.get("release_decision")
    physical = candidate.get("physical_hardware_verified")
    if not isinstance(decision, str) or decision not in RELEASE_DECISIONS:
        errors.append("candidate unknown release_decision")
    if type(physical) is not bool:
        errors.append("candidate physical_hardware_verified must be boolean")
    if commit is not None and (not isinstance(commit, str) or not SHA.fullmatch(commit)):
        errors.append("candidate commit_sha must be 40 lowercase hex or null")
    if artifact is not None and (not isinstance(artifact, str) or not SHA256.fullmatch(artifact)):
        errors.append("candidate zip_sha256 must be 64 lowercase hex or null")
    if (commit is None) != (artifact is None):
        errors.append("candidate SHA and artifact SHA-256 must be pinned together")
    if isinstance(decision, str) and decision in RELEASE_DECISIONS - {"not_assessed"} and (not commit or not artifact):
        errors.append("release decision requires an exact commit and ZIP SHA-256")
    if physical is True and (not commit or not artifact):
        errors.append("physical hardware claim requires an exact candidate")
    gates = registry.get("gates")
    if not isinstance(gates, list):
        return errors + ["gates must be an array"]
    try:
        original_event_counts = source_event_register_summary(repo_root)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        original_event_counts = None
        errors.append(f"QA-01 source event register unavailable or invalid: {exc}")
    seen: set[str] = set()
    journeys_path = repo_root / "docs" / "QA-PLAYER-JOURNEYS.md"
    try:
        journey_text = journeys_path.read_text(encoding="utf-8")
    except OSError:
        journey_text = ""
        errors.append("QA player journeys document unavailable")
    journey_ids = set(re.findall(r"\bJ-[0-9]{2}\b", journey_text))
    for index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            errors.append(f"gates[{index}] must be an object")
            continue
        name = gate.get("id")
        if not isinstance(name, str) or not GATE_ID.fullmatch(name):
            errors.append(f"gates[{index}] has invalid id")
            continue
        if name in seen:
            errors.append(f"duplicate gate {name}")
        seen.add(name)
        if not isinstance(gate.get("priority"), str) or gate["priority"] not in VALID_PRIORITIES:
            errors.append(f"{name} invalid priority")
        if not isinstance(gate.get("claim"), str) or not gate["claim"].strip():
            errors.append(f"{name} missing claim")
        if not isinstance(gate.get("next_action"), str) or not gate["next_action"].strip():
            errors.append(f"{name} missing next_action")
        status = gate.get("status")
        if not isinstance(status, str) or status not in VALID_STATUSES:
            errors.append(f"{name} invalid status")
        minimum = gate.get("required_layer")
        if not isinstance(minimum, str) or minimum not in REQUIRED_LAYERS:
            errors.append(f"{name} must require L4 or L5")
        journeys = gate.get("journeys")
        if not isinstance(journeys, list) or not journeys:
            errors.append(f"{name} missing journeys")
        else:
            for j in journeys:
                if not isinstance(j, str) or not JOURNEY_ID.fullmatch(j) or j not in journey_ids:
                    errors.append(f"{name} unknown journey {j!r}")
        refs = gate.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{name} missing source contracts")
        else:
            for ref in refs:
                if (not isinstance(ref, str) or not ref.startswith("docs/")
                        or ".." in pathlib.PurePosixPath(ref).parts
                        or not (repo_root / ref).is_file()):
                    errors.append(f"{name} missing or unsafe source contract {ref!r}")
        witnesses = gate.get("witnesses")
        if not isinstance(witnesses, list):
            errors.append(f"{name} witnesses must be a list")
            witnesses = []
        if isinstance(status, str) and status in {"passed", "failed"}:
            if not commit or not artifact or gate.get("candidate_commit") != commit:
                errors.append(f"{name} {status} without exact pinned candidate")
            if not witnesses:
                errors.append(f"{name} {status} without independent recorded witnesses")
        # QA-01 is a complete USA-release census, not a representative-case
        # gate. A single valid L4 report cannot accept an incomplete 45-event
        # denominator or silently shrink that denominator to certify a pass.
        # This is bookkeeping only: the independently compared course events
        # must still be verified against the owning event census.
        if name == "QA-01":
            census = gate.get("coverage")
            if not isinstance(census, dict):
                errors.append("QA-01 missing course-event coverage census")
            else:
                keys = ("complete_event_passes", "partial", "unverified")
                valid_counts = True
                for key in keys:
                    value = census.get(key)
                    if type(value) is not int or value < 0:
                        errors.append(f"QA-01 invalid USA coverage {key}")
                        valid_counts = False
                denominator = census.get("denominator")
                if type(denominator) is not int or denominator != 45:
                    errors.append("QA-01 USA coverage denominator must remain 45")
                if valid_counts and sum(census[key] for key in keys) != 45:
                    errors.append("QA-01 USA coverage counts must partition all 45 events")
                if status == "passed" and any(
                    census.get(key) != expected
                    for key, expected in (
                        ("complete_event_passes", 45), ("partial", 0),
                        ("unverified", 0)
                    )
                ):
                    errors.append("QA-01 passed without 45/45 independently accepted USA events")
        # Comparison coverage is not an additional USA shipping requirement,
        # but its declared 90 Europe/prototype cases and 135-case corpus must
        # remain arithmetically honest even for an otherwise accepted QA-01.
        if name == "QA-01" and isinstance(gate.get("coverage"), dict):
            regional = gate["coverage"]
            comparison_keys = ("regional_comparison_complete",
                               "regional_comparison_unverified")
            comparison_valid = True
            for key in comparison_keys:
                value = regional.get(key)
                if type(value) is not int or value < 0:
                    errors.append(f"QA-01 invalid regional coverage {key}")
                    comparison_valid = False
            region_denominator = regional.get("regional_comparison_denominator")
            if type(region_denominator) is not int or region_denominator != 90:
                errors.append("QA-01 regional comparison denominator must remain 90")
            if comparison_valid and sum(regional[k] for k in comparison_keys) != 90:
                errors.append("QA-01 regional comparison counts must partition all 90 cases")
            corpus_total = regional.get("total_tracked_course_rom_pairs")
            if type(corpus_total) is not int or corpus_total != 135:
                errors.append("QA-01 all-build course corpus total must remain 135")
        if name == "QA-01" and original_event_counts is not None:
            coverage = gate.get("coverage")
            if isinstance(coverage, dict):
                for field in (
                    "complete_event_passes", "partial", "unverified",
                    "regional_comparison_complete", "regional_comparison_unverified",
                ):
                    if coverage.get(field) != original_event_counts[field]:
                        errors.append(
                            f"QA-01 {field} disagrees with original event source register "
                            f"(source={original_event_counts[field]!r})"
                        )
            if status == "passed" and (
                original_event_counts["primary_pass_candidates"] != {commit}
            ):
                errors.append(
                    "QA-01 passed without every original/native source event "
                    "bound to the exact release candidate commit"
                )
        if status == "passed" and minimum == "L5" and physical is not True:
            errors.append(f"{name} L5 pass without physical hardware verification")
        if status == "waived":
            if not commit or not artifact or gate.get("candidate_commit") != commit or gate.get("waiver_zip_sha256") != artifact:
                errors.append(f"{name} waiver not tied to exact candidate commit and ZIP")
            if not isinstance(gate.get("waiver_reason"), str) or not gate["waiver_reason"].strip():
                errors.append(f"{name} waiver needs explicit rationale")
            if not isinstance(gate.get("waiver_approved_by"), str) or not gate["waiver_approved_by"].strip():
                errors.append(f"{name} waiver needs named reviewer")
            if not valid_evidence_timestamp(gate.get("waiver_approved_at")):
                errors.append(f"{name} waiver needs timezone-aware review instant")
        for w in witnesses:
            if not isinstance(w, dict):
                errors.append(f"{name} malformed witness")
                continue
            if (w.get("source_commit") != commit or
                    w.get("artifact_sha256") != artifact or
                    not commit or not artifact):
                errors.append(f"{name} witness not tied to exact candidate artifact")
            if not isinstance(w.get("source"), str) or not w["source"].strip():
                errors.append(f"{name} witness must identify reproducible source")
            if not valid_evidence_timestamp(w.get("tested_at")):
                errors.append(f"{name} witness tested_at must be a timezone-aware ISO-8601 instant")
            layer = w.get("layer")
            rank = LAYER_RANK.get(layer, 0) if isinstance(layer, str) else 0
            min_rank = LAYER_RANK.get(minimum, 99) if isinstance(minimum, str) else 99
            if rank < min_rank:
                errors.append(f"{name} witness below required layer {minimum}")
            if rank >= LAYER_RANK["L5"]:
                # An L5 assertion must identify representative real
                # consumer-device *classes*, not a synthetic SDL shim or
                # generic documentation page. Avoid serials/user IDs.
                hardware = w.get("hardware")
                required_device_classes = ("windows_version", "gpu",
                                           "display", "controller", "audio")
                if not isinstance(hardware, dict) or any(
                    not isinstance(hardware.get(k), str)
                    or not hardware[k].strip()
                    for k in required_device_classes
                ):
                    errors.append(f"{name} L5 witness needs Windows/GPU/display/controller/audio device matrix")
                if physical is not True:
                    errors.append(f"{name} L5 witness without physical hardware confirmation")
        if status != "passed" and witnesses and gate.get("candidate_commit") != commit:
            errors.append(f"{name} witness candidate mismatch")
    # QA-04's L5 release requirement is deliberately more demanding than a
    # one-off device list: three dissimilar environments, at least two actual
    # physical systems, with at most one isolated clean VM. A positive boolean
    # or three copies of the same hosted SDL fixture cannot be a hardware pass.
    # This validates evidence metadata only; it never attests devices existed.
    qa04 = next((g for g in gates if isinstance(g, dict)
                 and g.get("id") == "QA-04"), None)
    if isinstance(qa04, dict) and qa04.get("status") == "passed":
        qa04_witnesses = qa04.get("witnesses")
        setups: list[tuple[str, str, tuple[str, str, str], bool, str]] = []
        if isinstance(qa04_witnesses, list):
            for w in qa04_witnesses:
                if not isinstance(w, dict) or w.get("layer") != "L5":
                    continue
                hw = w.get("hardware")
                if not isinstance(hw, dict):
                    continue
                ident = hw.get("setup_id")
                environment = hw.get("environment")
                clean = hw.get("clean_environment")
                if (not isinstance(ident, str) or not ident.strip()
                        or environment not in ("physical", "isolated-clean-vm")
                        or type(clean) is not bool):
                    continue
                if environment == "isolated-clean-vm" and not clean:
                    continue
                if environment == "physical" and not all(
                    hw.get(flag) is True for flag in (
                        "physical_controller_observed",
                        "audible_output_observed",
                        "visible_display_observed",
                    )
                ):
                    continue
                traits = (hw.get("gpu"), hw.get("display"), hw.get("controller"))
                exe_digest = w.get("tested_executable_sha256")
                if (any(not isinstance(v, str) or not v.strip() for v in traits)
                        or not isinstance(exe_digest, str)
                        or SHA256.fullmatch(exe_digest) is None
                        or w.get("package_unchanged_after_launch") is not True):
                    continue
                setups.append((ident.strip(), environment, traits, clean, exe_digest))
        phys = [s for s in setups if s[1] == "physical"]
        vm = [s for s in setups if s[1] == "isolated-clean-vm"]
        if (len(setups) < 3 or len(phys) < 2 or len(vm) > 1
                or len({s[0] for s in setups}) != len(setups)
                or not any(s[3] for s in setups)
                or len({s[2] for s in phys}) < 2
                or len({s[4] for s in setups}) != 1):
            errors.append(
                "QA-04 needs three independently identified dissimilar L5 "
                "Windows setups (three physical or one isolated clean VM "
                "plus two physical), an actual clean environment and "
                "explicit controller/audio/display observation on real systems; "
                "all three must bind the same actual PE and immutable package"
            )

    if decision == "public_release":
        if not isinstance(candidate.get("release_approved_by"), str) or not candidate["release_approved_by"].strip():
            errors.append("public release requires a separately recorded human approver")
        if not valid_evidence_timestamp(candidate.get("release_approved_at")):
            errors.append("public release requires a timezone-aware human approval instant")
    if physical is True:
        # A bare boolean is not an independent physical witness. QA-04 is
        # the consumer-hardware gate, and its accepted L5 witness must itself
        # satisfy the candidate SHA/ZIP constraints above.
        qa04 = next((gate for gate in gates
                     if isinstance(gate, dict) and gate.get("id") == "QA-04"), None)
        if not isinstance(qa04, dict) or qa04.get("status") != "passed":
            errors.append("physical hardware claim requires passed QA-04 L5 gate")

    missing = REQUIRED_IDS - seen
    extra = seen - REQUIRED_IDS
    if missing:
        errors.append("missing mandatory gates: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("unexpected gate IDs: " + ", ".join(sorted(extra)))
    if isinstance(decision, str) and decision in {"beta", "release_candidate", "public_release"}:
        incomplete = [g.get("id", "?") if isinstance(g, dict) else "?"
                      for g in gates
                      if not isinstance(g, dict)
                      or not isinstance(g.get("status"), str)
                      or g["status"] not in {"passed", "waived"}]
        if incomplete:
            errors.append("release decision with unresolved gates: " + ", ".join(incomplete))
        if not candidate.get("physical_hardware_verified"):
            errors.append("release decision without physical Windows validation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--ledger", type=pathlib.Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    path = args.ledger or root / "docs" / "RELEASE-QUALITY-LEDGER.json"
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"release quality ledger unavailable/invalid: {exc}", file=sys.stderr)
        return 2
    errors = check_registry(registry, root)
    for error in errors:
        print("RELEASE_LEDGER_FAIL " + error, file=sys.stderr)
    if errors:
        return 1
    print(f"RELEASE_LEDGER_VALID gates={len(registry['gates'])} "
          "claim=bookkeeping-only release_verified=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
