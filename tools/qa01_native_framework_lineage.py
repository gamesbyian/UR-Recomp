#!/usr/bin/env python3
"""QA-01: distinguish actual Windows/Modern SNESRecomp build lineages.

Static, fail-closed repository manifest/workflow check; it does not identify
any downloaded ZIP without its exact manifest/build receipt and does not
claim native/original gameplay parity. It guards against treating an
independent Baldosa attract reference as a Windows legacy candidate pass.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLCHAIN = ROOT / "tools/toolchain.json"
TOOL_ENTRY = ROOT / "tools/toolchain-entries/snesrecomp.json"
WINDOWS = ROOT / ".github/workflows/windows-native-smoke.yml"
ROUTER = ROOT / ".github/workflows/modern-native-heavy-router.yml"
SHARED = ROOT / ".github/workflows/modern-shared-native-acceptance.yml"
BALDOSA = ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"

SCHEMA = "UR-QA01-NATIVE-SNESRECOMP-FRAMEWORK-LINEAGE/1"
LEGACY = "cd5875cbdaf19f5e324272b1f8051d671fce9215"
NEWER = "075fbe4c8e0d97b0013be541795c39cb644a9709"
GAME = "10b864b9d14a7b7416dd909eb7b054c88faef101"
URL = "https://github.com/RetroPortingToolKit/snesrecomp.git"


def required(source: str, needle: str, scope: str) -> None:
    if needle not in source:
        raise ValueError(f"{scope}: absent source-build identity {needle!r}")


def lineage(toolchain: str, entry: str, windows: str, router: str,
            shared: str, baldosa: str) -> dict:
    try:
        tooling = json.loads(toolchain)
        detail = json.loads(entry)
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid exact toolchain JSON") from exc
    matches = [t for t in tooling.get("tools", [])
               if isinstance(t, dict) and t.get("id") == "snesrecomp"]
    if len(matches) != 1:
        raise ValueError("toolchain must define one snesrecomp identity")
    for label, record in (("toolchain.json", matches[0]),
                          ("toolchain-entries/snesrecomp.json", detail)):
        if record.get("id") != "snesrecomp" or record.get("revision") != LEGACY:
            raise ValueError(f"{label}: legacy framework revision drifted")
        if record.get("url") != URL:
            raise ValueError(f"{label}: framework origin drifted")

    # The exact operations below matter: an import or comment mentioning an
    # upstream gitlink is not evidence that the production build uses it.
    required(windows, "python tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only",
             "Windows portable build")
    required(windows, 'FRAMEWORK="$GITHUB_WORKSPACE/.tools/src/snesrecomp"',
             "Windows portable build")
    required(windows, '-DSNESRECOMP_ROOT="$FRAMEWORK"',
             "Windows portable build")
    required(windows, "tools/assemble_windows_package.py assemble",
             "Windows portable package")

    required(router, "python3 tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only",
             "Modern canonical router")
    required(router, 'FRAMEWORK="$GITHUB_WORKSPACE/.tools/src/snesrecomp"',
             "Modern canonical router")
    required(router, "modern-native-canonical-candidate",
             "Modern canonical router")
    required(router, "uses: ./.github/workflows/windows-native-smoke.yml",
             "Modern Windows router")

    required(shared, "python3 tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only",
             "Modern shared default")
    required(shared, 'FRAMEWORK="$GITHUB_WORKSPACE/.tools/src/snesrecomp"',
             "Modern shared default")
    required(shared, "inputs.canonical_candidate != true",
             "Modern shared default")
    required(shared, "inputs.canonical_candidate == true",
             "Modern shared borrowed candidate")
    required(shared, "modern-native-canonical-candidate",
             "Modern shared borrowed candidate")

    required(baldosa, f'test "$(git -C baldosa rev-parse HEAD)" = {GAME}',
             "Baldosa game guest")
    required(baldosa,
             f'test "$(git -C baldosa/snesrecomp rev-parse HEAD)" = {NEWER}',
             "Baldosa fork")
    required(baldosa, "repository: gamesbyian/uniracers-recomp",
             "Baldosa guest checkout")
    required(baldosa, "ref: 10b864b9d14a7b7416dd909eb7b054c88faef101",
             "Baldosa game checkout")
    required(baldosa, "cmake -S baldosa",
             "Baldosa independent Windows title")

    return {
        "schema": SCHEMA,
        "legacy_framework": LEGACY,
        "baldosa_game": GAME,
        "baldosa_framework": NEWER,
        "default_shared_modern_framework": LEGACY,
        "router_canonical_modern_framework": LEGACY,
        "windows_portable_smoke_framework": LEGACY,
        "baldosa_independent_windows_title_framework": NEWER,
        "borrowed_canonical_candidate_requires_upstream_artifact_identity": True,
        "the_two_windows_builds_are_the_same_executable": False,
        "downloaded_windows_zip_exact_binary_identity_proven_here": False,
        "baldosa_reference_match_proves_windows_portable_attract_parity": False,
        "runtime_original_native_cpu_beam_parity_proven": False,
        "strict_usa_complete_event_credit": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error("refuse to overwrite an earlier source preflight")
    output = lineage(
        TOOLCHAIN.read_text(encoding="utf-8"),
        TOOL_ENTRY.read_text(encoding="utf-8"),
        WINDOWS.read_text(encoding="utf-8"),
        ROUTER.read_text(encoding="utf-8"),
        SHARED.read_text(encoding="utf-8"),
        BALDOSA.read_text(encoding="utf-8"),
    )
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print(json.dumps({
        "default_modern": output["default_shared_modern_framework"][:8],
        "baldosa": output["baldosa_framework"][:8],
        "same_windows_executable": False,
        "complete_event_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
