# Windows Visual Atlas: source-bound screenshots, coverage and mobile review

**Owner request:** complete Windows product visual inventory; genuine images wherever a Windows capture exists, and unmistakable **COMING SOON** architectural/graph-paper illustrated references for missing surfaces. Browser must be comfortable on a phone and copy durable IDs/link+context for agents.

**Status (2026-10-23 initial implementation):** First reference inventory, ROM-free contract validator, capture sharder, GHA workflow and static mobile viewer are implemented on a feature PR, subject to CI, actual hosted capture and review. The inventory has **199 stable entries**: 54 curated Windows-surface IDs, 120 original UI source-anchors, 25 independent visual acceptance cases; **13 mapped to existing native semantic capture routes** in four shards. A mapped route is a *candidate*, never an observed screenshot. Nothing in this document approves a screenshot, model, art, hardware journey or release gate.

## Actual repository reuse and boundaries

| Authority/tool | Role in the atlas |
| --- | --- |
| `AGENTS.md`, `docs/WORK-QUEUE.md`, `docs/HOURLY-AGENT-LINES.md` | Shipping priority, protected ownership and budget. The atlas is complementary, not a new release gate. |
| `analysis/ui-capture-manifest.json` / `analysis/ui-state-map.yml` | Original-game UI-state inventory and WRAM anchors; **not** fabricated Modern coverage or a competing state machine. |
| `analysis/modern-visual-acceptance-matrix.json` / `docs/MODERN-UI-VISUAL-FIDELITY.md` | Independent visual matrix and human checks. Atlas images may link to evidence but cannot award its approvals. |
| `tools/qa_modern_visual_win32_capture_driver.py` | Source-checked real Windows SDL readback launcher and semantic route fixtures; creates fresh user-data roots. |
| `tools/qa_modern_visual_sdl_capture.py` | Pinned Baldosa final-SDL-readback instrumentation staged in disposable checkout. No production renderer modification. |
| `tools/qa_modern_visual_pam_png.py` | Exactly converts authentic P7 raster bytes to PNG; no rescale or invented pixels. |
| `.github/workflows/modern-visual-native-win32-capture.yml` | Proven Windows 2022/pinned toolchain/native staging procedure. The new campaign is manual and does not replace this independent QA workflow. |
| `tools/showcase/graph_paper_trailer_art_direction.py` | Design vocabulary: cream drafting grid, source ink sketches, printed type, restrained red accents and footers. |
| `media/showcase/2026-10-20/graphpaper-final/cards/*.png` | **Actual existing owner-supplied / editorial art plate family** used behind explicit missing-surface labels, without synthesizing fake product screenshots. |
| `docs/CI-WORKFLOW-BEST-PRACTICES.md` | Opt-in extended compute, source-bound evidence, cancellation discipline, bounded fan-out, no redundant Windows AOT builds. |

The first implementation owns only `analysis/windows-visual-atlas.json`, `tools/windows_visual_atlas.py`, `tools/visual_atlas_web/*`, its small ROM-free tests and the opt-in Actions workflow. Do not edit shipping frontend, guest, PPU, save store or current visual acceptance authority to make a screenshot prettier.

## Coverage model: enumerate the product before collecting images

One **immutable ID** names one expected **visually distinguishable state**; a new capture updates its evidence, not its ID. An ID records presentation mode, surface family, UI/game state, display geometry, and capture recipe if known.

Mode coverage includes Modern, Authentic guest output, Original 4× fallback, Remastered/HD and actual widescreen composition; future P2P references remain labeled future until implemented. Surface families include title/boot, root+menu selections, profile creation/selection, 1P/2P/controller ownership, game modes/tour/practice, records/results, display+accessibility/options, pause/restart, System/Recovery, gameplay countdown/loop/jump/stunt/finish/HD OAM, multiplayer setup, credits and future interfaces. Each screen can have additional **state** samples for selected/hover/focus/disabled/error/empty/transitional/reduced-motion/4:3/16:9, plus cropped ROI evidence when warranted.

