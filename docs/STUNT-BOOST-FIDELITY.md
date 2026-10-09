# Stunt-message boost reward table: cartridge evidence (2026-10-08)

This contract retains a **game-ROM lookup**, not an inferred TAS bot scoring model. The USA consumer at `81:C167` indexes a signed little-endian word at `81:C4AA + 2*(message_id-1)`. P1 rewards are credited to persistent `7E:11CF` and P2 to `7E:11D1` by their bank-81 queued-message consumers. The historical `7E:11CD` is a per-racer *working* value, copied during race update.

## Verification

- `tools/extract_stunt_message_rewards.py` refuses an unrecognized structural block or a ROM whose 282-byte block differs from the existing `stunt-message-pipeline-structure-island.json` fingerprint. It relocates that block through each build's recovered structural map rather than guessing numeric shifts.
- The retained complete 21-entry signed table is `analysis/generated/stunt-message-reward-rom-verification.json`. Project tooling run `37755591934`, job `113239294543`, extracted every row from USA retail, Europe retail, PAL prototype 1994-11-29 and legacy beta. The results were **identical in all four ROMs**. All 17 historical named messages agree exactly; IDs `0x0D/0x0E` contain `-1`, so the nonnegative-reward gate excludes them.
- Unit coverage compares this retained numeric table with fresh extraction from each available original ROM and tests synthetic wrong-hash, truncated, relocated, and contradictory historical aliases. The repository stores no ROM bytes in this evidence artifact.

## Last Lap is queued but excluded from the reward consumer

The preserved message list calls ID `0x0F` **Last Lap** and ID `0x10` **Head Bounce**. All four original ROMs carry a signed boost lookup word **152** for both IDs. That word alone does not make a message eligible for a boost.

