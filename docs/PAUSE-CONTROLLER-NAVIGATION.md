# Pause-menu controller navigation contract

## Current implementation audit

The live desktop host already has most of this slice. `ur_uniracers_modern_system_gamepad_button` maps Start to pause toggle, D-pad Up/Down to the same pause-menu actions used by keyboard Up/Down, A to activation, and B to cancel. Options also accept D-pad Up/Down and A, while B/Start closes a host subview. Button releases are consumed while paused, which prevents a release edge from falling through to guest input.

The remaining gap is therefore deliberately small: normalize these physical bindings behind semantic host navigation actions, add Left/Right adjustment for option rows that support cycling, and prove input ownership/unlatching explicitly. Do not build a second controller subsystem.

## Authority boundary

- Guest controller state remains authoritative for Uniracers simulation.
- While the modern pause UI owns focus, navigation input is consumed by the host product layer and must not leak into the guest input mask.
- Authentic mode remains stock: modern pause/controller policy is inert.
- Existing keyboard navigation remains a control path and must retain equivalent menu semantics.

## Minimal input vocabulary

Use semantic host actions: Up, Down, Left, Right, Confirm, and Back. The SDL3 adapter translates physical keyboard/gamepad events into those actions; title/product state must not depend on SDL button constants.

Up/Down move selection. Left/Right adjust an option where the existing option contract supports cycling. Confirm activates or toggles the selected item. Back leaves a subview or closes the pause surface according to the existing lifecycle.

## Acceptance

Native tests must prove:

1. controller and keyboard actions reach the same host menu transitions;
2. consumed pause-menu controller actions do not change the guest input mask;
3. closing pause returns control cleanly without a stuck or latched guest button;
4. Authentic mode ignores the modern controller-navigation policy;
5. Restart, Options, Quit, Controls and Run Data behavior remains unchanged except for the normalized navigation source;
6. Left/Right only affects option rows with a defined adjustment and fails inertly elsewhere.

## Non-goals

Do not add rebinding, controller glyph selection, hot-plug UX, per-controller persistence, or a frontend redesign in this slice.
