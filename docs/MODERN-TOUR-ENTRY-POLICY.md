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
5. only then retire the profile-local continuation metadata.

If the route is cancelled, times out, changes profile/context, enters an unexpected race, or reaches TRACK_SELECT with a non-empty row, the continuation remains intact.

## Acceptance contract

Pure coverage proves:

- Authentic mode exposes neither action;
- invalid/missing/stale continuation context exposes neither action;
- Resume is non-destructive and carries restore permission;
- Restart cannot route until explicitly confirmed;
- all nine tours use the same stock route for confirmed Restart;
- Restart carries no restore permission;
- metadata retirement is permitted only after both settled TRACK_SELECT and an empty stock row;
- Resume never permits Restart-style retirement.

This is deliberately a stacked policy/model slice. Player-facing host wiring remains deferred until the current Continue/navigation host changes are reconciled. The later integration should be thin and should not add another course picker, another frontend router, or direct qualification-byte clearing.
