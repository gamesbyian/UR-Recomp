# Research Ledger

Use this for claims about the ROM, formats, routines, RAM, graphics or hardware behavior. Separate observation from interpretation.

## Entry template

### R-000 — Title

**Status:** hypothesis | supported | confirmed | rejected  
**Date:** YYYY-MM-DD  
**Area:** CPU | RAM | PPU | DMA/HDMA | physics | camera | course | compression | UI | audio | other

**Observation:** what was actually observed.  
**Evidence:** addresses, traces, hashes, debugger output, source references or repeatable steps.  
**Interpretation:** what it probably means.  
**Discriminating test:** smallest test distinguishing this from alternatives.  
**Dependencies:** assumptions this relies upon.

---

## Seed leads to verify locally

### R-SEED-001 — Rob Northen Compression

Historical reverse-engineering reports that original DMA developer Mike Dailly identified course/level data as Rob Northen Compression (RNC), and that investigators decompressed course data.

**Action:** independently locate and verify the decompression path in the supported ROM.

### R-SEED-002 — Course structure

Historical work reported block/tile-based course representations and very wide layouts.

**Action:** verify exact units, dimensions and indexing rather than inheriting old terminology.

### R-SEED-003 — OAM/HDMA special behavior

Snes9x has historically carried Uniracers-specific handling related to OAM address behavior during HDMA.

**Action:** test the current SNESRecomp runtime before designing a workaround.


### R-SEED-004 — Copier-sensitive anti-piracy path

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** CPU | other

Andrew Innes states that DMA discovered a behavioral difference between a proper cartridge and their fast copy-device development image and deliberately used it for anti-piracy protection. Mike Dailly independently confirms Magicom/devkit use during Unirally development.

**Evidence:** docs/original-development/SOURCE-INDEX.md entries OD-004 and OD-005.  
**Action:** identify cartridge/copier-sensitive code paths and validate them against a trustworthy reference emulator or hardware model.

### R-SEED-005 — Bespoke DMA SNES framework and SNasm conventions

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** CPU | DMA/HDMA | other

Mike Dailly credits himself with the Uniracers SNES framework/tools, lists SNasm as a bespoke 65816 macro assembler, and stated in 2008 that he had found his old SNES framework source.

**Evidence:** OD-001 through OD-004 in docs/original-development/SOURCE-INDEX.md.  
**Action:** search for surviving framework/tool source and compare recovered code idioms against the ROM before imposing modern assembler conventions.

### R-SEED-006 — Multidimensional unicycle animation corpus

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** PPU | other

Developer recollections describe rendered unicycle graphics with multiple pose dimensions, while Dailly lists dedicated Unicycle Compression and A0-plotter tools.

**Evidence:** OD-001, OD-003, OD-005.  
**Action:** correlate controlled animation states with ROM source ranges and sprite uploads; seek stride/table dimensions rather than assuming a simple linear frame strip.

### R-SEED-007 — 1994-11-29 PAL prototype as differential oracle

**Status:** external artifact identified  
**Date:** 2026-09-28  
**Area:** other

Hidden Palace documents a European prototype from a four-EPROM SHVC-4PV5B-01 development cartridge.

**Evidence:** OD-007.  
**Action:** acquire, hash, normalize, and diff against canonical USA retail at byte, block, pointer-table and disassembly levels.
