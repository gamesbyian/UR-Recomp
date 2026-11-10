#!/usr/bin/env python3
"""Plan bounded Pages publication from changes since the last successful site artifact.

A styling-only contributor update overlays its HTML into the previously published
site. No atlas, gallery raster previews, GLBs or measurements are regenerated.
"""
from __future__ import annotations

import argparse
import json
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
    "analysis/data/racer-original-index-lookup-20261102.json",
    "tools/art/build_racer_source_pixel_corpus.py",
    "tools/art/racer_source_pixels.py",
}
ATLAS_EXACT = {
    "analysis/windows-visual-atlas.json",
    "tools/windows_visual_atlas.py",
    "tools/windows_visual_atlas_intake.py",
}
MODEL_PAGES = {
    "tools/art/model-review/index.html": "model-review/index.html",
    "tools/art/model-review/visual-review.html": "model-review/visual-review.html",
    "tools/art/model-review/manual-landmarks.html": "model-review/manual-landmarks.html",
}
GALLERY_EXACT = {
    "assets/promo/canonical/blueprint-16x9-logo-left.png",
    "assets/promo/canonical/blueprint-4x3-logo-left.png",
    "assets/branding/uniracers-box-wordmark-traced.svg",
    "assets/branding/unirally-box-wordmark-traced.svg",
    "assets/branding/uniracers-japanese-katakana-wordmark.svg",
    "assets/branding/unirally-russian-cyrillic-wordmark.svg",
    "assets/branding/unirally-french-wordmark.svg",
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
    plan = {"atlas": False, "gallery": False, "model": False, "html": False, "model_page": False, "publish": False}
    for path in paths:
        path = path.strip()
        if not path:
            continue
        if path in HTML_ROUTES:
            plan["html"] = True
        elif path in MODEL_PAGES or (path.startswith("tools/art/model-review/") and path.endswith(".mjs")):
            plan["model_page"] = True
        elif path in MODEL_EXACT or path.startswith("tools/art/model-review/"):
            plan["model"] = True
        elif path in ATLAS_EXACT or any(path.startswith(p) for p in ATLAS_PREFIXES) or (
            path.startswith("media/showcase/art-reconstruction/2026-10-10/inputs-p")
            and path.endswith(".json")
        ):
            plan["atlas"] = True
        elif path in GALLERY_EXACT or any(path.startswith(p) for p in GALLERY_PREFIXES) or (
            path in {"tools/contributor_gallery/stage.py", "tools/contributor_gallery/png_preview.py"}
            or path.startswith("tools/contributor_gallery/source/")
        ):
            plan["gallery"] = True
    plan["publish"] = any(plan[k] for k in ("atlas", "gallery", "model", "html", "model_page"))
    return plan


def overlay_html(site: Path, paths: list[str]) -> list[str]:
    if not site.is_dir() or site.is_symlink():
        raise ValueError("Restored site must be a real directory")
    copied = []
    for path in paths:
        relative = HTML_ROUTES.get(path) or MODEL_PAGES.get(path)
        if relative is None and path.startswith("tools/art/model-review/") and path.endswith(".mjs"):
            relative = "model-review/" + Path(path).name
        if relative is None:
            continue
        src = ROOT / path
        dest = site / relative
        if not src.is_file() or src.is_symlink() or not dest.is_file() or dest.is_symlink():
            raise ValueError(f"Missing or redirected contributor page: {path}")
        if dest.parent.is_symlink():
            raise ValueError(f"Redirected contributor route: {path}")
        shutil.copyfile(src, dest)
        copied.append(relative)
    return copied


def prepare_model_placeholder(site: Path, backup: Path) -> None:
    """Preserve independently authenticated source artwork when replacing GLBs.

    The 3D stager only replaces a model-free placeholder. Convert an existing
    previously published GLB page into that placeholder, carrying over its
    original-source rails and comparison assets for the stager to revalidate.
    """
    target = site / "model-review"
    if not target.is_dir() or target.is_symlink():
        raise ValueError("Expected previous model-review directory")
    manifest = target / "manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise ValueError("Missing previous model manifest")
    prior = json.loads(manifest.read_text(encoding="utf-8"))
    if prior.get("model_url") is None:
        return  # Already a model-free atlas placeholder.
    if prior.get("schema") != "ur-racer-model-review/1":
        raise ValueError("Unknown prior model provenance")
    if backup.exists() or backup.is_symlink():
        raise ValueError("Model backup destination already exists")
    target.rename(backup)
    target.mkdir()
    shutil.copy2(ROOT / "tools/art/model-review/index.html", target / "index.html")
    (target / "manifest.json").write_text(
        json.dumps({"schema": "ur-racer-model-review/1", "model_url": None}) + "\n",
        encoding="utf-8",
    )
    for name in ("original-mesen24", "sprites", "sprites.json",
                 "visual-review-assets.json", "legacy-art"):
        source = backup / name
        if not source.exists():
            continue
        if source.is_symlink():
            raise ValueError(f"Redirected prior model reference: {name}")
        if source.is_dir():
            shutil.copytree(source, target / name, symlinks=False)
        else:
            shutil.copy2(source, target / name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "overlay", "model-placeholder"))
    parser.add_argument("--changed", required=True, type=Path)
    parser.add_argument("--site", type=Path)
    parser.add_argument("--model-backup", type=Path)
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
    elif args.mode == "overlay":
        if args.site is None:
            parser.error("--site required for overlay")
        for path in overlay_html(args.site, paths):
            print(f"Reused existing published site; overlaid {path}")
    else:
        if args.site is None or args.model_backup is None:
            parser.error("--site and --model-backup required for model-placeholder")
        prepare_model_placeholder(args.site, args.model_backup)


if __name__ == "__main__":
    main()
