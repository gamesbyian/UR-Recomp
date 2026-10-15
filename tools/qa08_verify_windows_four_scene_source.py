#!/usr/bin/env python3
"""Recompute every genuine 2P RGB5 pixel: Snes9x, old Linux, corrected Win32.

Offline, ROM-free, dependency-free and fail-closed on four exact GitHub Actions
artifact ZIP SHA-256 identities. Runs over the raw independently produced
256x224 video bytes, not a producer's summary or an image preview. Window
source is opt-in title read-only graphics. No guest event or release approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

SCHEMA = "qa08-win32-independent-4scene-original-source-rgb5/1"
EXPECTED = {
    "windows": "d15d1ca788661578f84b419d47da72ee88ec03eaeeb6e37f87affc4036efe38b",
    "native": "51593205e289a532666bc0163e66eb5f1da85c8c6046232e37b671f1f7482bf1",
    "postgo": "6e5d488230c11d3dfcd144b6a7cbc8c25d7acfcb4f95b776a85071dd3487f5e3",
    "countdown": "56ec0011a3559f5953578c495d080d0150f2a06fb7a76c2e437fab781e2b2ce6",
}
RUN = 38697704517
ARTIFACT = 11954613310
SOURCE_HEAD = "39ce09567a136904e565b6a43d805d48f089f32b"
EXE_SHA = "7431889698913feadab76261caf3b00b82d1d9a1466a8260d9b7512d8328324e"
ROWS = ((1856, 1855, "countdown", 971),
        (2192, 2191, "postgo", 512),
        (2208, 2207, "postgo", 512),
        (2224, 2223, "postgo", 512))
PAM_HEADER = (
    b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
    b"TUPLTYPE RGB_ALPHA\nENDHDR\n"
)
PX = 256 * 224


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def open_exact(path: Path, kind: str) -> zipfile.ZipFile:
    if digest(path.read_bytes()) != EXPECTED[kind]:
        raise ValueError(f"{kind} whole artifact SHA256 not independently pinned")
    return zipfile.ZipFile(path)


def decode_original(raw: bytes) -> bytes:
    if len(raw) != PX * 4:
        raise ValueError("original Snes9x callback was cropped/invalid")
    # Core reports four bytes B,G,R,X, RGB565 expanded to 8 channels.
    # Snes9x's G6 -> native RGB5 quantization is the ONLY approved transform.
    out = bytearray(PX * 3)
    for i in range(PX):
        b, g, r, _ = raw[4*i:4*i+4]
        green5 = (g >> 2) >> 1
        out[3*i:3*i+3] = bytes((r, (green5 << 3) | (green5 >> 2), b))
    return bytes(out)


def decode_p7(raw: bytes) -> bytes:
    if len(raw) != len(PAM_HEADER) + PX * 4 or not raw.startswith(PAM_HEADER):
        raise ValueError("native source is not exact 256x224 RGBA P7")
    source = memoryview(raw)[len(PAM_HEADER):]
    rgb = bytearray(PX * 3)
    for i in range(PX):
        rgb[i*3:i*3+3] = source[i*4:i*4+3]
    return bytes(rgb)


def compare_rgb(reference: bytes, baseline: bytes, corrected: bytes) -> dict:
    if len(reference) != PX*3 or len(baseline) != PX*3 or len(corrected) != PX*3:
        raise ValueError("full 57,344-pixel source RGB is required")
    before_rows, after_rows, changed_rows = {}, {}, {}
    for p in range(PX):
        i = p*3
        row = p // 256
        a = baseline[i:i+3] != reference[i:i+3]
        b = corrected[i:i+3] != reference[i:i+3]
        c = corrected[i:i+3] != baseline[i:i+3]
        if a: before_rows[row] = before_rows.get(row, 0) + 1
        if b: after_rows[row] = after_rows.get(row, 0) + 1
        if c: changed_rows[row] = changed_rows.get(row, 0) + 1
    return {
        "previous_wrong": sum(before_rows.values()),
        "corrected_wrong": sum(after_rows.values()),
        "corrected_source_changed_pixels": sum(changed_rows.values()),
        "previous_wrong_rows": before_rows,
        "corrected_wrong_rows": after_rows,
        "source_changed_rows": changed_rows,
    }


def adjudicate(window: zipfile.ZipFile, native: zipfile.ZipFile,
               originals: dict[str, zipfile.ZipFile]) -> dict:
    manifest = json.loads(window.read("qa08-windows-source-result.json"))
    if (
        manifest.get("schema") != "qa08-windows-source-bound-2P-original-ppu-candidate/1"
        or manifest.get("observed_from_same_windows_executable") != EXE_SHA
        or manifest.get("actual_complete_native_guest_frames") != 2473
        or manifest.get("actual_frames_observed") != [1856, 2192, 2208, 2224]
        or manifest.get("source_geometry") != [256, 224]
        or manifest.get("release_graphics_gate_approved") is not False
    ):
        raise ValueError("Windows source receipt differs from real exact candidate")
    files = []
    seen_moving_originals = set()
    for guest, callback, kind, wrong_expected in ROWS:
        prefix = f"ur-baldosa-original-source-{guest:06d}.pam"
        win_raw = window.read("source/" + prefix)
        old_raw = native.read("qa08-native-baseline/" + prefix)
        experimental_raw = native.read("qa08-native-experiment/" + prefix)
        original_path = (
            ("qa08-original-countdown-17/" if kind == "countdown" else
             "qa08-original-source-window/") +
            f"frame_{callback:06d}_256x224.raw"
        )
        original_raw = originals[kind].read(original_path)
        orig_sha = digest(original_raw)
        if kind == "postgo":
            if orig_sha in seen_moving_originals:
                raise ValueError("moving source callback duplicated/held")
            seen_moving_originals.add(orig_sha)
        if win_raw != experimental_raw:
            raise ValueError(f"Windows guest{guest} differs from experimental native source")
        expected_row = next((row for row in manifest["source_sha_controls"]
                             if row["actual_guest_frame"] == guest), None)
        if not expected_row or expected_row["actual_source_P7_sha256"] != digest(win_raw):
            raise ValueError(f"Windows P7 original bytes/receipt disagree at {guest}")
        result = compare_rgb(decode_original(original_raw), decode_p7(old_raw),
                             decode_p7(win_raw))
        if (result["previous_wrong"] != wrong_expected
            or result["corrected_wrong"] != 0
            or result["corrected_source_changed_pixels"] != wrong_expected):
            raise ValueError(f"original/native strict source mismatch at guest {guest}")
        if kind == "postgo" and result["source_changed_rows"] != {111: 256, 113: 256}:
            raise ValueError(f"active 2P corrected unexpected non-seam pixels: {guest}")
        if kind == "countdown" and (
            result["source_changed_rows"].get(111) != 256
            or result["source_changed_rows"].get(113) != 256
            or sum(v for y,v in result["source_changed_rows"].items()
                   if y not in (111,113)) != 459
        ):
            raise ValueError("countdown contour/seam source changes not preserved")
        files.append({
            "windows_native_guest": guest,
            "genuine_original_callback": callback,
            "original_raw_BGRX_sha256": orig_sha,
            "prior_native_P7_sha256": digest(old_raw),
            "corrected_real_windows_P7_sha256": digest(win_raw),
            "independently_recomputed_RGB5": {
                k: v for k,v in result.items()
                if k in ("previous_wrong","corrected_wrong","corrected_source_changed_pixels")
            },
            "source_changed_rows": result["source_changed_rows"],
        })
    return {
        "schema": SCHEMA,
        "Windows_source_commit": SOURCE_HEAD,
        "Windows_workflow_run": RUN,
        "Windows_source_artifact": ARTIFACT,
        "Windows_executable_sha256": EXE_SHA,
        "original_source_archives_sha256": {key: EXPECTED[key] for key in
                                           ("countdown", "postgo")},
        "independent_prior_native_archive_sha256": EXPECTED["native"],
        "real_windows_capture_archive_sha256": EXPECTED["windows"],
        "all_original_scenes_native_size": [256,224],
        "no_crop_mask_spatial_alignment_or_temporal_synthesis": True,
        "frames": files,
        "all_four_original_native_windows_RGB5_exact": True,
        "Windows_guest_CRC_2473_present_but_independent_state_parity_unproven": True,
        "not_proof_of_continuous_1P_2P_transition_result_or_hardware": True,
        "current_remastered_racer_art_owner_approved": False,
        "release_quality_ledger_gates_admitted": 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    for kind in ("windows", "native", "postgo", "countdown"):
        ap.add_argument("--" + kind + "-zip", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    archives = {k: open_exact(getattr(args, k + "_zip"), k)
                for k in ("windows", "native", "postgo", "countdown")}
    try:
        report = adjudicate(archives["windows"], archives["native"], archives)
    finally:
        for f in archives.values(): f.close()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("QA08_WIN32_4SCENE_SOURCE_AUTHENTICATED "
          "original_frames=4 wrong_previous=2507 wrong_corrected=0 "
          "all_source_57344_RGB5_exact=1 release_approved=0")


if __name__ == "__main__":
    main()
