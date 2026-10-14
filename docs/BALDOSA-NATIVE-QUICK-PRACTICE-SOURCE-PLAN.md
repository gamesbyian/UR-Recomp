# Baldosa native Quick Practice: source-backed integration boundary

**Status:** Implementation plan only. The shipping Baldosa native root still reports Practice as unavailable. No new product feature, original/native event pass, physical-controller QA, progression unlocking, or release credit is claimed by this document.

## Why this remains a real product gap

The native Modern root is no longer merely a picture: Play and Multiplayer already enter real stock selection, played 1P and paired 2P results have been committed, and Records reopens them in separate Windows game processes. First-user named racer creation, clean-exit launcher restart, and narrowly admitted interrupted first-create recovery are merged. But `tools/baldosa_native_modern_root.cpp::choose()` still includes Practice in the **unavailable destination** branch. Do not mark the five-destination journey complete because this row is painted.

## Reuse these existing authorities exactly

| Existing code | Source-backed responsibility |
| --- | --- |
| `native/product/quick_practice_route.hpp` | `quick_practice_target_for_track(track_id)` maps exactly **0..44** to nine real stock tour options `[0,1,2,3,4,5,6,7,9]` and five per-tour track slots. Reject `track_id >=45`; option 8 is not a shipping tour. Cursor motion and Accept are separate. |
| `native/product/quick_practice_launch.hpp` | `begin_quick_practice_launch` / `advance_quick_practice_launch` own the bounded state machine: `AwaitMain`, `AwaitRider`, `AwaitTour`, `AwaitTrack`, `AwaitNowPlaying`, `AwaitRace`, `Active`. Settle at **60 source observations** on each menu and exhaust after **3,600** if no verified completion. Never infer completion from passing a picker alone. |
| `native/product/quick_practice_input_mask.hpp` | `quick_practice_runner_mask` translates semantic Up/Down/Left/Right/Accept into the product input transport masks, with discrete input validation. No duplicated controller bit mapping. |
| `native/product/quick_practice_catalog.hpp`, `quick_practice_available_selection.hpp` | Canonical course menu and profile-dependent course availability, including locked/unavailable choices. The eventual native picker may not bypass stock/unlock semantics by advertising every track as freely selectable. |
| `native/title/uniracers_course_identity.h` and `.cpp` | `ur_uniracers_identify_course(decoded_course, available_bytes)` matches an **actual decoded** USA course header, accepting ordinals **1..45**, while deliberately ignoring mutable resource cursor bytes 0x0B/0x0C. Return `valid=0` for unknown or short input, never guess from menu cursor. |
| `native/product/uniracers_modern_host.cpp::authoritative_active_track_id` and `::advance_practice_route` | Historical integrated implementation: read stock state, resolve decoded course at bank 7F, advance the same state machine, queue one input, roll back its state on failed transport, and abort when the course is wrong or the route times out. **Reuse policy; do not transplant its separate frontend or old mutable-root assumptions.** |
| `tools/baldosa_native_modern_root.cpp` | The **only** native visible root, source stock handoff and P1/P2 focus owner. The existing `g_stock_target` route currently stops at stock racer selection (`0x3C`); it is not itself a target-aware Practice driver. |
| `tools/baldosa_product_pause_spike.py` | Already stages `native/title/uniracers_course_identity.cpp` with the native result source objects. Prefer this existing symbol/linkage and pinned AOT build, not a new guest-memory course parser. |

## Actual original-source observations needed

* `g_ram[0x009F]`: original visible menu. Current router's known stages are stock MAIN `0xD7`, RIDER `0x3C`, TOUR `0x6D`, TRACK `0xF6`, NOW PLAYING `0x16`; do not advance on frontend guesses.
* `g_ram[0x009B]`: stock selected option, read after menu settling; an Up/Down/Left/Right request must observe a cursor change before advancing.
* `g_ram[0x0313] == 0x01`: original race-in-progress bit. **Necessary but insufficient**: a demo race or wrong course must not satisfy Practice.
* `g_ram + 0x10000`: decoded bank 7F course image, fed to existing `ur_uniracers_identify_course(..., 0x10000)` after race becomes active. Convert returned one-based `course_index` to zero-based track ID; require an exact match to requested target.
* `quick_practice_launch_owns_player_input(state)`: while the source-driven route is pending, P1 gameplay cannot consume the same pad word. Release that host ownership only after the exact source race course is admitted, or after a verified safe abort.

## Minimum implementation slice, in order

1. **Observe without driving.** In the existing Baldosa native per-frame observer, add a *test-gated, read-only* course-ID witness for one stock Play-originated 1P race using the already-linked course decoder. Prove index 1..45 on the exact Windows executable and no course credit on attract/default title frames. Do not promote an unverified decoded-bank assumption into shipping source identity.
2. **Native Practice picker.** Render within the **same shared root painter and P1 physical-edge owner**, using existing Quick Practice catalog/selection policy. Initially admit the smallest course whose stock availability can be independently confirmed; show unsupported/unavailable rows honestly. Preserve Play, 2P Join, Records, Quit and first-racer modals, which already carry production player data.
3. **Target-aware stock route.** From explicit P1 confirmation, instantiate `begin_quick_practice_launch(quick_practice_target_for_track(id))`. Reuse `ur_baldosa_product_queue_stock_menu_input` / established pinned native input bridge, not a second SDL event loop, and advance only on actual menu/cursor/race observations. If transport rejects a command, retry the *same semantic state* under the bounded observation budget. Never inject a new menu selection after host focus has been released.
4. **Safe fail-closed exit.** On timeout, unexpected menu transition, wrong decoded course, or profile authority change, do not say “Practice ready” or blindly reopen the host overlay over a different original guest state. Adapt the existing guest restoration/abort contract from the legacy implementation, with save-root, original profile SRAM and pending input released transactionally. Until this is proven, keep the native route disabled.
5. **Genuine acceptance.** Drive the exact pinned Windows native candidate from visible root → Practice selection → **source-verified target course and GO**, then exercise Pause/Restart and Exit-to-root. Start with one normal stock track and one different tour (Hunter index should not be silently coerced to option 8). Include adversarial wrong-course / demo / missing decoder / input-transport rejection / cancellation / timeout witnesses, and a fresh-process named-profile SRAM check. Use one existing Windows build; do not launch a parallel generic research factory or claim parity from pure unit tests.
6. **Broaden only on successful source proof.** Walk the 45-track catalog with cumulative deterministic fixtures once routing is causal and cleanly abortable; keep regional, unlock and profile-state policies separate from visual polish. Physical controller mapping and original-emulator strict complete-event equivalence remain **independent gates**.

## Non-negotiable invariants

This is **product route integration**, not guest gameplay archaeology, PPU/OAM rendering, new profile storage, or independent release QA. Original 256×224 geometry/7:6 PAR, source menu/camera behavior, canonical typed/raw save authority, scripted vs physical input distinctions and rollback backend remain unchanged. Never credit a menu observation, guessed course ID, synthetic observer, or historical host unit test as an independently accepted complete original/native event.

**First actionable PR:** read-only native course-ID witness integrated into the existing Win32 Play→GO test, with positive and negative source signatures plus a bounded retained log. That eliminates the highest-risk unknown before enabling the Practice root destination.
