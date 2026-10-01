# USJO v13 passive recovery dossier

Last updated: 2026-09-30

## Scope and hard boundary

Target artifact: `usjo13.lua`, historically titled **Uniracers Stunts & Jump Optimizer v13**.

Historical URL:

`http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/usjo13.lua`

Internal version 8 is now recovered, so v13 is a **P1 passive delta-recovery target rather than a blocker**. The recovered ancestor already exposes stunt-search logic, RAM accesses, timing assumptions, boost/scoring rules and emulator automation; v13 matters mainly for later changes across five internal revisions.

**Do not contact historical authors, TASers, site owners, forum users, or other people to recover this artifact.** Recovery work is passive-only: public archives, mirrors, indexed code, preserved attachments, caches, repository history, downloadable backup corpora, and already-public artifacts.

## Direct recovery: internal version 8

On 2026-09-30 Olivier Bellemare (Halamantariel) recovered a surviving copy identified in its own header as **February 10th, 2008 (Internal Version 8)**. The exact bytes are preserved at `reference/imported/tas-bots/usjo8.lua`.

- size: 62,406 bytes
- SHA-256: `64b1a26966490a619a6557adee79d6ee0463e534fa2488cf3b5913d55a316ffc`
- Git blob SHA-1: `d78962aae7ca6a63bf94113f68680e730dade3fb`
- authorship: unresolved; Olivier explicitly recalls that he was not the main developer
- immediate value: direct RAM reads, stunt counters, jump/stunt state machine, timing constants, savestate search, boost/speed evaluator and best-input replay

This recovery changes the next action from "find any USJO source" to "mine and locally verify v8." Any future v13 recovery should be diffed against v8 to isolate the later discoveries instead of re-analyzed from zero.

## Strong surviving evidence

### Original Snes9x Lua thread

A February 2008 TASVideos Snes9x Lua-development thread preserves the full expansion of the name:

> Uniracers Stunts & Jump Optimizer v13

The contemporary description says the bot:
- starts from an emulator state immediately before a jump;
- intelligently tries different stunt combinations;
- optimizes for speed;
- replays the best stunt found;
- can record the result into a movie;
- performs in seconds optimization work that took a human hours.

Source:
https://tasvideos.org/Forum/Topics/6539

### Later USJO capability

Dessyreqt's 2011 TASVideos submission says USJO originated with Halamantariel, was improved with Nitrodon, and evolved far enough to beat Uniracers autonomously.

Source:
https://tasvideos.org/3072S

### Contemporary RAM watch anchors

Halamantariel published the following Snes9x watch addresses in the Uniracers research thread:

- `7E:04B7` signed 16-bit speed
- `7E:11CD` unsigned 16-bit boost meter
- `7E:0411` / `7E:0415` unsigned 16-bit X/Y position
- `7E:1509` screen X
- `7E:11FD` flips
- `7E:11F9` rolls
- `7E:0F61` twists
- `7E:042B` Z-flips
- `7E:042F` tabletops

These are useful code-search fingerprints because a renamed or copied descendant may retain the same literal addresses.

Source:
https://tasvideos.org/Forum/Topics/979

## Search pivots

Filename-only search is no longer the primary tactic. Use several overlapping passive-recovery families.

### 1. Exact-title and version-family search

Search:
- `"Uniracers Stunts & Jump Optimizer"`
- `"Stunts & Jump Optimizer"`
- `"Stunts and Jump Optimizer"`
- `USJO Uniracers`
- `usjo1.lua` through `usjo20.lua`
- `usjo*.lua`
- likely archive names such as `usjo.zip`, `uniracers-lua.zip`, `Uniracers (U) [!].zip`

Version 13 strongly implies ancestors; later descendants or renamed copies may also survive.

### 2. Directory/corpus reconstruction

Reconstruct the old obellemare Uniracers directory as a corpus rather than requesting one file. Search for mirrors/backups containing any of:
- `Uniracers.html`
- `usjo13.lua`
- historical SMVs
- SRAM files
- savestates
- `WRs.txt`
- `ZZZ - Realtime Play.smv`

A copied parent directory may survive where individual filename search fails.

### 3. Code-fingerprint search

Use combinations of the known WRAM literals with period Snes9x Lua APIs:
- `0x04B7`, `0x11CD`, `0x0411`, `0x0415`, `0x1509`
- `memory.readword`, `memory.readwordsigned`, `memory.readbyte`
- `joypad.set`
- `savestate.create`, `savestate.save`, `savestate.load`
- `emu.frameadvance`

Prefer multi-fingerprint combinations over any one address, because individual hexadecimal strings are noisy.

### 4. Ancestor/descendant and related-bot archaeology

Compare all surviving Uniracers Lua with the recovered 2014 Dessyreqt bot. Look for:
- identical address constants;
- inherited helper functions;
- stunt names/vocabulary;
- track IDs;
- Snes9x API idioms;
- comments or variable names that may fingerprint the same code lineage.

Do not assume the 2014 bot is a direct USJO descendant, but treat shared unusual code as a discriminator.

### 5. Passive archive surfaces

Prioritize:
- Internet Archive item file lists and bulk collections, not only Wayback URL captures;
- preserved forum attachment directories and database dumps;
- old emulator/TAS Lua-script packs;
- personal-site backup tarballs or mirrors;
- FTP/HTTP directory indexes mirrored by archival projects;
- source-code search engines and Git history;
- abandoned Google Code/SourceForge/project downloads;
- public torrent/index metadata for historic emulator scripting collections.

## Search results recorded 2026-09-30

- Broad public web searches for `usjo13.lua`, plausible earlier versions, the historical URL, and exact RAM fingerprints did not surface v13 before the direct v8 recovery.
- GitHub global code search returned no matches for the exact filename, full title, the strongest RAM-address combinations, or obvious Uniracers/Snes9x Lua fingerprints.
- The original Snes9x Lua thread is therefore currently the strongest surviving primary description of v13 itself.
- The 2011 submission independently confirms that USJO was later extended beyond one-jump optimization into autonomous play.

This is a negative result for the obvious indexed surfaces, not evidence that the file no longer exists anywhere.

## Stopping rule

Use recovered v8 immediately. Keep v13 at P1 passive-only and avoid repeated generic search churn.

A productive recovery pass should add at least one of:
1. a new archive surface or corpus;
2. a previously unknown filename/version/title;
3. a surviving code fragment or derivative;
4. a new directory sibling that improves corpus reconstruction;
5. a stronger code fingerprint.

If a pass adds none of those, return to local reverse engineering and revisit only when a new lead appears.