Coverage policy:
1. Start with an explicit expected-surface registry; **do not infer completeness from harvested screenshots**. Source state maps and issue/plan design specs inform enumeration, not a speculative all-combinations Cartesian explosion.
2. Add one stable ID for each meaningfully distinct visible behavior. Give comparative geometry/motion variants separate IDs where important; reuse ordinary case metadata for trivial size/cursor permutations.
3. Registry statuses at build time: `captured` only with independently matched Windows SDL receipt+PNG; `capture_pending` for existing semantic driver route without admitted bytes; `capture_failed` for a preserved failed route; `planned` for surfaces needing a route/implementation. On phone, `planned` reads **COMING SOON**, `capture_pending` never masquerades as finished visual work.
4. Subsequent expansion must diff the registry against Modern destination routes, original UI-state manifest, visual acceptance matrix, options/pause states, build variants and known defects. Add coverage for each genuinely uncovered screen/cursor/overlay/visual defect, including one example of every materially different item, and record exclusions. Reviewers can demand additional focused captures by ID.
5. Annotate evidence with SHA identities, exact source file, executable, renderer output size, route, driver and screenshots. A future per-region markup/annotation layer will attach normalized ROI to an ID + capture revision, so users can copy precise visual criticism without corrupting originals.

Original UI and independent QA-matrix references deliberately retain separate `URV-OG-*` and `URV-QA-*` identities, even when they revisit the same general menu: they name a specific original fixture or review obligation, rather than asserting that a corresponding Modern/Authentic Windows screenshot exists. If one genuine Windows capture satisfies several references, later versions should map those IDs to one immutable image receipt rather than duplicate the render. **Initial capture map:** Existing driver routes `root-quit`, `records-keyboard`, `practice-picker`, `multiplayer-unrecorded`, `options-p1`, `profile-first-p1`, four normal/reduced root-motion phases, and `authentic-stock`, at the explicitly requested wide/compact geometries. The first 13 mapped captures are **not** independent complete product journeys or release approval. Title, actual race HUD, native results, error dialogs and the majority of detailed states require their own demonstrated capture routes. No fake guest or screen data is permitted.

## Architecture and lifecycle

```text
analysis/windows-visual-atlas.json   (durable expected surfaces / stable IDs)
                   |
         validate + cheap PR tests
                   |
     one-shot first-merge or manual windows-visual-atlas.yml
                   |
  windows-2022: pinned Baldosa generated / native AOT, one tested PE
                   |
            immutable PE artifact
                   |
    4 independent job cohorts, max 3 Windows jobs simultaneously
       frontend | interaction | motion | authentic
                   |
      1 or 2 native capture processes per Windows job
      each case owns fresh config/user-data/temp/output directories
                   |
     allowlisted PNG + P7 + readback receipts / failure markers
                   |
        read-only Ubuntu assembly and hash admission
                   |
      self-contained atlas site artifact (30-day retention)
                   |
      optional GitHub Pages deployment (manual flag only)
```

The outer **job-level shard** divides independent screenshot families so a failed child route cannot waste another family, and so separate Windows machines share one immutable PE instead of recompiling. The inner **process-level shard** uses a maximum two independent native processes per Windows job (serial=1 available). The two captures are independent SDL renderer readbacks, **not physical Windows desktop screenshots**, and each case gets its own user-data root. No two processes may share storage, process config or mutable save timeline. UI focus/real-controller/desktop-screen tests are expressly disallowed from multi-process execution until proven safe.

**Initial bound:** one build job, four capture cohort jobs with `max-parallel: 3`; total at most three simultaneous Windows capture runners, and at most six native game processes, leaving other agents room under the owner's **20-runner ceiling**. This avoids an undisciplined per-screen matrix: each cohort runs several isolated cases, with scheduling bounded by a worker pool. Build first; only expand beyond this cohort count after measuring useful frame yield and duration. The bounded one-shot/manual workflow sets 35-minute per-Windows-job, 10-minute assembly and bounded per-route deadlines; failures produce named evidence, not silently fabricated screenshots or automatic retries.

The GHA artifact uploads **only** allowlisted screenshot PNG, raw P7, receipt, diagnostic logs and explicit failure markers. Never upload a ROM, extracted guest memory/SRAM or the fresh game user directory. The assembled website copies only approved existing illustrated plates plus PNG screenshots whose exact filename, output dimensions, source SHA, route, declared SDL mode and SHA256 match a retained receipt. Mixed executable hashes or forged/mismatched PNG receipts fail assembly. No automatic commit to main, Pages or release ledger.

## Mobile interface and reference protocol

The dependency-free `tools/visual_atlas_web` client is intentionally static: responsive two-column phone browsing, search by title/state/ID, filters by presentation/family/evidence, 16:9 preview plates, full-size inspection, 1:1 pixel view on genuine screenshots, horizontal swipe and keyboard next/previous, accessible buttons, reduced-motion preferences, and a real direct URL hash `#URV-MD-001` per identity. Clipboard actions provide either a direct link or full agent-ready reference.

