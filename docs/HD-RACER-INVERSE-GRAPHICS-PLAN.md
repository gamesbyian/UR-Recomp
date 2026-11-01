# HD racer inverse-graphics: executable delivery plan

**Status (2026-10-31): planned, not executed or accepted.** Governing technical contract: [HD-RACER-INVERSE-GRAPHICS-SPEC.md](HD-RACER-INVERSE-GRAPHICS-SPEC.md). Likeness authority: [HD-RACER-CHARACTER-RECONSTRUCTION.md](HD-RACER-CHARACTER-RECONSTRUCTION.md). Source measurements: [HD-RACER-PROJECTED-LANDMARKS.md](HD-RACER-PROJECTED-LANDMARKS.md). Live priority/owner assignment: [WORK-QUEUE.md](WORK-QUEUE.md), [HOURLY-AGENT-LINES.md](HOURLY-AGENT-LINES.md). **Do not** turn this file into a competing work queue or independently dispatch heavyweight CI.

## Decision and shortest valuable path

**Primary path: extend/qualify draft PR [#2832](https://github.com/gamesbyian/UR-Recomp/pull/2832), not a greenfield reconstruction.** That PR already has a single procedural OpenSCAD model, material-separated five-part GLB export, five exploratory poses, SHA-bound immutable receipts and focused tests. The original likeness and actual source-registered motion remain unvalidated. Its model is a useful *seed*, not approved character art. Closed [#1826](https://github.com/gamesbyian/UR-Recomp/pull/1826) had a five-pose and continuous render study that may be recovered selectively if absent from active branch. Only one canonical rig branch/model is permitted; reconcile code, do not fork art direction.

**First demonstrable outcome:** a registered and visually readable upright plus expressive-pose A/B contact sheet, and a withheld-pose result, generated reproducibly by **one shared 3D candidate**. A raw generic neural 3D asset without these checks does not advance ART-4K. Defer inference/GPU/vendor selection until this has a measured baseline.

Every task below starts by reading **live main, #2832 head and changed files**, the existing two art authorities, exact source manifests and current work owner. Where source artifacts have expired, use a reproducible allowed native export or recorded metadata; do not invent visuals or rerun expensive original/native jobs solely to enlarge a dataset.

## Dependency-ordered work packets

### P0 / A0: preserve and inventory available evidence (small, no GPU)
**Owner:** current ART-4K graphics agent. **Input:** main + #2832, source docs/scripts listed in spec.

Actions:
1. Build a *machine-readable inventory* of authentic on-main source data, by exact repository path, SHA/lineage, native run/artifact availability, original renderer source class, 64x64 composed ID, 7:6/source viewport/crop and rights. Include authentic title guest400, PPU slots at 1856/1872/1888/2208, already generated 1205–1220 original-stock family, and available 1230–1239/1244–1252 or other distinct holdout candidates. Do not treat identical asset IDs/appearance as new views.
2. Compare available exact source PNG/PAM/ZIP members against the known SHA-bound original manifest. Explicitly identify *missing source bytes versus present provenance metadata*, especially expiring GHA artifacts. Mark each usable for silhouette, pose, color, authentic high-detail design, or only review illustration.
3. Read draft #2832's current export command and tests. Audit whether its OpenSCAD source/GLB are locally reconstructible using the documented tools and whether earlier #1826 animation preview logic is present/needed. Record current model source SHA, pose keys, part parents/children, normals/GLB build and dependency versions.
4. Capture known blockers: title frame400 is dark-faded, 2P OBJ source alpha is not finished composite ownership, earlier art approvals are superseded *for likeness*.

**Output:** one small corpus-readiness JSON + human one-page digest with source/availability flags; avoid committing licensed pixels. **Tests:** reject swapped hash, absent source, repeated raster as independent view, mixed 7:6/square, missing provenance, reference-type confusion. **Done when:** another agent can reproduce the same eligible reference set and explain why every admitted view is independent or an intentional temporal neighbor.

### P0 / A1: make a source-matched calibration packet
**Depends:** A0. **Owner:** ART-4K agent. No model changes yet.

Actions:
1. Select original composed gameplay poses and two genuinely different expressive states. One useful starter is the 1205–1220 exact registered P1/P2 strip already present; choose an additional **different family** such as 1244–1252 as a candidate withheld test *only if its actual source bytes and semantics are verified*. Also include the original native 2P sampled phase as an independently tagged cross-check, **not** as a directly equivalent 64x64 scene.
2. Reuse tools/art/measure_unicycle_reference.py and tools/art/audit_unicycle_pose_sequence.py for source-image-bound landmarks, image perspective, relative scale, camera confidence, wheel/saddle/fork/hub/pedal uncertainty and frame association. Never invent unavailable landmarks.
3. Establish at least two unchanged camera hypotheses: same orthographic camera with moving object versus camera/orbit changes. Distinguish screen-space spin, actual 3D yaw, original sprite family change and pixel aspect. Authenticate one best available title/official large image for design reference but keep high-detail calibration **conditional** if only faded or illustrated sources are available.
4. Fix the train/validation/test split, grouping exact same-pixel poses, palette variants and neighboring temporal aliases. Publish holdout manifest **before** geometry fitting. Explicitly mark no novel-view test when only one independent camera exists.

**Output:** hash-bound projected landmark/pose manifest, annotated separate private review images, a non-image comparison metric baseline and specific known-unmeasurable items. **Done when:** source evidence is reproducible, pose splits don't leak, no 3D dimensions are claimed from 2D ratios, and source design constraints are acknowledged.

### P0 / A2: refit existing five-part blockout and camera (first visual deliverable)
**Depends:** A1 and live #2832 coordination. **Scope:** source-only art tools, no native/presentation edits.

Actions:
1. Parameterize existing SCAD wheel radius/profile and fork/saddle shape in a model/parameter manifest while preserving the five named GLB parents and 16 source-colour child material identities unless source evidence requires a documented change. Keep immutable model/export receipts.
2. Add a calibrated offline projection tool (OpenSCAD/Blender or other tested renderer), named fixed-camera setups and exact output-size/crop/PAR transforms. Benchmark a black silhouette/landmark fit first against two independent meaningful source poses. Geometry parameters shared across all views; only explicit per-pose transforms vary.
3. Keep a locked near-side side/three-quarter render comparison at normal size (32/64px, 4x), and continuous full-motion observation; wheel outside diameter normalized in *model* space and guest placement separately registered. Do not distort physics contact to match a poster.
4. Produce A/B against *both* original source raster and vetoed existing native 4x art, with source/C++/new-model columns, measurement annotations, real-size thumbnails and exact hashes.

**Tests:** #2832 GLB watertight/finite/normal/pivot/export-atomicity suite; orthographic calibration synthetic fixture; no accidental auto-zoom, no cut-off silhouettes, identical explicit source re-renders hash to same output. **Deliver:** at least one single-rig *upright + expressive* review sheet and a 3D turnaround. **Gate:** candidate visibly represents the original better according to independent review, or mark refit unsuccessful; **never** promote from silhouette IoU alone.

### P0 / A3: fit source cadence and validate withheld pose
**Depends:** A2.

Actions:
1. Derive an offline pose mapping from verified original semantic frame IDs/pose equivalence, with root tilt/translation, wheel/crank phase, saddle lean/curvature and optional stretch; explicitly distinguish source-supported parameters from plausible performance/acting priors.
2. Ensure crank geometry and pedal-platform orientation stay valid as phase changes (whole-parent pedal mesh rotation is insufficient). Add a deformable saddle/head pathway if supported by original high-detail acting; don't invent steering bones.
3. Fit source-registered train frames without per-frame arbitrary scale, camera or bespoke mesh. Render a named *withheld* pose family without optimizing against its target image. Report metrics on train, validation and holdout independently, plus a 16-frame uninterrupted sequence and static/alias behavior.
4. Repeat with red/green colors from verified palette equivalence using identical mesh and shared lights. Identify where original PPU final-composite color is affected by foreground/HMDA rather than material paint. (Correct term: HDMA.)

**Tests:** original stock-static aliases remain identical after exact source pose mapping; cadence/changed-pixel ratio versus source; no hidden per-frame alpha trim/zoom; continuous wheel/pedal closure and pivots; source-provenanced holdout metrics. **Gate:** nondegenerate articulated motion and credible withheld-pose generalization; otherwise record specific missing geometry/camera evidence.

### P1 / A4: efficient inverse parameter optimization
**Depends:** A2 measurable refit.

Actions: Implement a bounded low-dimensional model optimizer, with CPU-first silhouette distance, landmark residual, geometric priors, alternating camera/model/pose blocks and finite optimization budgets. Cache by source SHA and full parameter/environment digest; report independent per-term losses. Multiple seeded starts, failed attempts and holdout scores remain visible. Compare manual/heuristic selected parameter baseline vs automatic fit with **same** held-out references. Do not infer success from a tuned training IoU alone.

**Output:** tool invocation + parameter bounds/seed, machine-readable run receipt, candidate source hash, fitted values, runtime/CPU/RAM and independent error breakdown. **Tests:** synthetic recoverable model/camera, malicious swapped image/crop, artificially degenerate zero-area/huge-camera candidate, determinism/float tolerance and cache invalidation. **Gate:** demonstrates meaningful non-overfit gains and repeatable output against the frozen baseline. If no gain, stop feature expansion and revisit evidence/parameterization.

### P2 / A5: conditional AI / novel reconstruction bakeoff
**Only if A3/A4 identify specific underdetermined shape limitations.**

Before dispatch, write a one-page hypothesis: which saddle/fork/backside property cannot be recovered using parametric constraints; what independent source view could disambiguate it; what model/pipeline is currently operational and legally suitable. Candidate trials: bounded visual hull if calibrated different views genuinely exist; TRELLIS.2, Hunyuan3D-2.1 or LARM if released code/weights/licenses/resources allow; PyTorch3D or nvdiffrast only for explicit differentiable shape parameter improvement. A vendor/cloud trial requires explicit cost cap/rights/hosting approval.

**Compare to A4:** same exact train/held-out input groups, source perspective/crop and output resolution; measure novel-view/pose consistency, geometry coherence, source identity, articulated parts, runtime/VRAM/cost. Either absorb a *specific* beneficial geometry proposal into the **existing canonical rig**, or reject the candidate. **Stop** if the model generates plausible generic bicycles, fuses the wheel/saddle, distorts mechanical joints, requires per-frame hallucination or fails holdouts.

### P1 / A6: art review and promotion (deliberately separate from model training)
**Depends:** A3 and/or demonstrably stronger A4/A5 candidate.

Reproduce reviewer packet with high-detail authentic source references when available; source 32/64px; current vetoed procedural baseline; new candidate at gameplay and 4x; labelled 3D side/three-quarter and a genuine continuous stunt/landing segment. Show 1P, split-screen 2P, physical pixel aspect, full motion (not chosen key frames), color variants and known uncertain geometry. Reviewer records explicit likeness decision and reference hashes. **No implicit approval by green CI or improved numeric scores.**

Only after acceptance: export registered 4x/HD sprite families from the same model into the **existing** HD selector/manifest/host path. Respect rendered OAM source pixels, foreground occlusion, exact guest pose/time, contact/pivot anchors and safe Original fallback. Run native Windows and QA-08/source verification on the precise product head with normal release controls. Archive a reversible candidate and preserve historic art hash approvals.

## Cross-cutting work packages

**A7 / evidence and correctness:** source manifest, measured metrics and provenance receipt all get small ROM-free synthetic tests. Preserve git/artist/reviewer source hashes; fail closed on historical artifacts no longer accessible. Never commit copyrighted original sprites from a hosted API directly to public CI. Use *the existing* tests and dossiers, and add only narrowly focused unit tests adjacent to the new tools.

**A8 / compute and automation:** default unit/PR CI is stdlib and synthetic, seconds rather than large scene render. Render/optimizer jobs run explicitly opt-in, cached and resumable, ideally on unattended HP non-LLM compute when it has idle capacity; record actual time/peak RAM/failed/skipped. No required OpenSCAD/Blender/PyTorch installation for all agents/ordinary CI. Prefer one reusable geometry render+cache to two independent source-PNG pipelines. Heavy jobs have budgets, source SHA, retry-once-if-transient policy and stop on semantic/provenance failures; no blanket reruns of expired native campaigns.

**A9 / branches and merge:** A0/A1 pure datasets and A2/A3 source-model work should be coordinated with #2832's owner and kept on that PR or a deliberately superseding PR. The documentation/spec lives in its own small PR and can be integrated independently without promoting art. Do **not** force-merge #2832 while draft or when likeness/owner gate is absent. Keep live shared work board singular; new dispatch is via existing ART-4K priority, not an hourly background job added by this plan.

## Minimum output checklist for each artifact

- [ ] Existing source files and exact branch/head/sha identified
- [ ] Source originals are separately classified as composed stock / raw PPU OBJ / final PPU / large-scale official image / candidate
- [ ] Every source image can be independently hash checked and has correct rights/source context
- [ ] Train/heldout view and pose groups frozen before fitting
- [ ] Canonical 3D model/part/pivot/camera manifest and output hashes retained
- [ ] Comparison at real gameplay scale and enlarged art-review scale
- [ ] Authentic source vs rejected 4x baseline vs new candidate, no mislabeled acceptance
- [ ] Temporal, contact, palette and occlusion tests with original-native semantics
- [ ] Clear measured compute cost and CI dispatch scope
- [ ] New art/likeness, technical correctness and release acceptance reported as separate fields

## Prioritization / stop conditions

**Highest leverage:** A0 -> A1 -> A2 -> A3. A4 follows a genuine registered A2 candidate; A5 is strictly conditional. A6 gates only shipping promotion, not research iteration. Cross-cutting A7–A9 support all.

If independent high-detail source viewpoint is missing, progress the source-registered parametric model against verified gameplay views while reporting missing design confidence; do not block the whole lane on speculative archive hunting. If even a two-pose same-rig reproduction fails after bounded fitting, investigate camera/view and existing model structure rather than launching a dozen diffusion packages. If a different rig appears better, compare on identical held-out source and migrate its *measured advantage* into the existing part-addressable model. If a supposedly novel view is a rotated 2D frame or re-cropped cover, discard novel-view confidence.

**Milestone outcomes (no invented dates or %):**
- M0: verified corpus and protected holdouts;
- M1: source-fit two-pose model + locked-camera A/B packet;
- M2: coherent source-registered animated loop + honest withheld-family score;
- M3: repeatable optimizer with benchmarked gain or documented negative result;
- M4: explicit owner likeness sign-off;
- M5: original-safe HD presenter integration + full appropriate native verification.

**Handoff to any agent:** "Read main and active #2832, docs/HD-RACER-INVERSE-GRAPHICS-SPEC.md, docs/HD-RACER-INVERSE-GRAPHICS-PLAN.md, existing HD-RACER-CHARACTER-RECONSTRUCTION and projected-landmark authorities; execute the earliest unblocked A-task with its evidence/negative tests; keep the 2026 procedural blockout unapproved, use exact original source frames, and do not add a parallel rig, CI lane or runtime HD selector."
