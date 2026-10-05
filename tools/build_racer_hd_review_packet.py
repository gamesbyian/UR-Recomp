#!/usr/bin/env python3
"""Build a compact human-review packet for the retained Racer HD pose strip."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

try:
    from tools.build_racer_hd_asset_dossier import encode_png_rgba
except ModuleNotFoundError:  # direct tools/... execution
    from build_racer_hd_asset_dossier import encode_png_rgba


def read_ppm(path: Path) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    if not data.startswith(b"P6\n"):
        raise ValueError(f"{path} is not a binary P6 PPM")
    header, payload = data.split(b"\n255\n", 1)
    lines = header.splitlines()
    if len(lines) < 2:
        raise ValueError(f"{path} has an incomplete PPM header")
    width, height = map(int, lines[1].split())
    expected = width * height * 3
    if len(payload) != expected:
        raise ValueError(
            f"{path} payload length {len(payload)} != expected {expected}"
        )
    return width, height, payload


def ppm_to_png(path: Path) -> tuple[bytes, list[int]]:
    width, height, rgb = read_ppm(path)
    rgba = bytearray()
    for i in range(0, len(rgb), 3):
        rgba.extend(rgb[i:i + 3])
        rgba.append(255)
    return encode_png_rgba(width, height, bytes(rgba)), [width, height]


def build_review_manifest(dossier: dict, equivalence: dict) -> dict:
    reps = {
        rep["representation_id"]: rep
        for rep in dossier.get("representations", [])
    }
    poses = []
    for pose in equivalence.get("pose_groups", []):
        source = pose.get("authored_source_representation_id")
        if source is None:
            candidate = None
            source_rep = reps[pose["representation_ids"][0]]
        else:
            source_rep = reps[source]
            candidate = source_rep["art_review"]["authored_candidate"]
        poses.append({
            "pose_id": pose["pose_id"],
            "player": pose["player"],
            "representation_ids": pose["representation_ids"],
            "semantic_frame_ids": pose["semantic_frame_ids"],
            "observed_frames": pose["observed_frames"],
            "stock_rgba_sha256": pose["stock_rgba_sha256"],
            "authored_asset_rgba_sha256": pose.get("authored_asset_rgba_sha256"),
            "authored_asset_conflict": pose.get("authored_asset_conflict", False),
            "needs_authored_asset": pose["needs_authored_asset"],
            "stock_png": source_rep["stock_evidence"]["png"],
            "nearest_4x_png": source_rep["stock_evidence"]["nearest_4x_png"],
            "authored_png": candidate["png"] if candidate else None,
            "approval_status": candidate.get("approval_status") if candidate else None,
            "shipping_approval_source": source_rep["art_review"].get(
                "shipping_approval_source"
            ),
            "gameplay_scale_review": (
                candidate.get("gameplay_scale_review") if candidate else None
            ),
        })
    worklist = equivalence.get("worklist", {})
    return {
        "schema_version": 1,
        "family": dossier.get("family"),
        "temporal_window": dossier.get("temporal_window"),
        "semantic_representation_count": equivalence.get(
            "semantic_representation_count", 0
        ),
        "unique_pose_count": equivalence.get("unique_stock_pose_count", 0),
        "authored_pose_count": worklist.get("authored_pose_count", 0),
        "unauthored_pose_count": worklist.get("unauthored_pose_count", 0),
        "authored_conflict_count": worklist.get(
            "conflicting_authored_pose_count", 0
        ),
        "poses": poses,
    }


def alpha_diff_svg(review: dict) -> str:
    stock_only = review.get("stock_only_pixels", [])
    candidate_only = review.get("candidate_only_pixels", [])
    cells = []
    for x, y in stock_only:
        cells.append(
            f'<rect x="{x}" y="{y}" width="1" height="1" class="stock-only"/>'
        )
    for x, y in candidate_only:
        cells.append(
            f'<rect x="{x}" y="{y}" width="1" height="1" class="candidate-only"/>'
        )
    return (
        '<svg class="alpha-diff" viewBox="0 0 64 64" '
        'xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">'
        '<rect width="64" height="64" class="diff-bg"/>'
        + ''.join(cells)
        + '</svg>'
    )


def render_html(manifest: dict, live: dict | None, readiness: dict | None = None) -> str:
    readiness_by_pose = {
        pose["pose_id"]: pose
        for pose in (readiness or {}).get("poses", [])
    }
    cards = []
    for pose in manifest["poses"]:
        review = pose["gameplay_scale_review"] or {}
        shipping = readiness_by_pose.get(pose["pose_id"], {})
        iou = review.get("alpha_iou")
        iou_text = "n/a" if iou is None else f"{iou:.4f}"
        frames = ", ".join(str(x) for x in pose["observed_frames"])
        reps = "<br>".join(html.escape(x) for x in pose["representation_ids"])
        authored = pose["authored_png"]
        authored_href = f"../{authored}" if authored else None
        stock_href = f"../{pose['stock_png']}"
        nearest_href = f"../{pose['nearest_4x_png']}"
        authored_panels = (
            f'<figure><img class="asset large" src="{html.escape(authored_href)}">'
            f'<figcaption>After · authored 4× inspection</figcaption></figure>'
            f'<figure><img class="asset gameplay" src="{html.escape(authored_href)}">'
            f'<figcaption>After · gameplay footprint</figcaption></figure>'
            if authored else
            '<figure class="missing">No authored asset</figure>'
        )
        baseline_authored = pose.get("baseline_authored_png")
        baseline_href = baseline_authored if baseline_authored else None
        baseline_panels = (
            f'<figure><img class="asset large" src="{html.escape(baseline_href)}">'
            f'<figcaption>Before · authored 4× inspection</figcaption></figure>'
            f'<figure><img class="asset gameplay" src="{html.escape(baseline_href)}">'
            f'<figcaption>Before · gameplay footprint</figcaption></figure>'
            if baseline_href else ""
        )
        shipping_status = shipping.get("review_status", "unreviewed")
        blockers = ", ".join(shipping.get("blocker_codes", [])) or "none"
        diff_svg = alpha_diff_svg(review)
        stock_only_count = review.get("stock_only_pixel_count", "n/a")
        candidate_only_count = review.get("candidate_only_pixel_count", "n/a")
        cards.append(f"""
