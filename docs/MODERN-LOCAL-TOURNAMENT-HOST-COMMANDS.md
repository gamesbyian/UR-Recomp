# Modern Local Tournament: explicit host commands

Status: **native Windows product command seam, staged on the live-capture PR #815**, not yet a player-accessible tournament screen. This keeps the original guest's 2P race authority and frontend ownership separate.

## Three bounded UI-to-host operations

The C-compatible interface in `uniracers_modern_host.h` adds:
- `ur_uniracers_modern_local_tournament_create(profile_ids, count, course_ids, count, replace_active)`;
- `ur_uniracers_modern_local_tournament_arm_fixture(fixture_index)`;
- `ur_uniracers_modern_local_tournament_cancel_fixture()`.

Each returns 1 only when successfully applied, 0 on rejection. The functions admit calls only at settled Modern MAIN_MENU, outside active ordinary-2P capture, without a competing joined overlay or Practice session. Authentic stays inert. No function chooses host input devices, navigates stock menus, synthesizes racer results, writes SRAM, or awards points.

Create accepts an **explicit UI-selected roster** of 2–8 currently catalog-authorized Modern profile IDs and a nonempty 1–16 ordinary-Race course pool. The host checks bounded C string inputs before handing them to the already merged canonical coordinator. It uses `mint_local_tournament_token()` to independently generate an unpredictable 128-bit tournament identity through operating-system entropy and persists the canonical schedule under the user data root before the request succeeds. It refuses replacing an active event unless the caller passes the explicit replacement choice; any pending live fixture blocks replacement. The original tournament's verified historical receipts remain isolated by its instance ID.

Arm requires an existing, unfinished selected fixture and uses a **new** OS-minted attempt token to durably persist the pending checkpoint **before** any frontend caller begins the original stock 2P route. This pre-route step binds the requested scheduled opponent profile IDs and course as an *intent*. It does not attest that the scheduled opponents have joined their actual devices or raced. The existing ordinary-2P recorder alone validates both actual confirmed Modern join-overlay participants and the guest-observed authoritative course at real race start, then permits receipt linkage of the actual saved run/sidecar pair only for the retained live attempt. Wrong people/track/course retire/refuse membership without destroying unrelated Multiplayer Records.

Cancel retires only the exact currently pending fixture attempt and is available at the settled Modern frontend. It cannot undo or overwrite an authoritative completed result.

The companion pure C11 ABI and source-authority tests guard these commands and the boundary between front-end selection, actual guest routing, and official saved 2P results. These tests **are not player-visible or native controller tournament acceptance**. Normal UI still must own the create/replace/fixture selection flow, route into established stock 2P, display standings and completion in the original League visual grammar, and pass real Windows fresh-process tournament acceptance. No new guest-mode route, independent matchmaking system or second result database was introduced.
