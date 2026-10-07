# Modern Results Navigation Contract

Status: bounded Windows x64 implementation contract; production wiring is carried by PR #698 and remains gated on its dedicated native acceptance before `main` can claim the slice.

## Purpose

Close the remaining fast-navigation gap between preserved stock results and the existing Modern task surfaces without creating another progression, course-selection, restart, or menu-routing authority.

The product already has one-action Rematch / Repeat Practice, profile-scoped Recent Course, a validated Quick Practice launcher, and a uniquely derivable Next Event route for four-of-five tour rows. Stock tour results already return to TRACK_SELECT. This contract defines the remaining explicit **Track Select** and **Tour Select** results actions and the conditions under which **Next Event** may be surfaced there.

## Authority

Modern results navigation is presentation and routing policy only.

- The guest remains authoritative for stock results, qualification, tour state, rider state, course identity, SRAM and progression.
- Existing Tour continuation / Next Event derivation remains the only source for a uniquely derivable next event.
- Existing stock-menu routing remains the only route back through TRACK_SELECT / TOUR_SELECT.
- Existing Rematch / Repeat Practice continues to use the accepted Restart lifecycle.
- Existing Quick Practice routing remains isolated and is not reused as a progression shortcut.
- Authentic mode renders and accepts none of these Modern actions.

No action in this contract writes guest WRAM/SRAM directly, synthesizes qualification, invents event ordering, or creates a second course/tour model.

## Results action model

On a validated Modern stock results surface, build a renderer-neutral action list from current authoritative context.

### Ordinary tour result

Expose:

1. **Next Event** only when the existing continuation source is current and the existing derivation returns exactly one target.
2. **Retry** through the existing results-safe Restart authority.
3. **Track Select** through the accepted stock frontend route to the current tour's TRACK_SELECT.
4. **Tour Select** through the accepted stock frontend route to TOUR_SELECT.
5. **Records** through the existing Modern Records destination.

If Next Event is ambiguous or unavailable, omit it rather than disabling it with invented ordering.

### Quick Practice result

Keep the existing **Repeat Practice** action. Track Select, Tour Select and Next Event are absent because Practice is isolated from profile progression. Existing Records access may remain available.

### Non-tour / unsupported result

Only actions whose existing authority is valid for that surface may appear. Do not infer a tour from course identity alone.

## Routing invariants

Track Select and Tour Select must reuse the same title-owned frontend transition / stock-menu transport already used by continuation and practice routing. They may not jump by writing menu-state bytes.

Before dispatch, snapshot the authoritative result context needed to reject stale actions. A route must fail closed if execution mode changes, the result surface is no longer valid, the active profile changes, the expected tour context no longer matches, or an existing router owns input.

Once routing begins, the owning Modern router consumes its semantic keyboard/controller input until completion, cancellation or failure. It must preserve the repository's established menu-settle timing and bounded observation budget.

Cancellation or route failure returns to the safest already-valid product/frontend surface without altering qualification or durable progression.

## Presentation

Preserve the stock results ritual and indicators. Modern actions are additive host presentation after the result is authoritative.

Keyboard and controller navigation use the existing semantic input map. Do not add controller-brand heuristics or a second key map.

The surface must use the shared Modern overlay-composition contract so logical geometry and glyph density remain stable through configured 1x–4x presentation density.

## Acceptance

PR #698 adds deterministic action/host contracts plus `modern-results-navigation-acceptance.yml`, which builds the real Modern native host and drives the shipping keyboard entry path from authoritative stock results. The route cases cover ambiguous Next Event omission, Track Select settlement, Tour Select settlement with the existing profile-snapshot rollback after the stock rider wipe, unique Next Event through the existing continuation authority, Quick Practice isolation, and Authentic inertness. These are authored merge gates, not claimed passing evidence until CI reports them green.

A production implementation is complete only when deterministic/native evidence proves:

1. a finished ordinary tour race can choose Track Select and reaches the expected stock TRACK_SELECT with unchanged qualification/SRAM;
2. the same result can choose Tour Select and reaches stock TOUR_SELECT without direct guest-state mutation;
3. a valid four-of-five continuation exposes Next Event and launches exactly the derived canonical course through the existing continuation authority;
4. ambiguous continuation omits Next Event;
5. Quick Practice results retain Repeat Practice but never expose progression navigation;
6. stale profile/context and in-flight-router conflicts fail closed;
7. keyboard and mapped controller activation converge on the same typed action;
8. configured 1x and 2x presentation preserve the same action model and logical bounds;
9. Authentic mode is byte-for-byte free of this host-owned results navigation.

## Stop condition

Stop when Track Select and Tour Select are production-wired with the acceptance above and the results surface consumes the existing Next Event authority where uniquely valid. Do not broaden this slice into Local Tournament, generic frontend redesign, new course ordering, or another run/records model.
