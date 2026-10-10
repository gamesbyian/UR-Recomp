# Definitive Uniracers technical reference: enduring project charter

**Status:** durable objective, 2026-10-10. This document describes completion standards, not a release gate or new immediate feature freeze. [PROJECT-PLAN.md](PROJECT-PLAN.md) owns durable game/product architecture; [WORK-QUEUE.md](WORK-QUEUE.md) owns near-term execution; [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json) alone owns release acceptance.

## Dual objective

UR-Recomp aims to deliver (A) an authentic, accessible, modern, extensible Uniracers/Unirally game and (B) a definitive, independently reproducible technical reconstruction of all recoverable original software. Neither objective subsumes the other.

A future contributor should be able to recover and verify every explained behavior, trace it to original instructions or data and independent observations, rebuild the original representation where possible, and pursue a new implementation or enhancement without reverse-engineering our undocumented workarounds. A faithful executable and a fully understood executable are separate accomplishments.

## Two coordinated tracks, one source of truth

**Playable Remaster:** original-correct simulation; cohesive Modern frontend; real 1P/2P and complete results; safe saves, records, ghosts, replays and tournaments; authentic Original mode; stable true widescreen and optionally authored HD; candidate-bound Windows validation. Ship playable internal builds without falsely claiming final release certification.

**Technical Reference:** original executable map; named reassemblable disassembly; CPU/PPU/APU/DMA and host timing; graphics/audio and course formats; physics, lap, scoring, progression and event semantics; regional differences; extraction/repacking; repeatable comparative evidence; documented historical uncertainty; accessible cross-linked atlas.

The tracks reuse the *same* ROM provenance, named addresses, authoritative executable, source-disassembly indexes, test witnesses and reusable product interfaces. No parallel gameplay simulator, overlapping save store, competing active plan or copy-paste experiment framework. Accepted research may improve the product; observed product defects may motivate research. Neither track can make speculative completeness an indefinite product-development blocker.

## Four independently assessed dimensions

1. **Mechanical:** every recoverable instruction, control/data entry and hardware interaction accounted for, including interpreted or otherwise uncertain paths and lossless data round-trips when feasible.
2. **Evidential:** meaningful statements cite concrete original ROM/disassembly locations, artifacts, test inputs, reference emulator and candidate SHAs; alternatives, negative results and mismatch limitations are retained.
3. **Architectural:** one authority per concern, separated guest/host state, replaceable renderer, deterministic reproducible tools, explicit compatibility boundaries, no unexplained patches or irreversible undocumented transformations.
4. **Explanatory:** subsystem questions can be answered via navigable technical accounts and linked verification, without dependence on private agent history or ephemeral CI logs.

Do not label anything *fully understood* based only on native recompilation, a byte-identical code rebuild, matched WRAM checksum, one route, an accepted sprite mask, or a plausible explanation.

## Technical Atlas contract

Grow the atlas from existing [knowledge/README.md](knowledge/README.md), [RESEARCH-LEDGER.md](RESEARCH-LEDGER.md), subsystem documents and proven artifacts rather than creating a competing encyclopedia. Each completed entry records:

- **Question and scope:** the exact behavior, ROM region/variant, modes, hardware assumptions and excluded cases.
- **Original authority:** bank/PC, symbols, instructions, bytes/data format, source provenance and reproducible extraction.
- **Semantic model:** named state, transitions, arithmetic/bit widths, edge behavior and what remains inferred.
- **Reproduction:** inputs, emulator/core/tool versions, hashes, controls, expected/observed output, fail-closed checks and regression coverage.
- **Cross-links:** underlying executable symbols and adjacent subsystems, product adapter, relevant data/graphics artifacts and prior conflicting hypotheses.
- **Confidence and unknowns:** verified, strongly inferred, candidate hypothesis, disproved, unobserved, or intrinsically unrecoverable (e.g. developer intention without documentary evidence).

Prefer generated/checked indexes and stable references. Preserve copyrighted ROM and game assets only within the repository's current private research boundary; the technical atlas must not imply public redistributability.

## Quality and prioritization rules

- The product can advance toward alpha once a verified original-native Windows journey works; full technical-atlas completion and all 45-course release gates are **not prerequisites to regular development**.
- Maintain an independent QA lane and promote gate claims only through [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json) on the exact candidate.
- Protect original execution correctness and player-data integrity immediately. Classify other gaps as product implementation, release evidence, deep-reference investigation or optional enhancements; do not interchange them.
- Preserve the earlier patched backend as a rollback while Baldosa adoption remains provisional; source/recompiler causal comparison lives in [BALDOSA-LEGACY-RECOMP-CAUSAL-COMPARISON-20261010.md](BALDOSA-LEGACY-RECOMP-CAUSAL-COMPARISON-20261010.md).
- Every hypothesis requires the smallest discriminating original-source observation and a stop condition. Preserve useful negative findings. Retrospective investigation remains first-class, but bounded in the active queue unless it changes a player-visible or architectural decision.

**Ultimate acceptance:** a technically competent outsider can reproduce the game and its documented internals, discover residual uncertainty promptly, replace/extensively extend presentation or product systems without guest hacks, and follow every significant claim back to its evidence.
