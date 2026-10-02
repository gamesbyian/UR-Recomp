# Inference Audit Plan

Status: active research plan
Date: 2026-10-02

## Purpose

UR-Recomp now has enough independent evidence that some remaining questions can be answered more efficiently by deriving predictions from existing data than by beginning with another runtime experiment.

This plan establishes a deliberate **derive first, probe second** research lane. It does not replace runtime validation. It turns the retained corpus into a constraint system so that new experiments are reserved for questions that remain observationally ambiguous.

## Core rule

Before commissioning a new experiment, ask:

1. What facts already constrain the unknown?
2. Which candidate models remain compatible with those facts?
3. What does each surviving model predict?
4. Can the prediction be calculated from retained data?
5. If several models remain, what is the cheapest discriminator between them?

Prefer a calculated prediction plus one confirmation experiment over a broad exploratory sweep.

## Evidence classes

The audit may consume:

- canonical ROM-derived/generated artifacts;
- deterministic runtime traces and fixtures;
- cross-build structural correspondence;
- WRAM/SRAM symbols and dataflow;
- course/resource manifests;
- graphics/presentation manifests;
- historical TAS/bot observations;
- independent emulator behavior;
- primary/manual/developer historical evidence.

Every inferred result must preserve its input provenance and distinguish:

- **derived invariant** — mechanically follows from already promoted facts;
- **strong prediction** — one model explains all retained evidence but has not yet been directly observed;
- **candidate correlation** — useful pattern requiring a discriminator;
- **external hypothesis** — sourced externally and not yet reproduced locally.

## Phase 0 — knowledge consolidation prerequisite

Use `docs/KNOWLEDGE-CONSOLIDATION-PLAN.md`.

Do not perform a broad inference census against prose fragments. Normalize the main domains first so joins and contradictions are explicit.

## Phase 1 — course-corpus inference audit

Highest-priority initial lane.

### Questions

- Can world extent be calculated for all 45 courses from the header dimension pair?
- Does the proven `coarse_grid = 4 × header_dims` transform hold across the whole corpus?
- Which courses maximize/minimize aspect ratio, fine-record count, resource count, resource reuse, and non-default spatial density?
- Can those extrema define a small principled Widescreen stress corpus?
- What structural quantity predicts the mutable header cursor/trailer distance?
- Do resource-list length, descriptor shape, trailer bytes, or another retained quantity explain the runtime cursor movement?
- Are fine records/resources reused in recognizable families across courses?

### Derived quantities

For each course calculate where supported:

- normalized header dimensions;
- coarse-grid dimensions;
- world extent;
- aspect ratio;
- resource-list length;
- trailer length;
- RNC compression ratio;
- fine-record count where available;
- materialized A000/C000 size where available;
- resource-ID frequency and sequence signatures;
- spawn/landmark coordinates in header and world units.

### Success condition

Produce a ranked set of new invariants/predictions and a minimal representative course set. Each proposed runtime follow-up must exist only because two or more models remain after the static audit.

## Phase 2 — racer/state schema inference

Treat mirrored P1/P2/current-player dataflow as a structural type system.

### Questions

- Can persistent racer fields be reconstructed mechanically from paired marshal operations?
- Which unknown fields form P1/P2 pairs even when their semantics remain unnamed?
- Which shared-current-player addresses act as projections of persistent state?
- Can width, signedness, lifetime and subsystem ownership be inferred from readers/writers?
- Which historical TAS/bot labels conflict with promoted runtime semantics?

### Method

Build relation tuples:

`(persistent P1, persistent P2, shared working, width, direction, readers, writers)`

Anchor known fields such as position, velocity, boost, pitch and angular velocity, then cluster unknown fields by the same structural behavior.

### Stop rule

Do not assign a semantic name merely because an address is paired. Unknown-but-structured is an acceptable result.

## Phase 3 — code-semantic graph inference

Use the comparative structural census and named symbols as a graph.

### Questions

- Which unnamed regions are strongly associated with known subsystems by callers/callees and state touched?
- Which regional edits isolate incidental normalization/presentation code from conserved simulation?
- Which structural islands now connect into larger causal services?
- Can likely semantic roles be ranked without new disassembly?

### Features

- call-graph neighborhood;
- WRAM/SRAM fields touched;
- referenced data tables;
- execution phase;
- regional/prototype conservation;
- proximity to named routines;
- fixture coverage;
- structural-island membership.

Output candidate roles with evidence, never silent promotion.

## Phase 4 — graphics/presentation differential inference

Treat the recovered racer frame records and OAM output as a constraint system.

Compare many frame records against known OAM changes to infer packed-word fields:

- tile identity;
- X/Y offsets;
- flip/attribute bits;
- piece count/layout;
- frame-family relationships.

Prefer natural animation-state differences over instruction-by-instruction decoding where the data itself identifies the encoding.

## Phase 5 — progression prediction

Construct the expected transformation:

`race/result state → medal cell/value → derived tier → checksum-valid SRAM`

before obtaining the final game-authored progression acceptance fixture.

The runtime fixture should then test an exact predicted logical delta rather than merely proving that some SRAM byte changed.

## Phase 6 — renderer/preparation synthesis

After the active preparation/emission lane closes, join:

`course cell/resource → camera/window → preparation queue → VRAM destination → emitted layer/OBJ → framebuffer`

Calculate preparation distance/horizon from retained queue events and camera position. Use that model to predict the minimum earlier-preparation requirement for Widescreen margins while preserving authoritative activation.

## Reporting

Create `analysis/generated/inference-audit.{json,md}` when the first audit runs.

Each finding should include:

- id;
- question;
- input facts;
- derivation/model;
- prediction or invariant;
- confidence class;
- falsifier;
- cheapest confirmation, if any;
- affected product decision.

## Admission rule for new runtime work

A new experiment from this lane must identify:

- the competing models that survived inference;
- the exact observation that separates them;
- why retained evidence cannot already decide it;
- stop condition.

Do not run broad sweeps merely because instrumentation exists.

## Initial execution order

1. Consolidate knowledge surfaces.
2. Audit all 45 courses and choose a minimal stress corpus.
3. Audit racer P1/P2/shared relations.
4. Build code-semantic graph joins.
5. Extend presentation-frame differential analysis.
6. Add progression prediction.
7. Join course/preparation/render evidence once the active preparation lane lands.
