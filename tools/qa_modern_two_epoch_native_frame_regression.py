#!/usr/bin/env python3
"""Independently compare two original 18-screen integrated Win32 SDL ZIP cohorts.

Original GitHub Actions artifacts are inputs, not reconstructed screenshots.
Each epoch must provide six ZIP files named executable.zip, root.zip,
navigation.zip, extra-root.zip, authentic.zip and title.zip in its directory.
Requires two distinct exact source checkouts and two distinct AMD64 binaries.
Every original P7/PNG, receipt and successful native process log is re-read.
A matching pixel hash is technical regression evidence only: never a visual,
guest state, physical controller, physical display, or release approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

try:
    from tools import qa_modern_visual_actions_archive as archive
    from tools import qa_modern_visual_actions_batch as batch
except ModuleNotFoundError:
    import qa_modern_visual_actions_archive as archive
    import qa_modern_visual_actions_batch as batch

ROLES = {
    "root": {
        ("root-quit", (1024, 768)), ("root-quit", (1280, 720)),
    },
    "navigation": {
        ("multiplayer-unrecorded", (1280, 720)),
        ("options-p1", (1280, 720)),
        ("practice-picker", (1280, 720)),
        ("profile-first-p1", (1280, 720)),
        ("records-keyboard", (1024, 768)),
    },
    "extra-root": {("root-quit", (856, 480))},
    "authentic": {
        ("authentic-stock", (1024, 768)),
        ("authentic-stock", (1280, 720)),
    },
    "title": {
        (route, dims)
        for route in ("title-still", "title-entered-root",
                      "title-reduced-still", "title-reduced-entered-root")
        for dims in ((1024, 768), (1280, 720))
    },
}
TITLE_ROUTES = frozenset(key[0] for key in ROLES["title"])
ROOT_GEOMETRY = {
    (1024, 768): "raster=256x224 root=8,10,240,204",
    (1280, 720): "raster=342x224 root=11,10,320,204",
    (856, 480): "raster=342x224 root=11,10,320,204",
}
SAVE_LOG = re.compile(
    r"UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=(\d+) "
    r"guest_frame=(\d+) output=(\d+)x(\d+) "
    r"source=SDL_RenderReadPixels backend=sdl3"
)
EXPECTED_COUNT = sum(len(v) for v in ROLES.values())
assert EXPECTED_COUNT == 18


class RegressionError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_stage(route: str, dims: tuple[int, int], before: str,
                draw: int, guest_frame: int) -> None:
    """Recheck semantic stage before SDL readback; never trust route label alone."""
    if route == "authentic-stock":
        if (draw != 240 or "[snes_load]" not in before or
                "UR_BALDOSA_MODERN_TITLE " in before or
                "UR_BALDOSA_MODERN_DESTINATION stage=" in before or
                "UR_BALDOSA_MODERN_ROOT opened=1" in before or
                "UR_BALDOSA_MODERN_ROOT painted=1" in before):
            raise RegressionError("Authentic stock source isolation or frame absent")
        return
    if "UR_BALDOSA_MODERN_ROOT opened=1" not in before:
        raise RegressionError("Modern native root not genuinely entered")
    if route in TITLE_ROUTES:
        src_w = 256 if dims == (1024, 768) else 342
        if f"UR_BALDOSA_MODERN_TITLE painted=1 raster={src_w}x224 host=modern" not in before:
            raise RegressionError("native title source did not paint")
        entered = "entered-root" in route
        if entered:
            expected_frame = 60 if "reduced" in route else 74
            if (draw != 100 or guest_frame < expected_frame or
                    "UR_BALDOSA_MODERN_TITLE native_p1_start=1 frame=60" not in before or
                    f"UR_BALDOSA_MODERN_TITLE entered_root=1 frame={expected_frame}" not in before or
                    "UR_BALDOSA_MODERN_DESTINATION stage=root " +
                    ROOT_GEOMETRY[dims] not in before):
                raise RegressionError("actual P1 title-to-root source handoff absent")
        elif (draw != 40 or guest_frame >= 60 or
              "UR_BALDOSA_MODERN_TITLE entered_root=1" in before or
              "UR_BALDOSA_MODERN_TITLE native_p1_start=1" in before):
            raise RegressionError("title still was captured after P1 handoff")
        return
    expected_stage = archive.ROUTE_STAGES.get(route)
    if expected_stage is None:
        raise RegressionError("unsupported current native route")
    matches = re.findall(
        r"UR_BALDOSA_MODERN_DESTINATION stage=([^\s]+) "
        r"(raster=\d+x\d+ root=\d+,\d+,\d+,\d+) "
        r"source=modern_product_view", before)
    if (not matches or matches[-1] !=
            (expected_stage, ROOT_GEOMETRY[dims])):
        raise RegressionError("actual pre-SDL destination source stage mismatch")


def check_capture(z: zipfile.ZipFile, receipt_member: str,
                  source_sha: str, exe_sha: str) -> dict:
    prefix = receipt_member[:-len("readback-receipt.json")]
    receipt = json.loads(archive.read(z, receipt_member, 64 * 1024))
    if not isinstance(receipt, dict):
        raise RegressionError("invalid native receipt object")
    route = receipt.get("native_semantic_route")
    dims = receipt.get("actual_sdl_renderer_output")
    if (not isinstance(route, str) or not isinstance(dims, list) or
            len(dims) != 2 or any(type(v) is not int for v in dims)):
        raise RegressionError("missing actual route or SDL drawable geometry")
    key = (route, tuple(dims))
    valid_cases = set().union(*ROLES.values())
    if key not in valid_cases:
        raise RegressionError("unqualified actual native screen/size")
    target_mode = "authentic" if route == "authentic-stock" else "modern"
    marker_expected = route not in ("authentic-stock", "root-quit")
    if (receipt.get("schema_version") != 1 or
            type(receipt.get("native_process_exit")) is not int or
            receipt.get("native_process_exit") != 0 or
            receipt.get("SDL_driver") != "windows" or
            receipt.get("execution_mode") != target_mode or
            receipt.get("native_route_marker_observed") is not marker_expected or
            receipt.get("source_sha") != source_sha or
            receipt.get("exe_sha256") != exe_sha or
            receipt.get("requested_window_size") not in (None, dims) or
            receipt.get("visual_approved") is not False or
            receipt.get("hardware_approved") is not False or
            receipt.get("authentic_isolation_approved") is not False or
            receipt.get("release_gate_credit") != 0):
        raise RegressionError("native receipt mode, process, source or approval mismatch")
    png = archive.read(z, prefix + "actual-sdl-drawable.png", archive.MAX_IMAGE)
    if digest(png) != receipt.get("png_sha256"):
        raise RegressionError("original PNG hash mismatch")
    raw_p7s = [name for name in z.namelist()
               if name.startswith(prefix) and name.endswith("/actual-sdl-drawable.pam")]
    raw_logs = [name for name in z.namelist()
                if name.startswith(prefix) and name.endswith("/native-process.log")]
    p7_matches = [name for name in raw_p7s
                  if digest(archive.read(z, name, archive.MAX_IMAGE + 512)) ==
                  receipt.get("p7_sha256")]
    log_matches = [name for name in raw_logs
                   if digest(archive.read(z, name, archive.MAX_LOG)) ==
                   receipt.get("native_process_log_sha256")]
    if len(p7_matches) != 1 or len(log_matches) != 1:
        raise RegressionError("missing or duplicate successful native P7/process")
    raw_p7 = archive.read(z, p7_matches[0], archive.MAX_IMAGE + 512)
    m = archive.P7.match(raw_p7)
    if (not m or tuple(map(int, m.groups())) != key[1] or
            len(raw_p7) != m.end() + dims[0] * dims[1] * 4 or
            raw_p7[m.end():] != archive.png_rgba(png, key[1])):
        raise RegressionError("actual SDL P7 != original lossless PNG bytes")
    log = archive.read(z, log_matches[0], archive.MAX_LOG).decode("utf8", "replace")
    matches = list(SAVE_LOG.finditer(log))
    if (len(matches) != 1 or
            (int(matches[0][3]), int(matches[0][4])) != key[1] or
            receipt.get("observed_in_draw") != int(matches[0][1])):
        raise RegressionError("ambiguous original saved SDL readback")
    check_stage(route, key[1], log[:matches[0].start()],
                int(matches[0][1]), int(matches[0][2]))
    return {
        "route": route, "pixels": dims,
        "source_sha": source_sha, "exe_sha256": exe_sha,
        "p7_sha256": digest(raw_p7),
        "png_sha256": digest(png),
        "process_log_sha256": digest(log.encode("utf8")),
    }


def scan_epoch(folder: Path, source_sha: str, exe_sha: str) -> dict:
    if (not archive.SOURCE_HEX.fullmatch(source_sha) or
            not archive.HEX.fullmatch(exe_sha) or
            folder.is_symlink() or not folder.is_dir()):
        raise RegressionError("unqualified native epoch identity/directory")
    expected_files = {f"{role}.zip" for role in ROLES} | {"executable.zip"}
    observed_files = {p.name for p in folder.iterdir() if p.is_file()}
    if observed_files != expected_files or any((folder / p).is_symlink()
                                               for p in expected_files):
        raise RegressionError("missing or extra original native artifact ZIP")
    actual_pe, size = batch.native_exe_sha(folder / "executable.zip")
    if actual_pe != exe_sha:
        raise RegressionError("native AMD64 executable hash mismatch")
    cases: dict[tuple[str, tuple[int, int]], dict] = {}
    for role, expected in ROLES.items():
        path = folder / f"{role}.zip"
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if len(names) != len(set(names)) or any(
                    name.startswith("/") or "\\" in name or
                    ".." in Path(name).parts for name in names):
                raise RegressionError("unsafe original archive member")
            receipts = [name for name in names
                        if name.endswith("readback-receipt.json")]
            if len(receipts) != len(expected):
                raise RegressionError("wrong screenshot count in original artifact")
            found = set()
            for name in receipts:
                result = check_capture(z, name, source_sha, exe_sha)
                key = (result["route"], tuple(result["pixels"]))
                if key not in expected or key in found or key in cases:
                    raise RegressionError("duplicate or swapped native route")
                found.add(key)
                cases[key] = result
            if found != expected:
                raise RegressionError("missing exact real screenshot in role " + role)
    if len(cases) != EXPECTED_COUNT:
        raise RegressionError("incomplete 18-case actual native epoch")
    return {
        "source_sha": source_sha, "exe_sha256": actual_pe,
        "exe_bytes": size, "cases": cases,
        "original_ZIP_sha256": {
            role: digest((folder / f"{role}.zip").read_bytes())
            for role in ("executable", *ROLES)
        }
    }


def compare_epochs(first: dict, second: dict) -> dict:
    if (first["source_sha"] == second["source_sha"] or
            first["exe_sha256"] == second["exe_sha256"]):
        raise RegressionError("epochs must be distinct compiled source/PE")
    a, b = first["cases"], second["cases"]
    if len(a) != EXPECTED_COUNT or set(a) != set(b):
        raise RegressionError("different original native case inventories")
    changes = [key for key in a if
               a[key]["p7_sha256"] != b[key]["p7_sha256"]]
    return {
        "schema_version": 1,
        "native_capture_pairs": len(a),
        "identical_original_P7_RGBA_cases": len(a) - len(changes),
        "pixel_changed_cases": [
            {"route": key[0], "pixels": list(key[1])} for key in sorted(changes)
        ],
        "exact_pixel_stability": not changes,
        "first_source_sha": first["source_sha"],
        "second_source_sha": second["source_sha"],
        "first_executable_sha256": first["exe_sha256"],
        "second_executable_sha256": second["exe_sha256"],
        "same_executable": False,
        "native_screen_art_approved": False,
        "physical_hardware_approved": False,
        "original_guest_equivalence_approved": False,
        "human_visual_approved": False,
        "release_gate_credit": 0,
        "scope": "source/PE-bound 18 original Win32 SDL screenshots only",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--first", type=Path, required=True)
    p.add_argument("--second", type=Path, required=True)
    p.add_argument("--first-source", required=True)
    p.add_argument("--second-source", required=True)
    p.add_argument("--first-pe", required=True)
    p.add_argument("--second-pe", required=True)
    p.add_argument("--require-identical", action="store_true")
    args = p.parse_args()
    try:
        first = scan_epoch(args.first, args.first_source, args.first_pe)
        second = scan_epoch(args.second, args.second_source, args.second_pe)
        out = compare_epochs(first, second)
        print(json.dumps(out, indent=2))
        return 2 if args.require_identical and not out["exact_pixel_stability"] else 0
    except (ValueError, OSError, zipfile.BadZipFile, KeyError, TypeError) as exc:
        print("INDEPENDENT_NATIVE_SDL_REGRESSION_INCONCLUSIVE:", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
