# Windows Modern frontend Options entry

Status: native acceptance pending. No new settings schema or renderer is introduced.

At the settled ordinary one-player Modern main menu, **F10** or the remapped **P1 Select** semantic opens the **same Options panel** already used from Modern pause. Keyboard Up/Down, Enter, Left/Right on Volume, and Escape work exactly as on pause. Mapped P1 Up/Down/Left/Right/A/Select/Start/B use the existing GamepadMap bindings rather than assuming physical controller positions. F10 also closes the frontend panel. The title retains its normal main menu underneath. F1 Help now gives the new shortcut alongside Quick Practice, Profiles and Tour Progress.

The panel reuses `g_options_menu`, `activate_options_selection()`, the live framework volume and the shipping settings transactions/persistence; there is no duplicate settings state, input map, image asset or frontend simulation/route implementation.

Admission is restricted to Modern, an unpaused settled `0xD7` main menu, and absence of an active host modal, track/tour route, replay/results route, stock 2P join or frontend transition. The host consumes all player input while the panel is visible using the same held-button release latch that protects Practice and Tour modals. The panel automatically closes if the guest leaves the settled menu or the profile transitions into a different surface. Authentic does not open it. Display changes and settings operations use the same already-shipping Options authority.

The pause-owned Options panel remains untouched. Its renderer is deliberately shared, with a source-context flag selecting a standalone modal on the frontend instead of drawing a second pause menu beneath it. Native acceptance opens F10 from a fresh process, proves panel rendering, navigates to the real framework volume setting and changes it, closes F10 without launching a race, and verifies the same key is inert in Authentic. Unit contracts check admission, mapped semantics, held-input ownership and the shared renderer.

The follow-on Controls slice opens the existing P1 rebind panel via F9 or mapped P1 X from frontend Options, returning to the same Options row without a second binding model (see `docs/MODERN-FRONTEND-CONTROLS.md`).

A full five-destination Modern root remains a separate integration slice. This makes **Options** a real main-menu product surface without forcing Play, Multiplayer or Records through unsupported guest routing or the Records browser's paused-session admission.
