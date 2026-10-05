# Modern Challenge Tier Policy

Modern challenge selection is a product-layer choice over already-proven stock tiers. It does not redefine race timing, opponents, qualification rules, endings, secret unlocks or stock medal semantics.

## Proven stock mapping

Retained runtime/static evidence establishes:

- medal value `0` selects the Bronze challenge and BRONSEN on ordinary tours;
- medal value `1` selects Silver and SILVIA;
- medal value `2` selects Gold and GOLDWYN;
- Hunter (tour row 8) uses ANTI-UNI;
- medal values persist as `0 none / 1 bronze / 2 silver / 3 gold`;
- stock medal award increments the current medal by exactly one, saturating at 3;
- stock tour confirmation snapshots the active medal generation into SRAM `0x10D1`;
- the persistent medal matrix is checksum-protected.

Evidence owners:
- `analysis/generated/tier-opponent-probe.json`;
- `analysis/generated/sram-medal-progression-static-model-2026-10-01.md`;
- `analysis/generated/progression-sram-semantics.json`;
- `analysis/generated/tour-award-ending-probe.json`.

## Settled Modern policy

For an available ordinary tour, Modern may let the player select Bronze, Silver or Gold directly. Canonical opponents and challenge semantics remain tied to those exact stock tiers. Completing a selected higher tier records that tier and therefore satisfies all lower tiers. Replaying a lower/equal tier never reduces recorded completion.

Authentic mode remains stock-sequential: medal generation advances at most one step per successful stock award.

Hunter remains discovery content and canonical Gold-only once legitimately available. The retained stock probe shows a GOLD label and ANTI-UNI regardless of Hunter medal state, so Modern does not invent Bronze/Silver Hunter variants. This policy does not expose Hunter eligibility requirements or create a checklist for secret progression.

`native/product/modern_challenge_tier_policy.hpp` encodes only this semantic algebra. It has no SRAM/WRAM or runtime write interface.

`native/product/modern_challenge_tier_selector.hpp` turns that policy into a host-navigation-ready selector without duplicating progression rules in UI code. Ordinary tours expose Bronze/Silver/Gold and default to the next stock-sequential tier (or Gold once already complete). Hunter collapses to one Gold choice. Authentic, unavailable tours and invalid medal state expose no selector.

## Required runtime adapter before shipping selection

A player-facing selector is **not yet authorized to launch a non-current tier**.

For ordinary tours, stock derives the opponent/challenge generation from the medal currently held. Therefore selecting Gold while the persistent medal is 0 requires a narrow validated runtime seam that can present generation 2 to the stock challenge initializer without pretending the profile already owns Silver.

The adapter must satisfy all of these constraints:

1. persistent medal/checksum state is not pre-granted merely to select a challenge;
2. the stock race initializer sees the selected canonical generation and produces the exact canonical opponent/threshold behavior;
3. failure leaves persistent completion unchanged;
4. successful completion commits `max(previous_medal, selected_tier)`;
5. the persistent medal checksum remains stock-valid and survives fresh-process reload;
6. Gold completion still dispatches the stock tour-specific gold vignette/ending behavior where applicable;
7. Authentic mode cannot invoke the adapter;
8. Hunter secret eligibility/ending behavior is preserved rather than bypassed;
9. no general arbitrary SRAM/WRAM writer is exposed to product UI.

The preferred implementation shape is a title-owned typed challenge adapter with the smallest possible input/output vocabulary, analogous to the existing tour-resume adapter. It should own all concrete stock addresses and checksum mechanics. Generic product policy should see only tier/opponent/completion semantics.

## Cheapest next discriminator

Do not reopen generic progression archaeology. The missing question is narrow:

**Which smallest stock-owned state/input boundary can substitute the selected medal generation for race setup while leaving persistent medal ownership unchanged until a successful award?**

Start from the already-proven tour-confirm medal snapshot and opponent-selection path. A useful discriminator must compare a stock Silver/Gold initialized race against a Modern-selected equivalent and identify the minimum state that must differ. Once that seam is proven, build the typed adapter and fresh-process medal/checksum acceptance around it.

Until then, the policy/model is ready but player-facing non-current-tier selection remains blocked by this one adapter seam.