<section class="pose">
  <h2>{html.escape(pose["pose_id"])} · {html.escape(pose["player"])}</h2>
  <div class="meta">
    frames: {html.escape(frames)} · alpha IoU: {iou_text}<br>
    shipping review: {html.escape(shipping_status)} · blockers: {html.escape(blockers)}<br>
    guards:<br>{reps}
  </div>
  <div class="panels">
    <figure><img class="asset stock" src="{html.escape(stock_href)}"><figcaption>Stock 1×</figcaption></figure>
    <figure><img class="asset large" src="{html.escape(nearest_href)}"><figcaption>Stock nearest 4×</figcaption></figure>
    {baseline_panels}
    {authored_panels}
    <figure>{diff_svg}<figcaption>Alpha mismatch · stock-only {stock_only_count} · authored-only {candidate_only_count}</figcaption></figure>
  </div>
</section>""")

    live_html = ""
    if live is not None:
        live_html = f"""
<section class="live">
  <h2>Live split-screen reference</h2>
  <p>Both captures are displayed at the same 256×224 CSS footprint. Open the HD image directly to inspect the native {live["hd_dimensions"][0]}×{live["hd_dimensions"][1]} pixels.</p>
  <div class="panels">
    <figure><a href="{html.escape(live["original_png"])}"><img class="frame" src="{html.escape(live["original_png"])}"></a><figcaption>Original</figcaption></figure>
    <figure><a href="{html.escape(live["hd_png"])}"><img class="frame" src="{html.escape(live["hd_png"])}"></a><figcaption>Remastered true-density</figcaption></figure>
  </div>
</section>"""

    shipping_summary = ""
    if readiness is not None:
        counts = readiness["counts"]
        shipping_summary = (
            f' · shipping ready: {str(readiness["shipping_ready"]).lower()}'
            f' · approved {counts["approved"]}/{readiness["unique_pose_count"]}'
            f' · needs refinement {counts["needs_refinement"]}'
            f' · changed since review {counts.get("changed_since_review", 0)}'
        )
    baseline_summary = ""
    if "baseline_comparison" in manifest:
        baseline = manifest["baseline_comparison"]
        baseline_summary = (
            f' · before/after changed {baseline["changed_authored_pose_count"]}'
            f'/{baseline["matched_pose_count"]} poses'
        )
    summary = (
        f'{manifest["semantic_representation_count"]} exact guards → '
        f'{manifest["unique_pose_count"]} unique poses · '
        f'{manifest["authored_pose_count"]} authored · '
        f'{manifest["unauthored_pose_count"]} unauthored · '
        f'{manifest["authored_conflict_count"]} authored conflicts'
        + shipping_summary
        + baseline_summary
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Racer HD review packet</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 24px; background: #111; color: #eee; }}
h1, h2 {{ margin-bottom: 8px; }}
.summary {{ padding: 12px; background: #222; border-radius: 8px; }}
.pose, .live {{ margin: 24px 0; padding: 16px; background: #1b1b1b; border-radius: 10px; }}
.meta {{ font-family: ui-monospace, monospace; font-size: 12px; color: #bbb; }}
.panels {{ display: flex; flex-wrap: wrap; gap: 16px; align-items: end; }}
figure {{ margin: 0; }}
figcaption {{ margin-top: 6px; color: #bbb; font-size: 12px; }}
.asset {{ background: repeating-conic-gradient(#333 0 25%, #222 0 50%) 50% / 12px 12px; }}
.stock {{ width: 64px; height: 64px; image-rendering: pixelated; }}
.large {{ width: 256px; height: 256px; image-rendering: auto; }}
.gameplay {{ width: 64px; height: 64px; image-rendering: auto; }}
.frame {{ width: 256px; height: 224px; object-fit: fill; image-rendering: auto; }}
.alpha-diff {{ width: 256px; height: 256px; border: 1px solid #555; }}
.diff-bg {{ fill: #202020; }}
.stock-only {{ fill: #ff5b5b; }}
.candidate-only {{ fill: #55d8ff; }}
.missing {{ width: 256px; height: 120px; display: grid; place-items: center; background: #311; }}
</style>
</head>
<body>
<h1>Racer HD review packet</h1>
<p class="summary">{html.escape(summary)}</p>
{live_html}
{''.join(cards)}
</body>
</html>
"""


