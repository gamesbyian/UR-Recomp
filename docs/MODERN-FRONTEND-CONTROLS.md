# Modern frontend Controls entry

Status: stacked product slice following the frontend Options entry (#746). Native desktop acceptance required before merge.

At the settled Modern 1P main menu, **F9** opens the existing keyboard P1 Controls/rebinding panel. Controller-only players enter the shipping frontend Options surface with their mapped P1 Select control and press their mapped P1 X control to open Controls. The Options footer names this shortcut. The first-run Help panel also names F9 alongside F10/Select.

Controls is a child of the existing frontend Options surface, not a new controls implementation. Enter/A begins capture for the selected binding, the next key applies through SNESRecomp's live `keybinds_set_button()` and `keybinds_save()`; Delete clears, R resets, and mapped Up/Down/Confirm/Back follow the shipping semantic-control adapter. Escape/mapped Back closes Controls and returns to the same Options row. F10 then closes Options to the stock main menu. A genuine pause-owned Controls panel still closes back to the pause family, with no frontend transition.

The title-owned admission and input boundaries are unchanged: `open_frontend_options()` admits only Modern, unpaused, settled `0xD7` main menu with no overlapping host modal or in-flight stock route. Controls adopts the same source flag and host input-release latch. It automatically closes if the main menu ceases to be settled. Authentic ignores both shortcuts. No guest SRAM, input grammar, tour progression or physics are changed.

Native `run_modern_frontend_controls_acceptance.sh` uses a fresh desktop process to enter Controls via F9, confirms that the real panel is drawn, captures the P1 A binding as the G key and sees authoritative binding/save diagnostics, returns to Options then the guest, and proves the same shortcut is inert in Authentic. Strict host-contract unit tests also pin source admission, no duplicate binding storage, and the frontend/paused renderer distinction.

This does not introduce a new keyboard menu, another gamepad map, or a global controls binding authority.
