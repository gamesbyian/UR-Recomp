# Modern Unfinished-Tour Resume

This document owns the first deliberately narrow Modern-mode continuation path for an unfinished one-player tour. It is a product-layer wrapper around proven stock progression data. It does not redefine medal semantics, race results, rider identity or authoritative simulation.

## Stock facts reused

The implementation relies only on already-promoted progression facts:

- one-player tour mode is battery SRAM byte `0x10AD == 1`;
- the selected P1 rider index is battery SRAM byte `0x0748`, valid for selectable riders `0..15`;
- the selected tour row is the established runtime value at WRAM `0x00D0`, valid for rows `0..8`;
- the active medal generation is the stock medal cell `0x069C + 16*tour + rider`, value `0..3`;
- in-tour qualification progress is exactly five stock bytes at `0x1075 + 5*tour`;
- stock rider confirmation clears all 50 in-tour flag bytes;
- the five flag bytes are outside the stock medal checksum domain.

The runtime rider/tour values are used only after the frontend has reached a semantically settled TRACK_SELECT or results surface. They are not treated as persistent SRAM identity.

## Profile representation

Profile-local cartridge saves use the flat framework-creatable namespace `saves/profile-<profile-id>`. The pinned framework only creates `saves` plus one leaf, so a deeper `saves/profiles/<id>` path is deliberately avoided on first run.\n\nHost profile schema v2 adds one optional unfinished-tour continuation:

- rider index;
- tour row;
- medal value at the start/current generation of that run;
- the five stock qualification flags.

A continuation is valid only when rider, tour and medal are in their proven ranges and exactly one through four flags are set. Zero flags carry no progress. Five flags are not representable as an unfinished continuation because stock owns the award-and-clear transition.

Profile schema v1 remains readable. A v1 profile deterministically migrates in memory with no tour continuation and canonical re-save writes v2.

## Runtime ownership

`native/title/uniracers_tour_resume.{hpp,cpp}` owns all Uniracers addresses and exposes a narrow typed observation/apply boundary. Generic profile persistence does not know SRAM offsets.

`uniracers_modern_host.cpp` loads `host-profile.txt` beside the active Modern profile's isolated `save.srm`. Missing profile metadata begins from typed defaults. A malformed profile metadata file remains read-only for that process so recovery never silently destroys it.

Every settled stock results surface is a Modern autosave boundary. The framework's ordinary `RtlTryWriteSram()` first durably publishes the authoritative profile-local cartridge save, including records, stats and any medal update; the profile metadata is then atomically replaced with an exact 8 KiB SRAM mirror. When one through four qualification flags remain, that same commit carries the unfinished-tour continuation. A completed five-track row carries no continuation because stock has already awarded the medal and cleared the row.

On a later process, a valid active Modern profile with a byte-identical live/persisted SRAM snapshot exposes a compact **F3 Continue Tour** affordance on the settled stock main menu. Continue does not reconstruct guest state. A pure host route reuses the proven stock menu policy and injects only ordinary discrete directional/confirm inputs through the existing deterministic input path:

`MAIN_MENU (D7) -> RIDER_SELECT (3C) -> saved TOUR_SELECT option (6D) -> TRACK_SELECT (F6)`.

The route deliberately stops at TRACK_SELECT and immediately relinquishes input ownership. The player still chooses the next event, and stock race initialization remains untouched. Escape, or controller B/Start while the route is in flight, cancels the host route without changing progression.

Stock rider confirmation is allowed to perform its historical flag wipe unchanged. At TRACK_SELECT, and only there, the existing title adapter may restore the saved five-byte row when all of the following still match:

- Modern mode;
- active profile;
- one-player tour mode;
- rider index;
- tour row;
- medal value;
- current stock row is empty.

A changed medal makes the continuation stale and clears it. A different rider/tour leaves it pending. Existing new progress is never overwritten. Authentic mode never loads or applies Modern continuation metadata.

## Acceptance

The native resume acceptance uses the already-promoted R-2026-10-04-UI-20 state contract rather than pretending that the simple hand-driven first-race script is a qualifying win. It starts from the canonical clean SRAM, seeds the historically proven unfinished Crawler row `11000`, and writes matching schema-v2 profile metadata. No checksum rewrite is needed because the five tour flags are outside the medal checksum domain.

A fresh native process now exercises the player-facing Continue route itself. The host starts at the settled stock main menu, routes through ordinary rider/tour inputs, and must report `UR_TOUR_CONTINUE READY` only after reaching the persisted tour's stock TRACK_SELECT surface. Stock rider confirmation performs its historical 50-byte wipe unchanged. At TRACK_SELECT the host must also report `UR_TOUR_RESUME APPLIED`; that status is emitted only when the current five-byte row is empty immediately before restoration, so it directly proves the stock wipe occurred before the host repair. Acceptance verifies that the process remains out of a race, the runtime tour row is correct, and profile-local `save.srm` contains exactly the five flags recorded in `host-profile.txt`.

The same host-side acceptance trigger runs in a second fresh process under Authentic policy and must leave the game at the stock main menu with no Continue or resume diagnostics. This keeps the new route completely outside Authentic mode.

Separate native result-boundary behavior is exercised by the ordinary product host: every settled stock result durably autosaves full profile-local SRAM. The hand-driven first-race fixture is intentionally not used as a continuation-capture proof because it reaches results without earning a qualifying tour flag.

This remains deliberately narrow. It now removes unnecessary frontend reconstruction for a valid unfinished one-player tour, but does not auto-select an event, change medal thresholds, skip races, create a second campaign model, or generalize to VS/League. The broader task-oriented Modern root, explicit Restart Tour UX, challenge-tier policy and richer controller-facing Continue presentation remain separate product work.