def build_review_packet(
    dossier_path: Path,
    equivalence_path: Path,
    output_dir: Path,
    original_frame: Path | None = None,
    hd_frame: Path | None = None,
    readiness_path: Path | None = None,
    baseline_dossier_path: Path | None = None,
    baseline_equivalence_path: Path | None = None,
) -> dict:
    dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
    equivalence = json.loads(equivalence_path.read_text(encoding="utf-8"))
    readiness = (
        json.loads(readiness_path.read_text(encoding="utf-8"))
        if readiness_path is not None else None
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_review_manifest(dossier, equivalence)

    if (baseline_dossier_path is None) != (baseline_equivalence_path is None):
        raise ValueError("baseline dossier and equivalence must be supplied together")
    if baseline_dossier_path is not None and baseline_equivalence_path is not None:
        baseline_dossier = json.loads(
            baseline_dossier_path.read_text(encoding="utf-8")
        )
        baseline_equivalence = json.loads(
            baseline_equivalence_path.read_text(encoding="utf-8")
        )
        baseline_manifest = build_review_manifest(
            baseline_dossier, baseline_equivalence
        )
        baseline_by_pose = {
            pose["pose_id"]: pose for pose in baseline_manifest["poses"]
        }
        baseline_root = baseline_dossier_path.parent
        copied = 0
        changed = 0
        for pose in manifest["poses"]:
            before = baseline_by_pose.get(pose["pose_id"])
            if before is None:
                continue
            before_png = before.get("authored_png")
            if before_png:
                source = baseline_root / before_png
                target_name = f'{pose["pose_id"]}.png'
                target = output_dir / "baseline" / target_name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                pose["baseline_authored_png"] = f"baseline/{target_name}"
                copied += 1
            pose["baseline_authored_asset_rgba_sha256"] = before.get(
                "authored_asset_rgba_sha256"
            )
            pose["authored_asset_changed"] = (
                before.get("authored_asset_rgba_sha256")
                != pose.get("authored_asset_rgba_sha256")
            )
            if pose["authored_asset_changed"]:
                changed += 1
        manifest["baseline_comparison"] = {
            "pose_count": len(baseline_manifest["poses"]),
            "matched_pose_count": sum(
                pose["pose_id"] in baseline_by_pose for pose in manifest["poses"]
            ),
            "copied_authored_png_count": copied,
            "changed_authored_pose_count": changed,
        }

    if readiness is not None:
        readiness_by_pose = {
            pose["pose_id"]: pose for pose in readiness.get("poses", [])
        }
        for pose in manifest["poses"]:
            shipping = readiness_by_pose.get(pose["pose_id"], {})
            pose["shipping_review_status"] = shipping.get(
                "review_status", "unreviewed"
            )
            pose["shipping_art_approved"] = bool(
                shipping.get("shipping_art_approved", False)
            )
            pose["shipping_blocker_codes"] = list(
                shipping.get("blocker_codes", [])
            )
            pose["reviewed_authored_rgba_sha256"] = shipping.get(
                "reviewed_authored_rgba_sha256"
            )
        manifest["shipping_readiness"] = {
            "shipping_ready": readiness["shipping_ready"],
            "counts": readiness["counts"],
        }
    live = None
    if (original_frame is None) != (hd_frame is None):
        raise ValueError("original and HD live frames must be supplied together")
    if original_frame is not None and hd_frame is not None:
        original_png, original_dims = ppm_to_png(original_frame)
        hd_png, hd_dims = ppm_to_png(hd_frame)
        if original_dims != [256, 224]:
            raise ValueError(f"unexpected Original dimensions: {original_dims}")
        if hd_dims != [1024, 896]:
            raise ValueError(f"unexpected HD dimensions: {hd_dims}")
        (output_dir / "live-original.png").write_bytes(original_png)
        (output_dir / "live-hd.png").write_bytes(hd_png)
        live = {
            "original_png": "live-original.png",
            "hd_png": "live-hd.png",
            "original_dimensions": original_dims,
            "hd_dimensions": hd_dims,
        }
        manifest["live_reference"] = live

    (output_dir / "review-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "index.html").write_text(
        render_html(manifest, live, readiness),
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dossier", type=Path)
    parser.add_argument("equivalence", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--original-frame", type=Path)
    parser.add_argument("--hd-frame", type=Path)
    parser.add_argument("--readiness", type=Path)
    parser.add_argument("--baseline-dossier", type=Path)
    parser.add_argument("--baseline-equivalence", type=Path)
    args = parser.parse_args()
    manifest = build_review_packet(
        args.dossier,
        args.equivalence,
        args.output_dir,
        args.original_frame,
        args.hd_frame,
        args.readiness,
        args.baseline_dossier,
        args.baseline_equivalence,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
