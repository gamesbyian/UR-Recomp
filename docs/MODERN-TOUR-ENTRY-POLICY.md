# Modern Tour Entry Policy

This document owns the product policy immediately above unfinished-tour persistence and the stock frontend route. It defines how Modern presents and distinguishes **Resume Tour** and **Restart Tour** without creating a second progression system or granting new guest-memory authority.

## Product decision

When the active authoritative Modern profile has a valid unfinished-tour continuation whose proven source fields still agree with persisted and live stock state, the product may offer:

- **Resume Tour**: route through the stock frontend to the saved tour and permit the existing narrow five-flag restore at TRACK_SELECT;
- **Restart Tour**: require explicit confirmation, route through the exact same stock frontend path, deliberately suppress continuation restoration, and retire the host continuation only after stock rider confirmation has performed its historical qualification-row wipe.

If the profile is missing/non-authoritative, the continuation is absent/stale, or execution is Authentic, neither action exists.

## Ownership boundary

`native/product/modern_tour_entry_policy.hpp` is pure product policy. It does not write SRAM, WRAM, profile files or menu state. It returns only:

- whether Resume/Restart are available;
- whether Restart requires confirmation;
- whether the accepted stock frontend route should run;
- whether TRACK_SELECT restoration is permitted;
- whether the continuation may be retired after a proven stock wipe.

`native/product/modern_tour_continue.hpp` carries that intent through the already-proven stock route. Resume and Restart use identical menu navigation. They differ only at the TRACK_SELECT ownership boundary.

Restart is intentionally not implemented as "clear the five flags." Stock rider confirmation already owns the historical 50-byte wipe. A future thin host integration must therefore:

1. receive a confirmed Restart intent;
2. route through ordinary stock MAIN_MENU -> RIDER_SELECT -> saved TOUR_SELECT -> TRACK_SELECT inputs;
3. suppress the existing Resume restore for that route;
4. observe settled TRACK_SELECT and an empty stock qualification row;
5. ask the title-owned `tour_qualification_row_empty()` predicate for proof of the stock wipe, keeping SRAM offsets out of product code;
6. only then retire the profile-local continuation metadata.

If the route is cancelled, times out, changes profile/context, enters an unexpected race, or reaches TRACK_SELECT with a non-empty row, the continuation remains intact.

## Player-facing action model

`native/product/modern_tour_action_menu.hpp` is the host-agnostic action surface for this policy. It uses the existing `UrModernHostNavigationAction` vocabulary rather than physical keyboard/gamepad bindings.

For a valid unfinished Modern tour it exposes:

1. **Resume Tour**;
2. **Restart Tour**;
3. **Back**.

Restart opens a confirmation state and requires a second explicit confirm. Back cancels confirmation without discarding continuation. The context is revalidated when the second confirm arrives, so a profile/source change while the confirmation is open fails closed. If continuation is absent/stale or execution is Authentic, only Back exists.

The model emits typed `ModernTourEntryIntent` values; it does not route menus, mutate progression or persist anything.

## Acceptance contract

Pure coverage proves:

- Authentic mode exposes neither action;
- invalid/missing/stale continuation context exposes neither action;
- Resume is non-destructive and carries restore permission;
- Restart cannot route until explicitly confirmed;
- all nine tours use the same stock route for confirmed Restart;
- Restart carries no restore permission;
- metadata retirement is permitted only after both settled TRACK_SELECT and an empty stock row;
- the empty-row proof is provided by the title adapter rather than duplicated SRAM offsets in product/UI code;
- Resume never permits Restart-style retirement.

The player-facing Windows x64 integration is now thin and direct. At a valid settled Modern main menu, F3 or mapped semantic controller Y opens the existing action model as a modal Resume Tour / Restart Tour / Back surface. Keyboard Up/Down/Enter/Escape and mapped P1 semantic controller Up/Down/A/B-or-Start feed the same `UrModernHostNavigationAction` model. Restart still requires its second explicit confirmation.

The panel also surfaces the existing challenge-tier state without persisting another progression value: the displayed Bronze/Silver/Gold tier is derived from the continuation's authoritative stock medal through `default_modern_challenge_tier()`. No tier shadow state is introduced.

The host carries the typed Resume/Restart decision through the stock route until the settled TRACK_SELECT boundary. The route reuses the same evidence-backed stock-menu timing as Quick Practice: MAIN, RIDER, TOUR and TRACK must each remain visible for the shared 60-observation settle window before the host emits the corresponding stock input. This prevents first-visible menu bytes from being mistaken for input-ready surfaces and keeps transient frontend race-state bytes from escaping the intended route. Resume alone may invoke the existing five-flag restore. Restart cannot fall through into that restore path: it asks the title-owned `tour_qualification_row_empty()` predicate for proof that stock rider confirmation performed the historical wipe, then retires continuation metadata transactionally. Cancellation, input-transport failure, context loss, timeout, unexpected race entry, a non-empty row, or a failed retirement persistence all preserve the resumable continuation. Restart retirement is published transactionally: the candidate host profile is written before save.srm, and an SRAM-write failure rolls the host profile back to the exact pre-retirement state. Because stock rider confirmation can wipe the live row before TRACK_SELECT, an abort after that destructive boundary restores the existing exact profile SRAM snapshot and persists that rollback before releasing host routing; pre-wipe failures leave live SRAM untouched; this reuses the current profile authority rather than adding another recovery format. Authentic mode never exposes the surface.

Fresh-process native acceptance now drives the actual F3 UI for Resume and confirmed Restart, forces an in-flight cancellation and deterministic input-file failure, and asserts the destructive ordering `TRACK_SELECT ready -> stock reset proven -> continuation retired`.


### Fresh-process frontend source boundary

The persisted continuation source remains strict about the stock in-tour play-mode marker. Native fresh-process evidence shows that by settled stock main menu the live SRAM changes the play-mode byte at `0x10AD` from tour `1` to frontend `0` while preserving rider, medal generation and the five qualification flags; the stock checksum byte also changes. Player-facing Resume/Restart therefore uses a title-owned live-frontend predicate that admits only play mode `0` or `1` with exact continuation identity, while persisted provenance still requires `1`. Other modes remain fail-closed.
