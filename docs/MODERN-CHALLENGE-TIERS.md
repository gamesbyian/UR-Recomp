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

`native/product/modern_challenge_tier_policy.hpp` encodes only this semantic algebra. It has no SRAM/WRAM or runtime write interface. Forged/out-of-range tier values fail closed: they are not selectable, do not resolve an opponent, and cannot grant completion.

`native/product/modern_challenge_tier_selector.hpp` turns that policy into a host-navigation-ready selector without duplicating progression rules in UI code. Ordinary tours expose Bronze/Silver/Gold and default to the next stock-sequential tier (or Gold once already complete). Hunter collapses to one Gold choice. Authentic, unavailable tours and invalid medal state expose no selector.

## Qualification semantics

The stock result path now closes the remaining qualification question mechanically.

At `83:879A`, stock dispatches the qualifying-result check by `$074B & 3`. Event types 0 and 1 share `83:88D3`, which compares the live result fields `$0769` and `$07D3` and does **not** read either the persistent medal or `0x10D1`. Therefore race/circuit qualification remains stock-owned once the selected generation has produced the canonical opponent/race setup.

Stunt is the one exception. Event type 2 dispatches to `83:88E1`, which calls `83:9EEB`. That routine:

1. computes the active medal cell with `83:9EB4`;
2. reads the checksum-protected persistent medal at `$77:069C,X`;
3. converts completion medal 3 back to challenge generation 2;
4. indexes the 16-bit table at `83:A218` with `3 * tour_row + generation`;
5. returns the numeric `QUALIFY` target.

For Crawler, the stock thresholds are Bronze **68**, Silver **137**, Gold **270**; the retained Bronze result-screen capture displays `QUALIFY : 68`, matching the table exactly.

`native/title/uniracers_challenge_qualification.{hpp,cpp}` now models the only Modern substitution required here. It is write-free and fail-closed. For an ordinary-tour stunt result, it may substitute the selected challenge generation only when rider, tour, 1P mode, expected persistent medal and stock-derived generation all still agree. Hunter and stale/malformed context are rejected. Race/circuit paths need no analogous qualification hook.

The generated/runtime callsite integration for `83:9EEB` remains gated until its execution-tier ownership is proven, just like the `80:E6A2` snapshot writer.

## Completion commit policy

`native/product/modern_challenge_commit_policy.hpp` defines the only product-level circumstances under which a selected tier may request persistent progression. Selection, launch and ordinary race completion are not commit authority by themselves.

A commit plan requires all of the following:

- Modern mode;
- valid prior stock medal and selected tier;
- the selected tier was actually completed;
- the stock tour-award lifecycle boundary was reached.

The plan records the exact previous medal it expects and the resulting canonical medal `max(previous, selected)`. A title adapter must revalidate that expected previous medal before any write; if progression changed underneath the plan, it fails closed. Failure, cancellation, an incomplete tour, a lower/equal replay, invalid input and Authentic mode produce no progression write.

This is policy only. Checksum-covered medal mutation and any derived-tier reconciliation remain title-owned implementation details gated by native/fresh-process acceptance.

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

### Generation snapshot adapter

`native/title/uniracers_challenge_generation.{hpp,cpp}` now implements the typed decision half of that seam. It is designed to sit directly on the stock tour-confirm snapshot writer rather than performing a later SRAM patch.

The adapter receives the generation value stock was about to write plus an optional Modern request. A request names the rider, ordinary tour row, expected persistent medal and selected generation. It applies only when all of these still agree with live stock context:

- one-player tour mode;
- live rider;
- live tour row;
- persistent medal cell;
- stock writer input generation.

On success it returns only the selected generation that the stock snapshot writer should store. It does not itself write SRAM or WRAM. With no request, invalid input, Hunter, stale profile/progression context or a stock-generation mismatch, it returns the original stock generation unchanged.

This shape is important because the retained direct-reference scan localizes the stock snapshot writer at `80:E6BF`, an ordinary opponent consumer at `80:B315` and a frontend generation-label consumer at `80:E8F0`. Substituting at the writer boundary lets downstream stock consumers share one coherent generation instead of repairing label/opponent state afterward.

The generated-code writer hook is now implemented as a fail-closed post-generation patch plus a narrow C bridge. `tools/patch_challenge_generation_writer.py` scans the shipping generated C set and requires exactly one emitted byte store to `$77:10D1`; it wraps only that store's value through `ur_uniracers_challenge_generation_filter()`. Zero or multiple matching stores fail the shipping preparation. The 4:3 regression-baseline generator deliberately does not apply this hook.

The bridge is exact stock pass-through until a typed request is armed. `uniracers_challenge_generation_runtime.cpp` installs a one-shot filter for one stock snapshot writer only. The request is consumed and disarmed whether validation succeeds or fails, and explicit cancellation restores pass-through before the writer. This prevents a stale tier choice from leaking into a later tour confirm.

Player-facing wiring and threshold/result acceptance are still pending. The existence of the writer hook is not by itself authorization for non-current-tier launch.

### Completion/reward constraint

The retained stock award path already closes an important implementation question: at `83:8823..8838` stock reads the persistent medal cell, increments it by exactly one, stores only values up to 3, then the later `83:88FD` dispatch selects ordinary medal presentation versus the per-tour gold vignette / Hunter ending based on the resulting stock progression state.

Therefore a Modern Gold-selected tour begun from persistent medal 0 cannot be implemented as:

1. run Gold semantics using a transient generation;
2. let stock award Bronze `0 -> 1`;
3. rewrite the saved medal to 3 afterward.

That sequence would let the stock reward path observe the wrong generation and can skip the canonical gold vignette/ending. The completion adapter must instead make the **stock-owned award transaction itself resolve to the selected completed tier**, or provide an equivalently narrow hook before the reward dispatch while preserving stock checksum and derived-tier updates. Persistent completion must still remain ungranted before successful tour completion.

This makes completion a separate seam from challenge initialization. The current pure `ModernChallengeCommitPlan` is the host/product authorization boundary only; it is not permission for a post-hoc SRAM edit.

`native/product/modern_challenge_award_policy.hpp` now describes the preferred stock-owned hook contract. Once a commit plan is authorized, the selected completion tier maps to the **effective previous medal that stock should increment**: Bronze → 0, Silver → 1, Gold → 2. The hook must revalidate the actual persisted medal against the commit plan, but it should substitute only the value consumed by the stock award calculation. Stock then remains responsible for storing the resulting 1/2/3 medal, recomputing its checksum, deriving unlock tiers and selecting the canonical medal/gold/ending presentation.

For example, a profile with persistent medal 0 that legitimately completes a selected Gold tour authorizes an effective previous value 2; the stock transaction still performs the authoritative `2 -> 3` award. Until the exact callsite seam is validated, this remains pure policy rather than generated-code authority.

## Cheapest next discriminator

Do not reopen generic progression archaeology. The missing question is narrow:

**Which smallest stock-owned state/input boundary can substitute the selected medal generation for race setup while leaving persistent medal ownership unchanged until a successful award?**

Start from the already-proven tour-confirm medal snapshot and opponent-selection path. A useful discriminator must compare a stock Silver/Gold initialized race against a Modern-selected equivalent and identify the minimum state that must differ. Once that seam is proven, build the typed adapter and fresh-process medal/checksum acceptance around it.

Until then, the policy/model is ready but player-facing non-current-tier selection remains blocked by this one adapter seam.
