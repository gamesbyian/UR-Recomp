# External Evidence Intake

This document defines how public third-party research moves from an interesting lead into project-owned, reproducible evidence.

The source registry is `references/catalog.yml`. The actionable queue is `references/evidence-worklist.json`. The worklist owns current uncertainty, acquisition state, next discriminator, expected deliverables, and whether human download assistance is actually required. It is intentionally separate from the chronological `docs/RESEARCH-LEDGER.md`.

## Evidence pipeline

Use the smallest path that can answer the current question:

1. **Index the source.** Add stable title/author/date/URL/revision information and rights status to `references/catalog.yml`.
2. **Create or update a worklist lead.** State the uncertainty as a question, identify the cheapest useful discriminator, and say what durable project artifact should result.
3. **Acquire only what is useful.** Prefer original patches, source, traces, movies, metadata, SPCs, documents, or other research artifacts over transformed ROM images.
4. **Fingerprint immediately.** Record original filename/container, byte size, SHA-256, source URL, retrieval date, and upstream revision/hash where applicable.
5. **Keep third-party bytes quarantined.** Imported material belongs under `references/imported/` and must follow `references/imported/MANIFEST.json` and `docs/THIRD-PARTY-CODE-AUDIT.md`.
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
