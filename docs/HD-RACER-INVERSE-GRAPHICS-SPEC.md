# Source-registered inverse graphics for the Uniracers racers

**Status (2026-10-31): approved research direction and executable planning contract; no newly calibrated source-authentic 3D model, animation rig or shipping artwork is claimed.** This is the technical annex to [HD-RACER-CHARACTER-RECONSTRUCTION.md](HD-RACER-CHARACTER-RECONSTRUCTION.md). That document owns the target likeness and the owner's visual veto; [HD-ART-DIRECTION.md](HD-ART-DIRECTION.md) owns art direction, [HD-RACER-PROJECTED-LANDMARKS.md](HD-RACER-PROJECTED-LANDMARKS.md) owns projected 2D evidence, [WORK-QUEUE.md](WORK-QUEUE.md) alone owns active dispatch and [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json) alone owns release acceptance. Execution sequence: [HD-RACER-INVERSE-GRAPHICS-PLAN.md](HD-RACER-INVERSE-GRAPHICS-PLAN.md).

## 0. Goal, non-goals, evidence standard

Recover **one source-consistent, parametrically editable, animatable 3D character** that explains the widest independently authenticated original raster/period-render reference set; use that model to generate candidate high-density racer art with correct source pose, composition, motion and character personality. Exact recovery of a vanished source polygon mesh is mathematically underdetermined. Distinguish (a) observed 2D pixels, (b) independently supported camera/pose assumptions, (c) geometry inferred under constraints, and (d) generative proposals.

Do **not** replace the working original 1x path, invent independent poses frame by frame, alter guest simulation/contact/collision, introduce a second HD selector or runtime renderer, treat a poster illustration as a source-authenticated 3D turnaround, run every speculative neural tool, or assert that a visually convincing candidate is original-source geometry. The objective is a coherent, original-faithful reconstruction useful to the shipping racer art pipeline, not a generic photogrammetry showcase.

Use actual source-registered 32/64px and normal 1P/2P display evaluation, plus high-detail title/press evidence where provenance is independently established. Preserve identity and all original fixed pixel anchors; do not use source OAM alpha as a substitute for final screen visibility or confuse last visible alpha Y with ground contact.

## 1. Current repo inventory and reuse map (inspected 2026-10-31)

### Already present on main: exact extraction and reference evidence

