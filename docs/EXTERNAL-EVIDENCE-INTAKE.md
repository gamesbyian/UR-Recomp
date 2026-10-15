# External Evidence Intake

## October 15, 2026: malmazuke PAL evidence follow-up

Consult [the pinned cross-project handoff](CROSS-PROJECT-BEHAVIOR-CORROBORATION.md#october-15-2026-pal-intake-menu-controls-and-multi-tour-leagues-conditional) before scheduling repeat PAL archaeology. Newly accepted **PAL** MENU-INPUT #79/R-0097, and **unmerged draft** LEAGUE-TOURS #81/R-0098 (head `876aa89f0157b252e559aca2e42f1e9efe78b2dc`), can shorten existing USA investigations into pad ownership, result/awards transitions, two-human stunts and SRAM timing. No general code transplant: PAL original reference captures and disassembly are evidence leads, not USA original witnesses. The existing cross-project source index/pinned corpus, research ledger, and specialist authority decide which question is unresolved.

**Intake finish condition:** check upstream PR review/merge and pins; compare each potentially relevant claim with existing USA source/fixtures; nominate **at most one cheapest first-difference original-USA experiment per demonstrated live blocker**, with exact ROM/core/candidate provenance, frame origin and pad stream; hand it to its existing owner. If the owner has no relevant failure, record deferred/reopen-only status and stop. Avoid extra GHA triggers or importing giant PAL evidence files. Upstream's October 14 evidence cleanup (#80) illustrates retaining replay recipes and hashes, but UR's own retention and CI policy remains authoritative.


This document defines how public third-party research moves from an interesting lead into project-owned, reproducible evidence.

The source registry is `reference/catalog.yml`. The actionable queue is `reference/evidence-worklist.json`. The worklist owns current uncertainty, acquisition state, next discriminator, expected deliverables, and whether human download assistance is actually required. It is intentionally separate from the chronological `docs/RESEARCH-LEDGER.md`.

## October 2026 code-search deduplication decision

The [13 October Uniracers GitHub code-search closeout](../reference/notes/github-uniracers-code-search-closeout-20261013.md) reconciles Snes9x, MAME/bsnes, jgenesis, ZSNES, RustySNES, PAL malmazuke, game databases and sound-driver build notes against the existing repository. It is a **read-only source delta**, not a new source import or direct game-truth claim. Check it before accepting another OAM/2P emulator fork as an independent source. The worklist entries `active-display-oam-behavior` and `historical-emulator-failure-matrix` now identify previously completed original-USA experiments and the **remaining conditional** first-difference tests. Do not duplicate already-landed source patches, observability tools, replay routes, graphics surveys or ROM downloads.

## Evidence pipeline

Use the smallest path that can answer the current question:

1. **Index the source.** Add stable title/author/date/URL/revision information and rights status to `reference/catalog.yml`.
2. **Create or update a worklist lead.** State the uncertainty as a question, identify the cheapest useful discriminator, and say what durable project artifact should result.
3. **Acquire only what is useful.** Prefer original patches, source, traces, movies, metadata, SPCs, documents, or other research artifacts over transformed ROM images.
4. **Fingerprint immediately.** Record original filename/container, byte size, SHA-256, source URL, retrieval date, and upstream revision/hash where applicable.
5. **Keep third-party bytes quarantined.** Imported material belongs under `reference/imported/` and must follow `reference/imported/MANIFEST.json` and `docs/THIRD-PARTY-CODE-AUDIT.md`.
6. **Convert the artifact into a project-owned observation.** Examples include touched-ROM ranges, RAM predicates, symbol candidates, decoded data structure, input stream, audio-driver fingerprint, or emulator-sensitive event.
7. **Reproduce locally.** External claims and labels remain leads until a canonical ROM/runtime experiment supports them.
8. **Promote durable truth.** Confirmed technical conclusions go to `docs/RESEARCH-LEDGER.md`, `docs/SYMBOLS.md`, a deterministic fixture/test, or the subsystem authority that owns the fact.
9. **Close or downgrade the lead.** Mark dead ends and context-only results so future agents do not repeatedly excavate the same empty hole.

Run:

```bash
python3 tools/validate_external_evidence.py
```

to validate and summarize the queue. `--json` emits a compact machine-readable summary, including any leads whose artifact acquisition genuinely requires user action.

## Patch archaeology

Third-party IPS patches are unusually useful because they encode another reverse engineer's discoveries without requiring their notes to survive.

Use:

```bash
python3 tools/analyze_ips_patch.py path/to/patch.ips
python3 tools/analyze_ips_patch.py path/to/patch.ips \
  --base reference/roms/retail/Uniracers_USA.sfc \
  --output analysis/generated/example-patch-map.json
```

The analyzer reports literal/RLE records, coalesced file-offset ranges, canonical LoROM address hints, hashes, and, when a base image is supplied, the number of bytes that actually change and the resulting image hash. It never modifies the base image in place.

For translation/restoration patches, the first classification pass should distinguish at least:

- text/string data;
- pointer or index tables;
- font/tile graphics;
- UI width/layout data;
- checksum/header-only edits;
- executable code changes;
- unrelated padding or copier-header offsets.

Do not treat a translated or otherwise modified ROM image as the preferred research artifact when the original patch can be recovered.

## Acquisition escalation

Automated retrieval should be exhausted before asking for manual downloads:

1. direct public URL;
2. surviving mirror;
3. source-host release/attachment;
4. Wayback or archive capture;
5. exact filename/hash search;
6. author/group pivot;
7. one-shot repository workflow when the agent environment cannot transfer a public binary directly.

A one-shot workflow is temporary acquisition infrastructure. It should produce hashes/reports or a short-lived artifact, must not become recurring CI without a durable invariant, and should be deleted once its evidence has been harvested.

Only set `artifact_need.user_action_required=true` after the automated/archive routes have materially failed. The request must name the exact artifact or page and explain what should be uploaded. Do not ask the user to perform broad research that the repository can automate.

## Rights and publication boundary

Availability is not ownership. A public artifact may be useful research evidence while still being unsuitable for permanent redistribution in a public repository.

Prefer committing compact derived metadata, hashes, reports, and project-owned tooling when third-party redistribution rights are unclear. Preserve raw bytes only when the existing corpus policy and rights assessment support doing so. Never import third-party ROM distributions merely because they are convenient.

## Current high-information lead classes

The worklist currently emphasizes:

- active-display OAM and historical emulator failure seams;
- differential archaeology across the four preserved builds;
- independent Spanish translation patches as text/font/pointer maps;
- SPC dumps as APU/audio-driver and unused-content evidence;
- lost TAS tooling such as `usjo13.lua`;
- original DMA authoring tools and SNES framework material;
- fan-recreation author pivots only where they may contain measurements, source, or technical experiments.

Social demand for a remake/rerelease is useful primarily as a breadcrumb graph. Preserve it when replies expose authors, projects, files, or technical claims; otherwise keep it context-only rather than letting sentiment consume reverse-engineering time.


## Deduplication preflight

Before adding a new source-derived work item, check whether the repository has already solved, imported, or queued the same artifact or question under older terminology.

At minimum search:

- `docs/RESEARCH-LEDGER.md` for promoted or rejected conclusions;
- `reference/notes/` for recovered historical artifacts and prior archaeology;
- `reference/catalog.yml` for the same URL, filename, hash, author/project, or artifact;
- `reference/evidence-worklist.json` for an existing discriminator covering the same mechanic or failure;
- `analysis/generated/` and relevant tools/tests for already-landed extraction or reproduction work.

Classify a new web hit before creating work:

1. **Corroboration only:** it supports a fact already solved locally. Add provenance to the existing source set if useful; do not create another work item.
2. **New discriminator:** it conflicts with, sharpens, or adds a distinct test to an open question. Extend the existing work item.
3. **New lead:** create a new work item only when neither the fact nor a suitable discriminator already exists.

A rediscovered artifact that is already imported, hashed, parsed, or replayed is not an acquisition lead. Update stale source metadata instead of adding a second identity for it.