Copy format:

```text
Inspect URV-MD-001: Modern root, widescreen. Modern / Front end /
Main menu / 1280 × 720. Real Windows SDL capture; source <40-hex>,
EXE SHA256 <64-hex>; PNG SHA256 <64-hex>. Atlas: <hosted-url>#URV-MD-001
```

A missing capture explicitly states that no Windows screenshot has been admitted. An `https:` URL is included **only when the site is actually hosted**; local previews copy the stable ID. Deep links remain stable when a screenshot revision changes.

**COMING SOON graphic:** Reuse real approved graph-paper promotional plates as the background rather than attempting to draw the unshipped screen. A large visible status sash and the provenance pane distinguish illustration from Windows software. Later iterate with the original art-direction generator to create plate-specific illustrated mockups, carrying provenance and owner approval; never call concept art a gameplay capture.

## How to run and where the output goes

Cheap PR checks, ROM-free:

```sh
python3 -m unittest tests.unit.test_windows_visual_atlas
python3 tools/windows_visual_atlas.py validate
python3 tools/windows_visual_atlas.py build --out /tmp/ur-atlas-preview
python3 -m http.server 8000 --directory /tmp/ur-atlas-preview
```

Actual Windows capture: the initial PR carries an explicitly authorized one-shot sentinel in `analysis/windows-visual-atlas-first-capture.request`; merging it to `main` launches **one** bounded, source-exact hosted campaign. For subsequent captures, use [Actions / Windows Visual Atlas](../.github/workflows/windows-visual-atlas.yml) → **Run workflow** on the exact intended ref. Leave Pages flag false until the repository Pages source is configured to GitHub Actions and you intend to publish. Choose one or two workers per Windows capture job; in the first run, inspect any exact-drawable refusals and log SHA provenance. The four named capture artifacts retain short-lived raw evidence; the `ur-windows-visual-atlas-website` artifact contains the browser-ready offline-distributable site. No user needs to babysit every cohort; failures are reported by ID in `shard-summary.json`.

## Subsequent milestones / outstanding items

- **M0, in this PR:** baseline catalog (199 = 54 curated + 120 source UI + 25 acceptance cases), 13 route mappings, GHA captured-binary sharing and nested bounded sharding, ROM-free evidence guard, original promotional backgrounds, responsive static browser and copy/deep-link controls. Must pass unit, JS syntax and exact hosted workflow validation. No live Windows screenshot claimed.
- **M1, immediately after merge:** execute one deliberate manual hosted run, preserve run/artifact URLs, classify the 13 receipts into actual captured, failed and pending, inspect actual PNGs on a phone; correct capture driver differences on *their owning test route*, not by weakening acceptance. Publish a source-bound assembled atlas artifact, optionally configure Pages.
- **M2, inventory completeness:** reconcile `analysis/ui-capture-manifest.json`, `analysis/modern-visual-acceptance-matrix.json`, the Modern root/destination code and current issues to add missing state/mode geometry entries. Capture authentic original menus, actual race/finish/HUD, real 1P/2P split, title and profiles from specifically reproducible true Windows processes; include state fixtures/trace identities. Record why blocked states cannot yet be captured.
- **M3, richer inspection:** two-source comparison, blink/overlay/difference map at equivalent pixel geometry, configurable crops and ROI annotations, screenshot revision timelines, issue permalink creation, image contact sheets and filtering by open visual defects. Reuse existing QA diff helpers. Do not compare differently scaled source pixels as parity evidence.
- **M4, maintainability/acceptance:** one targeted snapshot smoke per affected frontend/display module, opt-in big campaigns, manifest/schema policy tests, retention/publishing decisions, real Pixel 6 Pro portrait Chrome/PWA inspection, keyboard/screen-reader review, and human art signoff. Keep release ledger independent. Separate visual acceptance from hardware/controller/audio QA.

**Known limits as written:** No Windows process was executed from this editing environment; the first genuine hosted capture is set to launch once after merging to main. Pages configuration was not readable from the available repository API; deployment stays manual/off by default. Historic marketing plates carry separate redistribution/owner-approval considerations. Route names and state coverage will evolve on active `main`, and the named capture routes have not yet been re-proven on the exact PR head.