| Asset/tool | What it actually establishes | Planned reuse |
| --- | --- | --- |
| tools/extract_racer_presentation_family.py; analysis/generated/racer-presentation-family.json | ROM-grounded frame ID, packed composition data, OBJ graphic/palette round trips | Canonical original raster extraction path, no new ROM parser |
| tools/prototype_racer_hd_replacement.py; analysis/data/racer-hd-replacement-prototype.json | Original 64x64 stock composition, semantic frame/pose mappings and 1205–1220 P1/P2 reviewed motion window | Sampling/candidate-family selection; exact semantic IDs |
| tools/build_racer_pose_equivalence.py; tools/build_racer_hd_asset_dossier.py | Byte-identical pose deduplication, original/HD/contact-neighbor dossier | Train/holdout grouping and comparison output, not replacement |
| tools/export_native_racer_obj_source_reference.py; docs/QA08-ORIGINAL-OBJ-SOURCE-REFERENCE-EXPORT-20261010.md | Hash-bound authentic native PPU OBJ source layers and alpha rows, not final PPU composition | Provenance-strict source silhouettes |
| tools/art/build_qa08_original_contact_sheet.py; docs/QA08-ORIGINAL-RACER-TITLE-REFERENCE-SHEET-20261013.md | Verified AOT original title frame400 and frame2208 isolated OBJ slots 96–99 | Distinct title/gameplay reference comparison, title fade limitation |
| tools/art/build_qa08_original_multipose_atlas.py; docs/QA08-ORIGINAL-2P-MULTIPOSE-SOURCE-ATLAS-20261013.md | Genuine 2P slot 96–99 samples at 1872, 1888, 2208, backed by native evidence | Source pose families, no invented geometry |
| analysis/data/qa08-original-2p-four-pose-source-alpha-through2208.json; analysis/data/qa08-original-2p-racer-palette-four-poses-through2208.json | Frame1856/1872/1888/2208 original 2P source-alpha/color invariants | Real source-space sanity checks and variant/occlusion constraints |
| tools/art/measure_unicycle_reference.py; tools/art/audit_unicycle_pose_sequence.py; tests/unit/test_measure_unicycle_reference.py; tests/unit/test_audit_unicycle_pose_sequence.py | SHA-bound human landmarks, perspective/pixel-aspect tags and projected temporal variation; explicitly **not** recovered 3D | Extend, never bypass, for calibration dataset |
| tools/check_racer_hd_temporal_coherence.py; tools/check_racer_hd_pixel_confinement.py; tools/check_racer_hd_foreground_occlusion.py | Motion cadence, stable/static states, bounded pixels and foreground acceptance checks | Existing downstream regression gates |
| native/presentation/racer_hd_presenter.hpp/.cpp; racer_replacement_selector.cpp/.hpp; racer_oam_placement.cpp/.hpp | Current native 4x procedural baseline, guarded asset selection, placement, alpha/foreground | Comparison control and future offline-generated raster integration; do not mutate now |
| analysis/data/racer-hd-art-approval*.json | Historic narrower technical hash approvals before explicit owner likeness veto | Immutable historical test controls only |
| media/showcase/art-reconstruction/2026-10-10/ (stock/, authored/, image sheets, MP4, manifests, SHA256SUMS) | Historical original-vs-procedural visual baseline with per-frame provenance; its README's former art-approval language predates owner visual veto | Review baseline, never present as finished art |
| reference/imported/manuals/Uniracers-USA-manual.pdf; reference/imported/press/dma-design/uniracers_01.pdf; reference/catalog.yml | Retained manual and period press source(s); DMA archive had only the previously imported relevant PDF | Original-design research with rights/perspective notes; no duplicate archive scrape |
| docs/HD-RACER-PERIOD-PR-ART-SOURCES-20261014.md; docs/HD-RACER-CHARACTER-RECONSTRUCTION.md | Evidence provenance, art identity, approved/rejected distinctions | Source authority and artistic rubric |

Important observed facts: the title reference guest400 is **inside a dark fade**, so its brightness-adjusted display is an *inspection aid*, never a true source-colour sample. The original 2P OAM upper slot98/99 at frame2208 has 317/313 original source pixels, and narrow countdown projections visibly change to wider post-GO projections. The 7:6 SNES pixel-aspect distinction must be carried through every comparison. Source OBJ visibility and completed-composite pixel ownership are separately tested in QA-08. The repeated source raster is not an independent viewpoint. See the named source docs for exact AOT run IDs, SHA-256 and limits.

### Existing 3D work: **do not duplicate**

