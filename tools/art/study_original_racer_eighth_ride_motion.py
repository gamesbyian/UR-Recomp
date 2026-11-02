#!/usr/bin/env python3
"""Nine source-authored 2026 ride-phase GLBs versus verified 1994 source motion.

No 1994 guest-frame is assigned a time in this 2026 rig. Reuses the single
authentic-source evaluator and retains its original historical five-point mode.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.art.study_original_racer_continuous_ride_motion import evaluate
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from study_original_racer_continuous_ride_motion import evaluate
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-EIGHTH-RIDE-SOURCE-UNPAIRED-MOTION/1"
TIMES = ("0.0", "0.125", "0.25", "0.375", "0.5",
         "0.625", "0.75", "0.875", "1.0")
# Exact independently downloaded actual five-parent/16-material source-owned
# GLB bytes from successful original experimental rig CI run 41385793054.
SHA = {
    "0.0": "71c5e5b6dee81b9051027e6106c91c869b3ff518d4c30f9f649206f30284956a",
    "0.125": "bd3b13b13514a304d3f5113528cb6133844b8354f6267ff4737e6214887e7aa7",
    "0.25": "22ccd778a650910a8ffc67d6a260386a8312d38afa851bdb601cb8e1acfb5126",
    "0.375": "5cc001680c872f4123268907e9ad58246fc6fc431bb0cfa3bf31ec212f8ac914",
    "0.5": "f5d6b0f29e00b6f04fe4d7561b1cda87674b6a488f66e2900e8f141d0fa2147f",
    "0.625": "7a6776f8b0f50db384da98c466258f58a5bcb45efca348dc6626f946e9317a77",
    "0.75": "7075d09cfabae480ad8c08c8c2db553a01fcde4ead8f0680966ce39ce81dadeb",
    "0.875": "64aaa28a35f46e6124860be6a32cdac0ee00e34800562e3099ca7f793513cf84",
    "1.0": "12c8a01c8a4218bdcd20048a4d7d165cd88b406de5494f67b213e2f0579fe90a",
}



def registered_source_time_evidence(corpus_path: Path,
                                    verified_corpus_sha256: str) -> dict:
    """Bind a real ROM-composed sprite corpus to its *authored* time registry.

    A verified source-ROM raster is not independently verified original game
    PPU/OAM frame cadence. Never infer that its guest-frame numbers or holds
    were observed as a live simulation trace.
    """
    raw = corpus_path.read_bytes()
    if (type(verified_corpus_sha256) is not str
            or hashlib.sha256(raw).hexdigest() != verified_corpus_sha256):
        raise ValueError("authenticated source corpus SHA identity changed")
    source = json.loads(raw)
    if (not isinstance(source, dict)
            or source.get("source_kind")
                != "deterministic_canonical_USA_ROM_registered_composition"
            or source.get("source_rom_verified_and_used_for_composition") is not True
            or source.get("native_live_original_PPU_or_1994_3d_camera_independently_verified") is not False
            or not isinstance(source.get("source_temporal_frame_observations"), list)):
        raise ValueError("wrong or unclassified original source sampling evidence")
    return {
        "original_64px_rasters_composed_from_sha_authenticated_original_rom": True,
        "source_frame_order_is_registry_authored": True,
        "source_registered_guest_frame_integer_adjacency_measured": True,
        "original_live_emulator_ppu_frame_timing_independently_verified": False,
        "original_live_gameplay_hold_cadence_proven": False,
        "source_visible_alpha_anchor_is_physical_ground_contact": False,
    }


def compute(corpus: Path, camera: Path, samples: dict[str, Path]) -> dict:
    if set(samples) != set(TIMES):
        raise ValueError("exact nine 2026-authored ride grid samples required")
    result = evaluate(corpus, samples, camera,
                      sample_times=TIMES, pinned_glbs=SHA)
    source_evidence = registered_source_time_evidence(
        corpus, result["source_original_corpus_sha256"])
    if (result["exact_ride_grid"] != list(TIMES)
            or result["first_last_authored_cycle_4x_pixel_xor"] != 0
            or len(result["uniform_2026_phase_transition_diagnostics"]) != 8
            or not result["all_transition_pairs_predeclared_without_frame_matching"]
            or result["original_1994_camera_or_pose_or_cadence_recovered"]
            or result["shipping_art_approved"]):
        raise ValueError("actual source rhythm/phase boundary or loop closure lost")
    result["schema"] = SCHEMA
    result["source_temporal_evidence_class"] = source_evidence
    result["actual_GLBS_from_existing_draft_exporter_run_id"] = 41385793054
    result["quarter_phase_grid_had_720_degree_wobble_aliasing"] = True
    result["eighth_phase_wobble_extrema_source_authored_deg"] = {
        "0.125": 3, "0.375": -3, "0.625": 3, "0.875": -3,
    }
    result["actual_distinct_3d_mesh_states_previously_independently_measured"] = 7
    result["distinct_mesh_states_do_not_mean_original_1994_viewpoints"] = True
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--camera", type=Path, required=True)
    ap.add_argument("--ride-sample", nargs=2, action="append", required=True,
                    metavar=("TIME", "ARTIFACT_DIRECTORY"))
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    roots = dict((t, Path(path)) for t, path in args.ride_sample)
    if len(roots) != len(args.ride_sample):
        ap.error("duplicate 2026 ride phase")
    output = json.dumps(compute(args.corpus, args.camera, roots),
                        sort_keys=True, indent=2) + "\n"
    if args.out:
        publish_text_once(args.out, output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
