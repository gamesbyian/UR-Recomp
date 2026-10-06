# Malformed profile SRAM containment discriminator

Date: 2026-10-06
Target: Windows x64 Modern profiles

## Current seam

The generic profile codec intentionally treats the exact 8 KiB stock SRAM mirror as opaque bytes. `decode_host_profile_state()` validates the hex envelope and exact byte count, but it does not and should not decide whether the contained Uniracers save image is semantically valid. `restore_stock_sram_from_profile()` likewise copies any present 8 KiB snapshot after Modern-policy/profile-id checks.

The runtime authority gate in `uniracers_modern_host.cpp` proves catalog/profile identity and snapshot presence before a racer-bearing Modern profile becomes writable, but that gate does not validate the stock SRAM payload itself.

This leaves the bounded expert-edge question in `WORK-QUEUE.md` precise: malformed-SRAM containment belongs at a title-specific boundary before a profile snapshot acquires live guest/save authority, not in the generic profile codec.

## Next bounded experiment

Use the canonical clean stock SRAM image as the control. Produce single-fault variants that preserve the 8 KiB container while corrupting one independently meaningful stock-save region at a time:

1. checksum/check bytes only;
2. one persisted rider/progression byte without updating its checksum;
3. one medal/qualification byte without updating its checksum;
4. an otherwise valid image with the relevant checksum recomputed, if the recovered checksum semantics permit that construction.

For each variant, launch a fresh Modern process through the ordinary profile activation path and retain:

- pre-launch input SRAM SHA-256;
- whether profile authority was accepted or rejected;
- guest-visible save/reset behavior;
- first settled frontend state;
- post-launch persisted SRAM SHA-256;
- any stock recovery/defaulting behavior;
- whether host profile metadata remained writable;
- a clean-control run from the same build.

## Decision rule

If stock code deterministically rejects/repairs every malformed variant before it can become durable cross-profile corruption, retain that behavior as a native fixture and do not add a second validator.

If a malformed image can silently acquire live/durable authority, add the narrowest title-owned validator/preflight needed to reject that demonstrated class before restore. The generic `HostProfileState` codec must remain byte-opaque.

## Acceptance / stop condition

Close this expert-edge item once deterministic fresh-process evidence proves either:

- stock recovery safely contains the measured malformed classes and a regression fixture guards it; or
- a title-specific preflight rejects the demonstrated unsafe class while preserving valid clean and gameplay-authored SRAM, profile isolation, migration behavior, and complete Authentic inertness.

Do not expand this into generalized SRAM archaeology or duplicate stock progression semantics in host product code.
