#!/usr/bin/env python3
"""Plan bounded Pages publication from changes since the last successful site artifact.

A styling-only contributor update overlays its HTML into the previously published
site. No atlas, gallery raster previews, GLBs or measurements are regenerated.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
HTML_ROUTES = {
    "tools/contributor_gallery/index.html": "contributors/index.html",
    "tools/contributor_gallery/references.html": "contributors/references/index.html",
    "tools/contributor_gallery/three-d.html": "contributors/3d/index.html",
    "tools/contributor_gallery/playtest.html": "contributors/playtest/index.html",
}
MODEL_EXACT = {
    "tools/art/candidates/unicycle_shared_rig.scad",
    "tools/art/export_articulated_unicycle.py",
    "tools/art/prepare_model_review_measurement_sidecar.py",
    "analysis/data/racer-hd-replacement-prototype.json",
    "analysis/data/racer-inverse-side-provisional-1205.json",
}
ATLAS_EXACT = {
    "analysis/windows-visual-atlas.json",
    "tools/windows_visual_atlas.py",
    "tools/windows_visual_atlas_intake.py",
}
GALLERY_EXACT = {
    "assets/promo/canonical/blueprint-16x9-logo-left.png",
    "assets/promo/canonical/blueprint-4x3-logo-left.png",
}
ATLAS_PREFIXES = (
    "tools/visual_atlas_web/",
    "media/windows-visual-atlas/approved/",
    "media/showcase/2026-10-20/graphpaper-final/cards/",
    "media/showcase/art-reconstruction/2026-10-10/stock/",
)
GALLERY_PREFIXES = (
    "assets/branding/concepts/",
    "media/showcase/art-reconstruction/2026-11-09/title-screen-racer/",
    "media/showcase/art-reconstruction/2026-11-10/box-art-wheel-contours/",
)


def plan_changes(paths: list[str]) -> dict[str, bool]:
    plan = {"atlas": False, "gallery": False, "model": False, "html": False, "publish": False}
    for path in paths:
        path = path.strip()
        if not path:
            continue
        if path in HTML_ROUTES:
            plan["html"] = True
        elif path in MODEL_EXACT or path.startswith("tools/art/model-review/"):
            plan["model"] = True
        elif path in ATLAS_EXACT or any(path.startswith(p) for p in ATLAS_PREFIXES) or (
            path.startswith("media/showcase/art-reconstruction/2026-10-10/inputs-p")
            and path.endswith(".json")
        ):
            plan["atlas"] = True
        elif path in GALLERY_EXACT or path.startswith("assets/branding/") or any(
            path.startswith(p) for p in GALLERY_PREFIXES
        ) or (path.startswith("tools/contributor_gallery/") and
              path != "tools/contributor_gallery/publish_incremental.py"):
            plan["gallery"] = True
    plan["publish"] = any(plan[k] for k in ("atlas", "gallery", "model", "html"))
    return plan


def overlay_html(site: Path, paths: list[str]) -> list[str]:
    if not site.is_dir() or site.is_symlink():
        raise ValueError("Restored site must be a real directory")
    copied = []
    for path in paths:
        if path not in HTML_ROUTES:
            continue
        src = ROOT / path
        dest = site / HTML_ROUTES[path]
        if not src.is_file() or src.is_symlink() or not dest.is_file() or dest.is_symlink():
            raise ValueError(f"Missing or redirected contributor page: {path}")
        if dest.parent.is_symlink():
            raise ValueError(f"Redirected contributor route: {path}")
        shutil.copyfile(src, dest)
        copied.append(HTML_ROUTES[path])
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "overlay"))
    parser.add_argument("--changed", required=True, type=Path)
    parser.add_argument("--site", type=Path)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    paths = args.changed.read_text(encoding="utf-8").splitlines()
    if args.mode == "plan":
        flags = plan_changes(paths)
        print("Publication impact: " + ", ".join(k for k, v in flags.items() if v))
        if args.github_output:
            with args.github_output.open("a", encoding="utf-8") as handle:
                for key, enabled in flags.items():
                    handle.write(f"{key}={'true' if enabled else 'false'}\n")
    else:
        if args.site is None:
            parser.error("--site required for overlay")
        for path in overlay_html(args.site, paths):
            print(f"Reused existing published site; overlaid {path}")


if __name__ == "__main__":
    main()
