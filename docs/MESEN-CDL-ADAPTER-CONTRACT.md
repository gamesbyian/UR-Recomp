# Mesen CDL Compatibility Adapter Contract

Status: implementation-ready contract for the Phase 4/tool-interoperability validation item.

## Purpose

The project may eventually consume Mesen coverage in DiztinGUIsh or da65, but Mesen CDL bytes must not be treated as interchangeable with another tool's coverage format by filename or bit resemblance alone. The first adapter must therefore be a small, falsifiable translation with a known execution corpus and explicit loss reporting.

## Ownership boundary

The adapter is analysis tooling only. It must not participate in native execution, authoritative simulation, ROM mutation, Widescreen, HD presentation, or product state.

Inputs:

- one exact ROM fingerprint;
- one Mesen-produced CDL capture for that ROM;
- a manifest naming the bounded execution fixture and covered address ranges.

Outputs:

- normalized per-byte coverage records using project-owned semantic flags;
- an adapter report containing source/ROM hashes, input/output counts, unknown source bits, non-equivalent/lossy mappings, and uncovered ranges;
- optional downstream exports only after normalized validation passes.

No consumer may read raw Mesen CDL directly once the adapter is promoted.

## First validation corpus

Use a deliberately small deterministic fixture rather than a whole-race capture. The corpus must contain bytes independently known to exercise at least:

1. executed CPU code;
2. CPU data reads;
3. CPU data writes where Mesen records them;
4. untouched ROM bytes;
5. a bank/address boundary;
6. any Mesen flag combination that cannot be represented exactly by the first downstream target.

The expected classifications must be established independently from the fixture trace/disassembly, not inferred from the CDL under test.

## Fail-closed rules

The adapter must fail rather than silently translate when:

- the ROM fingerprint differs from the manifest;
- the CDL size/layout is incompatible with the pinned Mesen producer;
- an unknown source flag bit is present;
- an address cannot be mapped unambiguously into the normalized ROM/CPU address model;
- a requested downstream export would discard a semantic flag without recording that loss.

Lossy downstream conversion is allowed only when the normalized report names the lost semantics and the acceptance fixture proves the remaining mapping is intentional.

## Normalized semantics

Do not copy a third-party bit layout into the project API. The initial normalized record should express named booleans/enums such as executed, read-as-data, written, and producer-specific/unknown evidence where those concepts are actually supported by the pinned Mesen format. Add a semantic only after its producer meaning is verified.

ROM file offset and SNES CPU address are separate coordinates. Preserve both when the mapping is known.

## Acceptance

The first promoted adapter is sufficient when an automated test:

1. verifies the exact fixture ROM and CDL fingerprints;
2. translates the bounded corpus deterministically;
3. matches independently established expected classifications byte-for-byte;
4. proves untouched bytes remain untouched;
5. exercises at least one intentionally non-equivalent or lossy downstream case and reports it;
6. rejects one malformed/unknown-bit fixture;
7. emits identical normalized output on repeated runs.

Only after this acceptance should a DiztinGUIsh or da65 exporter be added to `tools/tool_interop.json`.

## Non-goals

This task does not require broad new emulator archaeology, a full-ROM coverage campaign, GUI automation, or making Mesen part of default CI. It establishes whether Mesen CDL evidence can cross the project tool boundary without semantic corruption.
