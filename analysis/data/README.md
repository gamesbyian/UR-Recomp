# Consolidated knowledge data

This directory is the normalized query layer for retained UR-Recomp evidence.

The files here do not replace the underlying evidence in `analysis/generated/`, `reference/notes/`, or the human-readable symbol/research ledgers. They join selected high-value facts across those sources with explicit provenance so inference tooling does not need to scrape prose or rediscover relationships.

Current surfaces:

- `course-corpus.json` — one normalized record for each of the 45 USA course streams, including calculated presentation geometry.
- `state-schema.json` — promoted RAM/SRAM semantics plus cross-build racer state relations.
- `code-semantics.json` — named semantic functions joined to the comparative structural census and cross-build correspondence.
- `presentation-assets.json` — reusable container for semantic presentation/graphics families.
- `evidence-claims.json` — selective atomic claims whose provenance matters for cross-source inference.
- `progression-model.json` — normalized medal matrix, tier derivation, checksum coverage, and current runtime-acceptance status.
- `course-resource-catalog.json` — promoted resource semantics, conserved bundles, and cross-build resource-selection deltas.
- `fixture-corpus.json` — curated semantic/event anchoring and suitability metadata for the most important deterministic fixtures.

Regenerate with:

```bash
python3 tools/build_consolidated_knowledge.py
python3 tools/build_consolidated_knowledge.py --check
```

See `docs/KNOWLEDGE-CONSOLIDATION-PLAN.md` for ownership and maintenance rules and `docs/INFERENCE-AUDIT-PLAN.md` for the analysis that consumes these datasets.

Second-pass consolidation also attaches the recovered 45-track historical start/finish landmarks directly to course records, and enriches `state-schema.json` with paired-racer leads, regional WRAM motion clusters, and reconciled Nitrodon semantics.
