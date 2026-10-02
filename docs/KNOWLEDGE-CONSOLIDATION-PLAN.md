# Knowledge Consolidation Plan

Status: initial consolidation complete
Date: 2026-10-02

## Purpose

UR-Recomp has accumulated high-quality evidence in many specialized artifacts, but related facts are spread across generated JSON, long-form research notes, symbol tables, historical-source notes, regional correspondence and one-off runtime reports.

The goal is to add a small normalized **query layer** without replacing or flattening the underlying evidence.

Detailed source artifacts remain authoritative evidence. Consolidated datasets contain normalized records with explicit provenance back to those artifacts.

## Design principles

1. **No giant universal JSON file.** Keep domain datasets separate and cross-reference by stable IDs.
2. **Evidence is not overwritten.** Normalized records point back to their sources.
3. **Promoted fact and historical label are different fields.**
4. **Derived values are marked as derived.**
5. **Unknown semantics stay unknown.** Structural identity alone does not justify a name.
6. **Generation should be deterministic.** Prefer scripts over hand-maintained duplicate values.
7. **Schemas are additive.** Downstream inference tools should survive new optional fields.

## Canonical normalized datasets

### `analysis/data/course-corpus.json`

One record per decoded course stream.

Join:

- RNC stream identity, offsets, sizes and hashes;
- course ordinal/tour/slot/type/name;
- decoded header dimensions;
- spawn/landmark pairs;
- resource-list/cursor information;
- resource IDs/count;
- calculated coarse grid/world extent;
- known presentation-contract measurements;
- runtime-confirmed landmarks where available;
- external map/reference identifiers.

This is the primary input for the first inference audit.

### `analysis/data/state-schema.json`

Normalize RAM/SRAM semantic knowledge.

Each entry may include:

- canonical name;
- address/width/signedness;
- storage/lifetime class;
- player ownership;
- known paired/shared relationships;
- regional addresses;
- value-domain notes;
- confidence;
- original evidence references;
- historical aliases or superseded labels.

Seed from `analysis/generated/symbols.json` and enrich with regional racer-state relations. Later passes may incorporate RetroAchievements, TAS watch lists, Nitrodon annotations and save/progression models as atomic provenance rather than replacing promoted symbols.

### `analysis/data/code-semantics.json`

Join named function symbols, cross-build function correspondence and the comparative structural census.

Keep two levels:

- semantic functions/services;
- bounded structural regions.

Record cross-build homologues and source-island membership without pretending every bounded region is a named function.

### `analysis/data/presentation-assets.json`

Normalize semantic frame/asset/palette identity into a multi-family container.

The first family is the retained ordinary-race racer presentation manifest. Future sprite/background/UI families append without creating incompatible one-off schemas.

### `analysis/data/evidence-claims.json`

Atomic, provenance-bearing claims that originate in external/historical material or cross-source reconciliation.

A claim contains:

- stable id;
- subject;
- predicate;
- value;
- status;
- source paths/ids;
- corroboration;
- notes.

This file is intentionally selective at first. Only claims with current inference value should be normalized; prose source notes remain the archival record.

## Implementation

Add `tools/build_consolidated_knowledge.py`.

The builder should:

1. read existing canonical/generated sources;
2. perform deterministic joins;
3. derive only explicitly documented quantities;
4. emit the five datasets;
5. fail on duplicate stable IDs or broken required joins;
6. preserve source paths in every output.

Add unit coverage for:

- 45-course completeness;
- world/coarse dimension derivation;
- stream/resource join by course index;
- state-address normalization and regional relations;
- named-function/census correspondence;
- presentation-family preservation;
- claim-ID uniqueness.

## Initial derivations

The course builder may derive:

- `coarse_grid = header_dims × 4`;
- `world_extent = header_dims × 256`;
- aspect ratio;
- RNC compression ratio;
- bytes from initial resource cursor through EOF;
- resource-count and sequence signatures.

These calculations are based on the currently promoted course-family presentation contract. Mark them as derived so the inference audit can still test whether any course violates the assumed family rule.

## Provenance tiers

Use simple machine-readable classes:

- `runtime_proven`;
- `static_proven`;
- `cross_build_supported`;
- `derived_from_promoted`;
- `historical_independent`;
- `external_unreproduced`;
- `candidate`.

A record may cite more than one tier/source.

## Repository relationship

- `docs/SYMBOLS.md` remains the human-readable symbol ledger.
- `analysis/generated/*` remains the experiment/analyzer output surface.
- `reference/notes/*` remains the archival/historical research surface.
- `analysis/data/*` becomes the normalized cross-domain query surface.
- inference reports go back to `analysis/generated/*`.

## Maintenance rule

When a source artifact changes, regenerate the normalized datasets. Do not hand-edit a generated field in `analysis/data` to disagree with its source.

Hand-curated atomic claims are allowed only in the claims seed maintained by the builder, with explicit source paths.

## Completion criteria for this pass

This consolidation pass is complete when:

- all 45 USA course streams have normalized records;
- the promoted symbol ledger is available in normalized state form;
- regional racer relations are attached where available;
- named functions and structural census regions can be queried together;
- the first presentation family is represented in a reusable multi-family schema;
- a small high-value historical claim set is normalized;
- unit tests protect the joins and derived course geometry;
- both plans point future work at the normalized surfaces rather than requiring ad hoc prose joins.

A later pass can expand claim extraction and progression-specific normalization without blocking the inference audit.

## Initial pass closeout — 2026-10-02

The initial consolidation pass is complete and protected by unit tests. The query layer now contains the full 45-course corpus, normalized promoted state semantics with regional racer relations, semantic-function/structural-census joins, the first reusable presentation family, and an initial atomic claim surface. The first inference audit consumed these files successfully and exposed one representation bug during validation: low mirror ROM code banks from the symbol ledger must be canonicalized to their high CPU mirrors before structural joins. That normalization is now part of the builder.

## Second pass closeout — 2026-10-02

A second consolidation pass corrected canonical course stream identity by reconciling decoded header coordinates, the complete historical landmark corpus, and SRAM progression row order. It also attached all 45 historical landmarks to course records, normalized the progression model, and enriched state data with paired-racer leads, regional motion clusters, and reconciled Nitrodon semantics. The key maintenance lesson is that player-facing order, storage order, and historical tool track IDs are separate coordinate systems and must never be joined by ordinal position without an explicit mapping.