The original checkpoint/finish handler may enqueue `0x0F` when the *post-decrement* per-player lap count equals 1 and the low byte of SRAM mode `77:074B` is nonzero (four-build verifier: `tools/extract_last_lap_reward_gate.py`, merged #870). The relevant lap word is `0EF1,Y` for USA/beta, `0EF5,Y` for PAL prototype and `0EFB,Y` for Europe retail.

The original P1 message consumer at USA `81:C10C..C136` (mirrored by P2 at `81:C251..C278`) has an earlier gate: it reads the message-to-stat map at `81:C521 + (ID-1)` and, on `0xFF`, branches directly to the **display-only** path at `81:C1A0`, before reaching the signed boost lookup `81:C167`. For message ID `0x0F`, that map byte is **`0xFF` across all four original builds**, checked against their exact 282-byte data-block SHA-256 fingerprints. Therefore **Last Lap does not credit the apparent 152 units through this queue consumer**. The next per-message enable byte `7E:20F6` is never reached for this ID in that path. This message-consumer `FF` exclusion is a **different lookup table** from the 625-byte stunt-finalizer praise table, whose `FE` suppression rule remains separate. This closes the proposed automatic Last Lap bonus at its actual decision point, without assuming how frequently the message appears in ordinary play.

Evidence and guard: `tools/check_last_lap_consumer_eligibility.py`, `tests/unit/test_check_last_lap_consumer_eligibility.py`, and `analysis/generated/last-lap-consumer-gate-verification.json`. Any other possible source of lap-dependent acceleration would require a **different** code path or a measured original-runtime event.

## Accepted runtime fidelity, after the original ROM lookup

The signed message reward table is independently established across all four original ROMs. Subsequent native/reference experiments have also admitted two separate **behavioral boundaries**. Do not continue to mark their measured portions as historical conjecture.

- **Speed, cap, airborne and edge penalties (R-2026-10-08-PHYS-03, merged #867):** `tools/probe_boost_speed.py` boots both engines from the original SRAM and writes the same one-time **controlled boost seed**. Native matches Snes9x on all reported traces. Under the measured forward-running conditions, settled X speed is `448 + min(meter, 0x180)/2`, with a maximum +24 speed increase per guest frame. The `0x0180` saturation is applied on the **speed read**, yielding the 640 ceiling; the stored meter is not itself capped. The meter drains during airborne as well as grounded motion. The viewport edge/offscreen path deducts 16 meter units per frame when applicable and an offscreen racer loses 3 X-speed units per frame. The retained authority is `analysis/generated/boost-speed-probe.json` and the named bank-82 code; this is **controlled-state** parity rather than an input-earned stunt bonus.
- **Recognized stunt landing rewards (R-2026-10-08-PHYS-04, merged #874):** `tools/probe_stunt_boundary.py` uses *input only* from an original-SRAM fresh boot with a single controlled jump. All six bounded native/reference cases agree frame-for-frame (`analysis/generated/stunt-boundary-probe.json`). R shoulder holds of 22/23 frames reach roll progress 2 without reward; 24/25 reach progress 3 and credit **128** boost at landing. The `7E:11F9` completed-roll count remains zero, so three roll-progress steps cannot be named one completed roll. An A twist hold of 4 frames remains unrewarded; 5 frames commits the Z rotation `7E:0DFD=16` and credits **128** boost. These experiments establish two input-duration reward boundaries without writing guest state.
- **Cross-provenance limit:** the positive base reward magnitude 128 also appears in the direct ROM lookup for messages `0x01` (Roll), `0x09` (Twist) and `0x12` (Z Flip). The admitted stunt samples include queue-write indices and boost transitions but not the full *message ID* observed at each consumer pop. Equal numbers alone do **not** prove which named message credited an individual landing, nor the complete recognition/praise/combo policy.

## QA-07 optional exploratory parity, not yet admitted (2026-10-09)

`tools/probe_stunt_boundary.py` now retains the six accepted R-shoulder and
A-twist cases as its **unchanged default**. Opt-in `--explore` adds seven
L-shoulder holds (20, 22–25, 28, 32 frames) and five simultaneous A+R
holds (4, 5, 22, 24, 25 frames). These are **input hypotheses**, not
asserted thresholds or already-observed results. Each still runs paired
fresh-process original/reference and native from the same SRAM and stock
Jumpover circuit with no guest WRAM writes. These exploratory observations
cannot be counted as 45-second Stunt course completions.

Opt-in `--queue-evidence` additionally reads each engine's **actual P1
32-byte message ring** at `7E:0CBB`, read/write cursors `0CE1/0CE3`,
persistent boost `11CF`, airborne value and X speed for every frame of
the same landing window. It uses the already accepted
`tools/extract_stunt_queue_events.py` validator, rejects missing frames,
invalid queue indices or cross-engine mismatch, and retains the enqueued
message IDs plus net boost increases. Do **not** attribute an increase to
a particular queued message without observing the original consumer pop:
queued IDs, their consumption and concurrent meter drain are distinct.

Example manual diagnostic after staging the existing drivers/binaries:

```sh
python3 tools/probe_stunt_boundary.py --snesref <snesref> \
  --core <snes9x-core> --native <native-executable> \
  --rom <canonical-usa-rom> --work-dir /tmp/qa07-stunts \
  --explore --queue-evidence --json-out /tmp/qa07-stunts.json
```

No new behavioral or original/native comparison result has been promoted by
adding these experiment routes. For an actual mismatch, retain first diverging
guest frame, queue contents/cursors, input mask and original handler PC before
changing the guest physics or stunt finalizer.

## QA-07 trajectory shadow channel: a real coverage omission (2026-10-09)

The admitted six-case R-hold/A-twist capture compares P1 pose, progress,
airtime, boost and queue-write index. It deliberately did not compare
**world position, signed velocity or persisted course contact**. A native
racer could land on a different cell, or begin to drift in speed, while
both engines still awarded identical 128-unit boosts. The existing
91-frame equality and stored fixture hashes would not detect that.

An opt-in `--trajectory-evidence` runs on **the same original/native
128 KiB input-only WRAM dumps**, without changing the six accepted default
cases or their retained hashes. It checks P1 `0411/0415` XY,
`04B7/04BB` signed velocity, `0E95` contact word, angle, airborne
state and boost for **all 91 consecutive frames** of each selected
input/hold case (262..352 relative to original race entry), using
the established `probe_jumpover_fallthrough_native.read_p1` decoder.
It independently records first field/frame disagreement and the exact
sampled `air_time > 0 → 0` transitions for both engines.

A ROM-free synthetic regression retains identical pose/boost readings
while changing only native X, X-speed and course contact at frame +270.
It establishes that the **old summary would have missed** this discrepancy
and the new channel rejects it. The fixture neither proves a real
original/native discrepancy nor attributes a sampled `air_time=0`
transition to a particular surface, collision-PC, stunt reward or
message-consumer pop.

To exercise the previously retained six cases with the new channel:

```sh
python3 tools/probe_stunt_boundary.py --snesref <snesref> \
  --core <snes9x-core> --native <native-executable> \
  --rom <canonical-usa-rom> --work-dir /tmp/qa07-stunt-motion \
  --trajectory-evidence --queue-evidence --json-out /tmp/qa07-stunt-motion.json
```

The optional L-shoulder/simultaneous-A+R hypotheses may also be run
with `--explore`. Capture and compare the first trajectory divergence
**before** asserting that a later equal stunt reward proves physics
parity. The full 45-second timed-Stunt and course-completion gates are
unchanged: no new original/native comparison was executed by this patch.

## Remaining precise discriminators

1. **Stunt semantics beyond the two admitted thresholds:** try L-shoulder flip landings, X/Z-flips and multi-stunt combinations, using the same fresh-boot intervention and per-frame event-relative control. Distinguish transient progress from completed-count fields, queue contents from queue cursors, and delayed boost addition from continuous drain.
2. **Unexplained failures only:** preserve the original's established ground/air boost law, speed cap and viewport penalties. Reopen that family only when a new scenario produces an actual native/reference semantic difference.

Do not rewrite original physics from either the lookup table or high-skill anecdotes. For any future discrepancy, reproduce canonical input-relative state and the controlling branch in the original before adjusting native simulation.
