# Modern Unfinished-Tour Resume

This document owns the first deliberately narrow Modern-mode continuation path for an unfinished one-player tour. It is a product-layer wrapper around proven stock progression data. It does not redefine medal semantics, race results, rider identity or authoritative simulation.

## Stock facts reused

The implementation relies only on already-promoted progression facts:

- one-player tour mode is stock SRAM byte `0x10AD == 1`;
- the selected rider index is the established runtime rider value at WRAM `0x017D`, valid for selectable riders `0..15`;
- the selected tour row is the established runtime value at WRAM `0x00D0`, valid for rows `0..8`;
- the active medal generation is the stock medal cell `0x069C + 16*tour + rider`, value `0..3`;
- in-tour qualification progress is exactly five stock bytes at `0x1075 + 5*tour`;
- stock rider confirmation clears all 50 in-tour flag bytes;
- the five flag bytes are outside the stock medal checksum domain.

The runtime rider/tour values are used only after the frontend has reached a semantically settled TRACK_SELECT or results surface. They are not treated as persistent SRAM identity.

## Profile representation

Host profile schema v2 adds one optional unfinished-tour continuation:

- rider index;
- tour row;
- medal value at the start/current generation of that run;
- the five stock qualification flags.

A continuation is valid only when rider, tour and medal are in their proven ranges and exactly one through four flags are set. Zero flags carry no progress. Five flags are not representable as an unfinished continuation because stock owns the award-and-clear transition.

Profile schema v1 remains readable. A v1 profile deterministically migrates in memory with no tour continuation and canonical re-save writes v2.

## Runtime ownership

`native/title/uniracers_tour_resume.{hpp,cpp}` owns all Uniracers addresses and exposes a narrow typed observation/apply boundary. Generic profile persistence does not know SRAM offsets.

`uniracers_modern_host.cpp` loads `host-profile.txt` beside the active Modern profile's isolated `save.srm`. Missing profile metadata begins from typed defaults. A malformed profile metadata file remains read-only for that process so recovery never silently destroys it.

At a settled results or TRACK_SELECT surface, a real unfinished stock flag row is autosaved into the profile metadata together with an exact 8 KiB SRAM mirror. The framework's ordinary `RtlTryWriteSram()` durably publishes the authoritative profile-local cartridge save before the metadata replace is committed.

On a later process, stock rider confirmation is allowed to perform its historical flag wipe unchanged. At TRACK_SELECT, and only there, the host may restore the saved five-byte row when all of the following still match:

- Modern mode;
- active profile;
- one-player tour mode;
- rider index;
- tour row;
- medal value;
- current stock row is empty.

A changed medal makes the continuation stale and clears it. A different rider/tour leaves it pending. Existing new progress is never overwritten. Authentic mode never loads or applies Modern continuation metadata.

## Acceptance

The native acceptance uses the real deterministic first-race route rather than synthesizing a completed result. Process one starts from clean profile-local SRAM, reaches the stock race result, waits until the host reports `UR_TOUR_RESUME CAPTURED`, and verifies a typed continuation was persisted.

Process two starts fresh from the same profile, follows ordinary rider/tour selection, lets stock rider confirmation wipe the in-tour row, and requires `UR_TOUR_RESUME APPLIED` at TRACK_SELECT. The persisted `save.srm` must then contain exactly the five flags recorded in `host-profile.txt`, with between one and four flags set, before the script proceeds into the race.

This is intentionally the smallest resumable-progression feature. It does not auto-navigate the frontend, change medal thresholds, skip races, create a second campaign model, or generalize to VS/League.
