#!/usr/bin/env python3
"""Execute bounded real Windows source comparison using independently linked PEs.

This is a draft QA08 research producer only. It neither repairs the renderer
nor grants QA08/QA10 acceptance. No ROM, PE, SRAM or P7 imagery is retained in
the uploaded diagnostics. Real source comparisons require the original
authenticated 2014 and compiled Windows reference archives.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

try:
    from tools.baldosa_windows_native_pause_route import run_route
    from tools.qa08_late_effective_trace_verify import (
        EXPECTED_CRC, EXPECTED_ROUTE, verify, summarize_trace)
except ImportError:
    from baldosa_windows_native_pause_route import run_route
    from qa08_late_effective_trace_verify import (
        EXPECTED_CRC, EXPECTED_ROUTE, verify)

ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
ENV = "UR_QA08_LATE_EFFECTIVE_PIXEL_TRACE"


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def source_lines(log: str) -> str:
    """No other game stdout, controller data or unbounded output is retained."""
    selected = [line for line in log.splitlines()
                if line.startswith("UR_QA08_LATE_")]
    if len(selected) > 1000:
        raise ValueError("native QA08 source logger exceeded bounded output")
    raw = "\n".join(selected) + "\n"
    if len(raw) > 500_000:
        raise ValueError("native QA08 source logger bytes exceeded limit")
    return raw


def run_pair(off: Path, on: Path, rom: Path, route: Path, original: Path,
             native: Path, out: Path, timeout: int) -> dict:
    if (not 1 <= timeout <= 720 or out.exists() or
        any(not p.is_file() for p in (off, on, rom, route, original, native))):
        raise ValueError("missing qualified source paths, invalid limit or output collision")
    if sha(rom.read_bytes()) != ROM_SHA or sha(route.read_bytes()) != EXPECTED_ROUTE:
        raise ValueError("US retail ROM or actual controller route SHA differs")
    off_sha, on_sha = sha(off.read_bytes()), sha(on.read_bytes())
    if off_sha == on_sha:
        raise ValueError("independently linked observer ON/OFF PEs are identical")
    out.mkdir(parents=True)
    results: dict = {
        "schema": "QA08-native-Windows-optin-pixel-witness/1",
        "original_USA_ROM_sha256": ROM_SHA,
        "real_two_pad_script_sha256": EXPECTED_ROUTE,
        "actual_off_executable_sha256": off_sha,
        "actual_on_executable_sha256": on_sha,
        "actual_source_process_runs": 0,
        "complete_guest_replay_equivalence_proven": False,
        "same_epoch_ON_OFF_guest_CRC_equal": False,
        "historical_RF017_guest_CRC_qualified": False,
        "unadmitted_PPU_observation_only": False,
        "actual_source_P7_ON_OFF_noninterference_proven": False,
        "QA08_QA10_release_accepted": False,
    }
    manifest = out / "status.json"

    try:
        for label, exe in (("off", off), ("on", on)):
            parent = out / label
            parent.mkdir()
            old = os.environ.get(ENV)
            if label == "on":
                os.environ[ENV] = "1"
            else:
                os.environ.pop(ENV, None)
            try:
                crcs, log = run_route(
                    exe.resolve(), rom.resolve(), route.resolve(),
                    parent, pause=False, video="windows", timeout=timeout)
            finally:
                if old is None:
                    os.environ.pop(ENV, None)
                else:
                    os.environ[ENV] = old
            results["actual_source_process_runs"] += 1
            path = out / f"{label}-guest-crc.txt"
            path.write_text("\n".join(c.lower() for c in crcs) + "\n", encoding="ascii")
            (out / f"{label}-route.bin").write_bytes(route.read_bytes())
            (out / f"{label}-source.log").write_text(source_lines(log), encoding="utf-8")
            results[f"{label}_CRC_sha256"] = sha(path.read_bytes())
            results[f"{label}_bounded_source_rows"] = len(
                (out / f"{label}-source.log").read_text().splitlines())
            results[f"{label}_matches_historical_RF017_CRC"] = (
                results[f"{label}_CRC_sha256"] == EXPECTED_CRC)
            results[f"{label}_actual_guest_frames"] = len(crcs)
        results["same_epoch_ON_OFF_guest_CRC_equal"] = (
            results["off_CRC_sha256"] == results["on_CRC_sha256"] and
            results["off_actual_guest_frames"] == 5484 and
            results["on_actual_guest_frames"] == 5484)
        if not results["same_epoch_ON_OFF_guest_CRC_equal"]:
            raise ValueError("observer ON/OFF changed real guest CRC or full 5484-frame inventory")
        if not results["off_matches_historical_RF017_CRC"]:
            # Newer host/guest epoch: inspect selected PPU words without
            # pretending old source frames or input epochs are equivalent.
            try:
                selected = summarize_trace(
                    (out / "on-source.log").read_text(encoding="utf-8"))
                results["unadmitted_live_PPU_sample"] = [{
                    "xy": row["xy"],
                    "actual_renderer": row["actual_renderer"],
                    "main_layer": row["main_layer"],
                    "main_directcolor": row["main_directcolor"],
                    "main_selected_palette_index": row["main_selected_palette_index"],
                    "main_actual_resolved_rgb555": row["main_actual_resolved_rgb555"],
                    "main_current_index_CGRAM_word": row["main_current_index_CGRAM_word"],
                    "current_main_CGRAM_6c_6f": row["current_main_CGRAM_6c_6f"],
                    "new_native_final_RGB5": row["new_native_final_RGB5"],
                    "same_historical_original_native_source_epoch_proven": False,
                } for row in selected["anchors"]]
                results["unadmitted_PPU_observation_only"] = True
            except (ValueError, OSError) as exc:
                results["unadmitted_observer_refusal"] = str(exc)[:1000]
            raise ValueError("same-epoch ON/OFF guest CRC matched but historic RF017 CRC did not")
        attested = verify(
            out / "on-source.log", out / "off-source.log", original,
            out / "on-guest-crc.txt", out / "off-guest-crc.txt",
            out / "on-route.bin", out / "off-route.bin", native)
        results["effective_source"] = attested
        results["complete_guest_replay_equivalence_proven"] = True
        results["historical_RF017_guest_CRC_qualified"] = True
        # Whole-P7 ON/OFF capture is still a separate required experiment.
        results["final_diagnostic_outcome"] = "source-only accepted; P7/beam/release HOLD"
        return results
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        results["final_diagnostic_outcome"] = "REFUSED"
        results["refusal"] = str(exc)[:1000]
        raise
    finally:
        manifest.write_text(json.dumps(results, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("off-exe", "on-exe", "rom", "script",
                "original-inner", "native-outer", "out"):
        p.add_argument("--" + arg, type=Path, required=True)
    p.add_argument("--timeout", type=int, default=360)
    a = p.parse_args()
    try:
        result = run_pair(a.off_exe, a.on_exe, a.rom, a.script,
                          a.original_inner, a.native_outer, a.out, a.timeout)
        (a.out / "witness.json").write_text(json.dumps(result, indent=2,
                                                       sort_keys=True) + "\n",
                                            encoding="utf-8")
    except (ValueError, RuntimeError, OSError) as exc:
        p.exit(2, "QA08_WIN32_EFFECTIVE_SOURCE_REFUSED: " + str(exc) + "\n")
    print("QA08_WIN32_EFFECTIVE_SOURCE witness=source-qualified P7_and_release=HOLD")


if __name__ == "__main__":
    main()