**Draft PR [#2832](https://github.com/gamesbyian/UR-Recomp/pull/2832)**, work ID UR-ART-4K-20261026, is the primary integration target. Its open head on 2026-10-31 is graphics/art4k-part-addressable-rig-20261029. The candidate OpenSCAD shared model was recovered from **closed, unmerged PR [#1826](https://github.com/gamesbyian/UR-Recomp/pull/1826)**, not an independently sourced original rig.

Draft-only files include:
- tools/art/candidates/unicycle_shared_rig.scad, with one parametric blockout and named upright, pedal, wheelie, stunt, bank poses (and exploratory continuous ride/stunt-cycle study in source).
- tools/art/export_articulated_unicycle.py and tools/art/candidates/ARTICULATED-BLOCKOUT.md.
- tools/art/scad_materials.py and tools/art/glb_roundtrip_guard.py; focused tests test_export_articulated_unicycle.py, test_scad_csg_guard.py, test_scad_materials.py and test_art4k_glb_*.

The exporter emits **five addressable parent parts** (tire, rim_and_hub, fork_and_frame, pedals, saddle) and, per draft read, **16 coloured child material meshes**, source-derived saddle/hub pivots, source-hash-bound immutable GLB+receipt, atomic current-success pointer and distinct last-attempt status. It has five named source-*blockout* pose transforms and optional exploratory phase/lean controls. PR evidence reports finite watertight geometry and part/normal/accessor integrity. **It is an articulated assembly/procedural blockout, not a verified skeletal animation rig, 1994 mesh, calibrated camera or source-matched animation.** Its broad and character-likeness/owner gates remain unpassed. Do not merge it as shipping art; modify and review this same candidate branch (or explicitly coordinate a successor) when the implementation work begins. Read live PR/head on every handoff because it is actively changing.

**Closed PR #1826 also explored locked-camera five-pose and continuous motion previews.** Its preview code is historical branch work; test whether each useful part was carried into #2832 before resurrecting it. [PR #1840](https://github.com/gamesbyian/UR-Recomp/pull/1840) addressed readable normal-size comparison previews. Never start a separate OpenSCAD rig, image atlas or approval format merely because an old branch was closed.

## 2. Data model: one evidence-backed corpus, no unlicensed duplication

Build a local **review corpus manifest** (proposal schema UR-RACER-INVERSE-CORPUS/1; document and test before implementation). Store machine-readable metadata and hashes under analysis/art/inverse/ or tools/art/fixtures; keep non-redistributable original pixels in local ignored directories and approved external artifacts. Avoid assuming a referenced historical Actions artifact is still downloadable; missing evidence is a fail-closed intake event, not a license to substitute thumbnails.

Each input record must carry: unique stable ID; kind (original-ROM-composed, original-PPU-OBJ-source, original-PPU-final, original-title, official-period-art, current-2026-blockout, synthetic-unit); original source URI/ROM hash and rights/region; producer commit/workflow run/artifact and per-image SHA-256; true raw pixel dimensions, channel/alpha semantics, crop and resample history; 7:6 vs square-pixel aspect; semantic racer/player/palette/frame/guard identity; exact viewport/OAM slot and layer visibility class; camera class (orthographic/perspective/unknown) with evidence/confidence; pose family, canonical temporal phase and explicit ambiguity; landmarks with occlusion/uncertainty; train/validation/test role; source-image equivalence family. Frame keys and crop/transform/pixel hash are separate fields, never overwritten.

Use lossless exact ROM raster and hard alpha as truth for tiny sprites. **Do not feed AI super-resolution outputs back as observed pixels**; upscale only for visual inspection or separately tagged proposed priors. Extraction must reproduce original source SHA and exact composed 64x64 where available; do not recolour source before proving equivalence. Semantic OAM slots may contain pieces/layers rather than full visible characters. Preserve final PPU and stage order separately.

Reference hierarchy by question:
1. Original high-detail *authentic title/menu* for 3D identity if not faded/occluded; original official packaging/press with provenance and perspective caveats for corroboration.
2. Original exact composite sprites and registered family/neighbor source for frame timing, placement and silhouette.
3. Original native isolated OBJ layers for source alpha/palette and otherwise-occluded pieces.
4. Blockout/2026 renders as **candidate-only** controls.
Never label packaging illustrations as authenticated renderings of the DMA source model. The 2010 developer interview documents original pre-rendering and animation complexity but does not supply the lost mesh.

### Split rules (anti-leakage)

Deduplicate original RGBA SHA, exact semantic pose equivalence and verified palette variants *before* partitioning. Keep all identical/mirrored/registered-alias poses and all near-neighbor frames from one short temporal window in the same partition unless the explicit test is interpolation within a sequence. Predeclare one held-out **distinct pose family** and, if genuine new view evidence exists, one held-out independent viewpoint. No view/generalization score if there is no independent viewpoint. Do not train on the same high-detail picture via a differently cropped regional cover and claim held-out generalization. Log the equivalence grouping algorithm and hashes.

## 3. Geometry, kinematics and camera parameterization

### Primary prior: existing OpenSCAD/GLB candidate from #2832

Normalize units by **wheel outside radius = 1.0** for *inference only*, with the parent assembly source origin and physical/native game contact separately tracked. Expose bounded, meaningful parameters: tire outer/inner shape, sidewall and tread profile; rim/axle/hub radius and thickness; fork offsets, attachment points, crown width, tubing/fork shape and mass; saddle contour/sweep/cup, width, height, nose/tail, mounting and optional non-rigid shape controls; crank length, pedal placement/platform size; mutually consistent mirrored components. The existing 2026 SCAD constants and experimental saddle_span/frame_mass are starting values, **not** canonical ratios.

Keep the same assembly identities and source-derived joints. Separate geometry parameters from per-pose transforms and from camera parameters. Mechanical invariants: coaxial wheel/tire/hub; closed round wheel under rotation; fork/hub connection; fixed crank length and opposite crank phase; pedal-platform level rules as actually required by source; no self-intersections or broken parent hierarchy. Rigid parts should transform rigidly; saddle/head expressivity can use constrained deformation. Do not build a guessed steering joint without source pose evidence. Distinguish forward wheel rotation linked to travel, game sprite pedal animation cadence and arbitrary remaster animation; source wins when they differ.

GLB is a **portable interchange/export**, not assumed to carry full editable parametric semantics or original keyed animation. Preserve a versioned source parameter manifest, deformation functions, pivot hierarchy and source transforms. If Blender's scripting and shape keys become materially more expressive than SCAD for the saddle/cross-pose fitting, add a *single* deterministic Blender offline authoring/export path importing/refitting the existing candidate, with one canonical source-of-truth parameter file; no second hand-maintained rig. Keep #2832's artifact receipts and integrity checks.

### Camera fitting

For each **genuinely independent** source view, fit orthographic or weak-perspective projection first, with original aspect ratio and known crop/registration. Only introduce perspective if independent high-detail evidence requires it. Treat viewpoint, world tilt, scale, camera translation and object deformation as partly confounded; require multi-view corroboration rather than treating a 2D spin as a 360-degree yaw. Never use COLMAP/SfM camera output as ground truth without independent feature/camera tests.

Fit an image-to-model transform for each explicit source group without mutating original guest placement/anchor. Distinguish apparent wheel ellipse due to yaw, wheel distortion due to pixel aspect, saddle deformation, and view-dependent sprite shading.

### Motion mapping

Map original frame IDs/pose equivalence classes to **per-pose model parameters**: shared model transform/tilt, wheel/crank angle, saddle lean and deformation, stretch/bounce and camera/view. Map as an *offline export function* of source-derived semantic identity and timestamp, not an independent runtime animation clock. Record unobservable and multiply plausible parameters. First test ride/pedal, wheelie/bank, full stunt/flip/recovery and stable/static alias edges. Exact frame cadence and source anchor/viewport handling are owned by the existing replacement registry/presenter.

## 4. Inverse-rendering optimizer and alternatives

### Stage 1: CPU deterministic reference baseline

Use source masks/landmarks to calibrate camera and geometry on a modest **parameter vector**, not free mesh vertices. Implement a reproducible forward renderer (existing OpenSCAD scene for shape/export plus Blender background or other tested offscreen render for camera, silhouette, surface and material). Initially optimize 2D silhouettes with chamfer/contour distance, landmark robust error and geometry priors. Use multi-start bounded derivative-free/scalar optimizers where parameter gradients are unavailable; cache geometry and repeated pose/material renders by source hash/parameter digest. Estimate time/cost only from measured first actual trial.

### Stage 2: optimize pose and appearance without cheating

Add silhouette IoU (report alongside loss, do not blindly optimize IoU as a differentiable scalar), signed-distance/contour loss, uncertain/visible landmarks, palette-family correspondence, occlusion-aware RGB loss and temporal smoothness/held-static constraints. Separate camera/shape/pose/material parameter blocks; alternate updates to avoid explaining an incorrect fork shape with a per-frame zoom or an incorrect wheel size with free camera scale. Test constant-camera and variable-camera hypotheses as distinct declared models; penalize unnecessary per-pose degrees of freedom. Only use original 2D visual evidence in its declared ownership layer. For 1994 lighting inferred from palette ramps, account for baked 16-bit quantization and uncertain normals; do not fit HDR PBR roughness to a fifteen-colour sprite as though it were calibrated reflectance.

Proposed objective, each term normalized and reported independently (weights calibrated on synthetic fixtures, not invented acceptance thresholds):

L = w_mask L_contour + w_landmark L_landmark + w_palette L_palette + w_motion L_temporal + w_prior L_kinematic + w_complexity L_model_complexity.

Quantify uncertainty with parameter bounds/alternative candidates, at least two initialization seeds, and sensitivity/ablation of disputed evidence. If different valid models fit equally well, label the geometry underdetermined.

### Stage 3: optional differentiable/GPU refinement

If the stage-1/2 ceiling is demonstrated, use PyTorch3D mesh-renderer or nvdiffrast to optimize *low-dimensional parameters* or carefully regularized mesh offsets. nvdiffrast is CUDA-oriented and lower-level; requires an appropriate NVIDIA GPU and review of its NVIDIA license. PyTorch3D has a differentiable mesh renderer and also has version/toolchain complexity. Do not place either on default Windows, HP CPU or per-PR CI paths. Any proposal for hosted GPU time must record tested environment, license, available VRAM, measured marginal gain and explicit cost.

### Stage 4: optional generative competitors

Evaluate **one** representative modern multi-image/image-to-3D model only if it accepts appropriately tagged independent views and produces a usable mesh, and after baseline pose fitting. Candidates as of October 2026 include TRELLIS.2 (Microsoft MIT source, GPU-heavy; dependencies have distinct licenses), Hunyuan3D-2.1 (strong image/texture output, model licensing and high VRAM requirements), LARM (SIGGRAPH Asia 2025 articulated sparse-view research, verify released code/weights/license), or a capped paid provider. The listed models are **candidates, not validated solutions for 1994 raster art**. Do not assume one image-to-3D result has correct articulation, source cadence or camera.

Run every candidate on identical source-input sets and holdouts, normalize orientation and scale, fit/retarget it to the *existing* five-part assembly and kinematic checks. If a mesh improves appearance but loses independent wheels/pedals/saddle or fails unseen poses, treat it only as a geometry proposal. No automatic invented PBR grunge/texture maps. Novel backside details must be explicitly tagged inferred/unobserved. No high-cost GPU workflows or external uploads of ROM-derived/rights-restricted imagery without separate authorization and provider/terms review.

## 5. Output contracts

Offline candidate bundle (local artifacts first, not wholesale committed copyrighted images):
- model source parameter/pose manifest, canonical source commit and 3D generator versions;
- complete GLB with named subassemblies and verified transforms, pivots, normals/materials, plus source-to-export digest, optional editable Blender file only when justified;
- source data manifest with input image SHA, origin, rights and equivalence/holdout grouping;
- per-view actual raw output masks/RGB at source/32/64px, 4x and independent title-scale, registered with identical camera/crop contracts;
- side and three-quarter canonical rotations, full pedal turn, expressive/stunt loop, frame-by-frame original/procedural-blockout/new-candidate comparison sheets and playable clip;
- machine-readable per-view mask IoU, boundary error, landmark residual, alpha-contact error, palette agreement, static-pose consistency, temporal motion error and holdout breakdown;
- fixed benchmark environment, seeds, parameter set, optimization log, CPU/GPU/time/memory cost and model-selection reason;
- immutable receipt with explicit **false** acceptance/likeness/shipping claims until independently reviewed.

Use existing dossier, motion checker, original stock variants and 1P/2P original fallback, with the existing native replacement surface once approved. No new runtime 3D rendering subsystem in this phase.

## 6. Acceptance and adversarial tests

**Synthetic-contract tests:** generate a known multi-part unicycle under two controlled cameras, hide one view, fit the model and verify reprojection and parameter recovery within pre-registered scale/tolerance. Test uncertainty when only one view exists. Reject malformed source hash, changed crop/PAR, identical raster masquerading as second view, mixed pose/camera interpolation, incorrect part winding/normal/units, absent original alpha, bad GLB pivots, stale success pointers and bad parentage. The existing #2832 integrity suite is required, not replaced.

**Authentic-source tests:** independently verified unchanged original source alpha, original and source-render registration and 7:6; holdout score on genuinely unseen pose families; wheel roundness/mechanical constraints; absence of new-frame motion for stock-static identity; consistent shared red/green geometry, only verified palette shifts; real 32px and 64px readable previews, split-screen, normal 4x, 4:3 and true 16:9. Respect final OAM/PPU occlusion, foreground segmentation and guest contact separately. A credible candidate may still fail likeness.

**Non-regression:** no changes to gameplay/state, native original renderer, source animation timing or windows package during offline exploration. At integration, run existing HD exact-pose/hash guards, original fallback, QA-08 visibility, motion, 1P/2P, representative native Windows and CI policy; preserve old historical approvals as historical records.

**Art admission gate:** independent owner review of a source-attributed multi-view turnaround, static original/title comparison and uninterrupted expressive pose loop in real gameplay size. Owner specifically approves character identity, not merely technical correctness. Until then: ART-4K candidate only, no ART-02..ART-10 or shipping credit and no bypass of the explicit 2026-10-10 likeness veto.

## 7. Tooling and research disposition (checked 2026-10-31)

| Tool/process | Decision | Evidence |
| --- | --- | --- |
| Existing OpenSCAD + trimesh #2832 | **Primary seed asset.** Start by measuring, refitting and preserving stable export, not remaking | https://github.com/gamesbyian/UR-Recomp/pull/2832 |
| Blender headless Python + glTF | Candidate offline camera/material/render/interchange workbench if measured necessity; deterministic source/export | https://docs.blender.org/api/current/bpy.ops.export_scene.html |
| scipy.optimize / constrained parameter search | Prefer first for small parameter vector, CPU-accessible | https://docs.scipy.org/doc/scipy/reference/optimize.html |
| COLMAP / OpenMVS | Not first-line: SIFT/pinhole assumptions and low-texture animated pixels may fail; only controlled match diagnostics | https://colmap.github.io/ |
| PyTorch3D | Optional differentiable mesh reprojection, GPU/toolchain gate | https://github.com/facebookresearch/pytorch3d |
| NVIDIA nvdiffrast | Optional high-performance differentiable rasterizer, CUDA + separate license | https://nvlabs.github.io/nvdiffrast/ |
| TRELLIS.2 | Optional proposal generator; MIT code, GPU and dependencies/weights require review | https://github.com/microsoft/TRELLIS.2 |
| Tencent Hunyuan3D-2.1 | Optional image-to-3D/texture competitor, not assumed source-faithful; high VRAM + license | https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1 |
| LARM | Articulated sparse-view research lead, applicability/release readiness unproven on sprites | https://sylviayuan-sy.github.io/larm-site/ |
| Classical silhouette/visual-hull carving | Constrains occupied volume **only** with actual independent calibrated views of substantially identical rigid shape; not an animation sequence with unknown camera | multi-view geometry |

**Avoid:** blanket super-resolution as pseudo-ground-truth; SAM for already known hardware-derived alpha; generic one-shot NeRF/3DGS on changing animated sprites; Marching Cubes directly over Gaussian centres (Gaussians are not intrinsically an isosurface); indiscriminate automatic skeletal rigging for mechanically known pivots; texture hallucination presented as original.

Research outcomes are hypotheses until executed on the repository's true references. Document experimental failures and use smallest discriminating tests rather than an endless succession of AI models.

## 8. Operational constraints

- Work within the **single existing ART-4K lane/PR #2832** or a clearly coordinated successor after confirming live ownership. Do not collide with five hourly agents or overwrite actively modified branch files.
- Preserve source licenses, royalty/copyright notes, input-only uploads restrictions; small synthetic fixtures and metadata are okay in the public repo. User acceptance of research-discoverability risk does not confer publication rights.
- Heavy rendering/parameter search can run on the HP unattended non-LLM compute scheduler, but schedule opportunistically around existing jobs, use bounded work packets with resumable immutable checkpoints, log CPU/memory/time, no unapproved GPU provisioning or paid service. Keep routine GH Actions CI to tiny CPU synthetic checks, opt-in expensive evaluation only after a material result.
- Promote no image/asset/score without exact commit/source-image and run hashes. On interruption, previous successful receipt remains usable but must not be mistaken for newest run, per #2832's last-attempt/current-success pattern.
