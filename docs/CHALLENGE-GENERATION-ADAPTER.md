# Challenge Generation Title Adapter

This file owns the candidate title-level seam for Modern direct Bronze/Silver/Gold challenge selection on ordinary tours.

It is intentionally **not wired into the product host yet**. Runtime evidence has shown that changing the stock tour-confirm generation snapshot at SRAM `0x10D1` after TRACK_SELECT can change the downstream canonical opponent/race generation while leaving the persistent medal cell unchanged. Qualification/result semantics still need acceptance before player-facing use is authorized.

## Distinct values

Do not conflate these two domains:

- **challenge generation**: `0 / 1 / 2` = Bronze / Silver / Gold initialization;
- **persistent completion medal**: `1 / 2 / 3` = Bronze / Silver / Gold completed.

The product policy exposes `challenge_tier_generation()` for the exact conversion. Gold is completion medal 3 but challenge generation 2.

## Adapter authority

`native/title/uniracers_challenge_generation.{hpp,cpp}` owns the concrete stock addresses and may write exactly one byte: SRAM `0x10D1`.

The adapter requires:

- settled stock TRACK_SELECT (`$009F == F6`);
- one-player tour mode;
- ordinary tour row 0..7;
- valid rider 0..15;
- persistent medal cell still equals the caller's expected previous medal;
- stock `0x10D1` snapshot still equals that expected medal, unless the same selected generation was already applied;
- selected generation is only 0..2.

It never writes the checksum-protected medal matrix, tour flags, rider, play mode, WRAM, opponent identity, or derived unlock tiers. Hunter is explicitly rejected because stock Hunter is its own Gold/ANTI-UNI discovery path rather than an ordinary three-generation tour.

## Fail-closed statuses

The adapter distinguishes:

- Applied;
- AlreadySelected;
- InvalidState;
- ContextMismatch;
- MedalMismatch;
- SnapshotMismatch;
- UnsupportedHunter.

Reapplying the same selected generation is idempotent. A stale medal or divergent snapshot cannot be silently overwritten.

## Evidence status

The bounded A/B discriminator has already shown a strong candidate result:

- persistent Crawler/MIKE medal remained 0 and checksum-valid;
- stock tour-confirm snapshot began at generation 0;
- substituting generation 2 caused NOW PLAYING and the actual race to use GOLDWYN / rider 19 with the canonical palette;
- the already-rendered TRACK_SELECT label remained BRONZE.

That establishes `0x10D1` as a downstream ordinary-tour opponent/race-generation input, but does not yet prove qualification thresholds or award behavior. The adapter therefore remains unwired.

## Remaining acceptance before host integration

Before this adapter can back the player-facing selector:

1. close the bounded discriminator's exact zero-frame mutation integrity check;
2. identify whether qualification/target logic consumes the same generation snapshot;
3. prove a selected non-current tier uses canonical result/qualification semantics;
4. prove failure leaves the persistent medal/checksum unchanged;
5. prove successful selected-tier completion can commit the product policy's `max(previous, selected)` result through a separate title-owned checksum-valid completion adapter;
6. prove stock gold vignette/ending behavior and Hunter discovery remain intact;
7. prove Authentic cannot invoke either adapter.

The host must receive only typed tier/generation operations. No raw SRAM address or generic write function is exposed.
