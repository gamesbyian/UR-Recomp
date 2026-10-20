#!/usr/bin/env python3
"""Source-gated 2P topological course candidates, never fictional gameplay.

Reuses the original Crawler/Shuffler menu routes and the two independent
post-GO dynamic inputs. No guest writes, geometry changes, ROM patches or
arbitrary coordinate teleportation. 2P menu behavior requires native proof.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "analysis/data/course-corpus.json"
SOURCE_ANCHOR = (
    "press p2:start 2\n"
    "wait 200\n"
    "press start 2\n"
    "wait 200\n"
    "press start 2\n"
    "wait 200\n"
    "press start 2\n"
    "until16 0053 == 8610\n"
)
# Tour 0 (Crawler) is original native's default. Tour 2 (Shuffler)
# is independently observed with one Down edge in the source original menu.
# These are *proposals* for 2P, whose stock controller ownership and exact
# course-entry bytes must be executed and checked before accepting footage.
TARGETS = {
    "zoom-zoo": ("Zoom Zoo", 2, 0, 1, "circuit-a", "graded/circuit geometry scout"),
    "bowl": ("Bowl", 3, 0, 2, "stunt", "bowl vertical profile scout"),
    "looper": ("Looper", 11, 2, 0, "race-a", "loop topology scout"),
    "megajump": ("MegaJump", 12, 2, 1, "circuit-a", "ramp/jump scout"),
    "jumps": ("Jumps", 13, 2, 2, "stunt", "repeated-ramp stunt scout"),
    "hill-climb": ("Hill Climb", 23, 4, 2, "stunt", "actual hill/slope geometry scout"),
}

def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def dynamic_module():
    path = ROOT / "tools/showcase/build_dynamic_2p_routes.py"
    spec = importlib.util.spec_from_file_location("ur_dynamic_capture_routes", path)
    if spec is None or spec.loader is None:
        raise ValueError("Missing qualified asymmetric 2P route generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def validate_catalog(data: dict) -> None:
    if data.get("schema_version") != 1 or len(data.get("courses", [])) != 45:
        raise ValueError("Not the 45-course source-catalog contract")
    courses = {row["name"]: row for row in data["courses"]}
    for key, (name, stream, tour, slot, kind, _) in TARGETS.items():
        course = courses.get(name)
        if course is None or (
            course["stream_index"], course["tour_index"] - 1,
            course["tour_slot"] - 1, course["track_kind"]
        ) != (stream, tour, slot, kind):
            raise ValueError(f"Candidate {key}: catalog name/course/tour/slot changed")

def menu_route(source: str, key: str) -> str:
    if key not in TARGETS:
        raise ValueError("No pinned course selection route")
    name, stream, tour, row, kind, expectation = TARGETS[key]
    if source.count(SOURCE_ANCHOR) != 1 or source.count("until 0E1F != 00\n") != 1:
        raise ValueError("Unknown native 2P menu/GO anchors")
    if tour not in (0, 2, 4):
        raise ValueError("Only default Crawler and tier-zero Shuffler/Walker prospective routes supported")
    section = [
        "press p2:start 2",
        "until 009F == 6D 1200",
        "wait 60",
    ]
    if tour:
        # Original one-edge Shuffler (tour index 2) is independently
        # source verified. Second-edge Walker index 4 is prospective and
        # must be guest-state-checked; no false assertion of proven 2P UI.
        for _ in range(tour // 2):
            section += ["press down 2", "wait 12"]
        section += [f"until 009B == {tour:02X} 600", "wait 30"]
    section += [
        "press start 2",
        "until 009F == 92 1200",
        "wait 60",
    ]
    for _ in range(row):
        section += ["press down 2", "wait 12"]
    section += [
        f"until 009B == {row:02X} 600",
        "wait 30",
        "press start 2",
        "until 009F == 16 1200",
        "wait 60",
        f"until 00CE == {stream-1:02X} 600",
        f"dump verified-course-{stream:02d}-loaded",
        "press start 2",
        "until16 0053 == 8610",
        "until 0313 == 01 1800",
        f"dump verified-course-{stream:02d}-active",
    ]
    return source.replace(SOURCE_ANCHOR, "\n".join(section) + "\n", 1)

def produce(source: str, key: str, profile: str) -> tuple[str, dict]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    validate_catalog(catalog)
    dynamic = dynamic_module()
    menu = menu_route(source, key)
    routed, receipt = dynamic.produce(menu, profile)
    name, stream, tour, row, kind, expectation = TARGETS[key]
    data = {
        **receipt,
        "course": name,
        "stream_index": stream,
        "runtime_expected_track_byte_7E00CE": f"{stream - 1:02X}",
        "track_kind_catalogued": kind,
        "tour_index_zero_based": tour,
        "track_row_zero_based": row,
        "menu_selection_source_identity": "source-derived original menu controls; 2P route must independently execute",
        "tour_navigation_evidence": ("2P Shuffler A/Start 009F=92 and 009F=16 source-probed in run 39355869639" if tour == 2 else ("default Crawler" if tour == 0 else "prospective second down edge, NOT source-verified in 2P")),
        "source_catalog_sha256": hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
        "source_original_native_menu_sha256": sha(source),
        "topology_expectation": expectation,
        "topology_visually_verified": False,
        "2p_tour_track_navigation_executed": False,
        "successful_tricks_executed": False,
        "course_result_or_parity_claim": False,
        "capture_status": "candidate_source_only_must_execute_and_check",
    }
    return routed, data

def self_test():
    dynamic = dynamic_module()
    fixture = (
        "turbo on\n" + SOURCE_ANCHOR + "until 0E1F != 00\ndump go\n"
        + dynamic.EXPECTED_TAIL + "\n"
    )
    validate_catalog(json.loads(CATALOG.read_text(encoding="utf-8")))
    results = []
    for name in TARGETS:
        for profile in dynamic.ROUTES:
            script, receipt = produce(fixture, name, profile)
            assert "until 0313 == 01 1800" in script
            assert f"until 00CE == {TARGETS[name][1]-1:02X} 600" in script
            assert receipt["capture_status"].startswith("candidate_")
            assert not receipt["topology_visually_verified"]
            assert receipt["post_go_scripted_frames"] >= 1150
            assert script.count("turbo off\n") == 1
            assert fixture.split("press p2:start 2")[0] == script.split("press p2:start 2")[0]
            results.append((name, profile))
    assert len(results) == 12
    for wrong in [fixture.replace("until16 0053 == 8610", "wait 5"),
                  fixture.replace("press p2:start 2", "press p2:a 2")]:
        try:
            produce(wrong, "jumps", "p1-leads")
        except ValueError:
            pass
        else:
            raise AssertionError("Unsupported 2P menu accepted")
    print(f"TOPOLOGY_ROUTE_SOURCE_PREFLIGHT PASS {len(results)} candidates")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--cases", nargs="+", default=["looper", "megajump", "jumps"])
    parser.add_argument("--profiles", nargs="+", default=["p1-leads", "p2-leads"])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    if not args.source or not args.out:
        parser.error("--source and --out required")
    source = args.source.read_text(encoding="utf-8")
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "UR-NATIVE-2P-TOPOLOGY-PROSPECTS/1",
        "catalog_sha256": hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
        "base_route_sha256": sha(source),
        "native_course_identity_gate": "7E:00CE must equal zero-based stream index",
        "topology_and_airtime_claim": "UNVERIFIED, DO NOT USE AS PROMOTIONAL FOOTAGE YET",
        "cases": {},
    }
    for case in args.cases:
        for profile in args.profiles:
            if case not in TARGETS or profile not in dynamic_module().ROUTES:
                parser.error(f"Unknown case/profile {case}/{profile}")
            script, claim = produce(source, case, profile)
            filename = f"{case}-{profile}.txt"
            (args.out / filename).write_text(script, encoding="utf-8")
            manifest["cases"][filename] = claim
    (args.out / "topology-candidate-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"cases": list(manifest["cases"]), "status": "source_only"}, indent=2))

if __name__ == "__main__":
    main()
