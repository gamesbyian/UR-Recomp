## No-PC original print figure artifact through GitHub Actions

If a local computer cannot run the PDF renderer, use the opt-in Actions
workflow **ART-4K authenticated original manual crop review (on demand)**,
`.github/workflows/art4k-original-manual-crops.yml`.
It also runs only on PRs modifying that workflow or its specific original
manual extractor/validator/tests. It is **not scheduled**; it does not
run for unrelated 3D, game, Android or CI work. From GitHub Actions,
select that workflow and **Run workflow** on `main`.

The workflow uses one Ubuntu runner, Python 3.12, pinned
`PyMuPDF 1.26.4` and `Pillow 11.3.0`, original repo-tracked
`Uniracers-USA-manual.pdf` and both focused synthetic-PDF unit suites.
It renders four source crops, then **re-authenticates the exact tracked
Git PDF blob and rerenders/compares every cropped RGB pixel** using the
independent sparse-landmark validator before offering any output.
The resulting downloadable seven-day GitHub Actions artifact
`art4k-original-1994-manual-four-views` contains exactly four PNGs,
`source-crops.json` with each real SHA-256 and PDF/page coordinates, and
`landmarks.UNANNOTATED.json`. It contains no original ROM, GLB candidate,
private credentials or approved art asset. The original scanned artwork
is not committed to a new source path.

Download/extract that ZIP to the phone, open the existing Pages 3D
viewer and its **Mark original printed 2D landmarks locally** link.
Select the four PNGs plus source-crops.json in one Android file-picker
operation. The browser checks local PNG hashes and records actual point
coordinates/occlusion. The separate offline Python source audit (#3170)
remains mandatory before claiming *measured* original print landmarks.
The workflow's generated PNG hashes are renderer-version-specific;
if running locally against them, use the pinned renderer environment
for exact RGB replay. Never mistake the original print figures for
verified lost 1994 3D model/camera data or owner-approved game art.

---

# Original manual 3D-reference crops with authentic PDF provenance

Research only. The original 1994 USA printed manual is already in the
repository at reference/imported/manuals/Uniracers-USA-manual.pdf, exactly
6,006,270 bytes, tracked Git blob SHA-1
a52da4f94a75e3e76fd61a759cb8e0c3a4fbc5d3.
This is not a historical 3D model, source-game camera, rig or part map.

To create the next physical-model source-image review set locally, use
optional PyMuPDF and Pillow:

    python3 tools/art/extract_manual_3d_reference_views.py \
      --pdf reference/imported/manuals/Uniracers-USA-manual.pdf \
      --out-dir /private/review/ur-manual-original-3d-20261105

The script validates the source bytes as this EXACT Git blob, computes
the independent PDF SHA-256, rejects wrong pagination, renders only the
predeclared figures at 144 DPI and writes an atomic, no-overwrite private
directory of four cropped PNGs and a source-crops.json receipt. No image
is copied to Git. Crop pixel boxes, full-page dimensions and exact PNG
SHA-256 are recorded for reproducibility. Reference boxes were manually
selected as generous regions in a 1024x1497 full-page visual inspection;
they are NOT authenticated 3D silhouette boundaries.

The exact crop set: p14 cyan near-front fork/crown, p14 red oblique lean,
p15 large underside wheel/hub/crank and p16 red saddle/neck/side view.
The p14 images contain track ribbons that occlude actual geometry; the p15
original print partly cuts the right pedal. Do not invent landmarks
behind an occlusion. Published official manual is original 1994 2D
printed art; its 3D production relationship to original ROM-rendered
characters and source camera are unknown.

The generated landmarks.UNANNOTATED.json is intentionally INVALID as
measured source data. A reviewer must visibly annotate actual wheel,
saddle, fork, crown, axle and/or pedal landmarks, explain absent ones and
identify themselves before the existing measure_unicycle_reference.py
can accept the resulting projected-landmark report. We extend its
known source kinds with official-manual, and use square scan pixels,
NEVER SNES 7:6 pixel aspect for a printed page. Page/crop SHA plus scan
perspective notes must accompany every observation.

No physical 1994 width/radius, independent original 3D holdout, art
approval, game graphics, new model or Windows release gate follows
automatically. Review against the one existing unapproved five-parent/
16-material 2026 GLB and its original-Mesen reference rail.
