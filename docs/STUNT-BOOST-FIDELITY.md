# Stunt-message boost reward table: cartridge evidence (2026-10-08)

This contract retains a **game-ROM lookup**, not an inferred TAS bot scoring model. The USA consumer at `81:C167` indexes a signed little-endian word at `81:C4AA + 2*(message_id-1)`. P1 rewards are credited to persistent `7E:11CF` and P2 to `7E:11D1` by their bank-81 queued-message consumers. The historical `7E:11CD` is a per-racer *working* value, copied during race update.

## Verification

- `tools/extract_stunt_message_rewards.py` refuses an unrecognized structural block or a ROM whose 282-byte block differs from the existing `stunt-message-pipeline-structure-island.json` fingerprint. It relocates that block through each build's recovered structural map rather than guessing numeric shifts.
- The retained complete 21-entry signed table is `analysis/generated/stunt-message-reward-rom-verification.json`. Project tooling run `37755591934`, job `113239294543`, extracted every row from USA retail, Europe retail, PAL prototype 1994-11-29 and legacy beta. The results were **identical in all four ROMs**. All 17 historical named messages agree exactly; IDs `0x0D/0x0E` contain `-1`, so the nonnegative-reward gate excludes them.
- Unit coverage compares this retained numeric table with fresh extraction from each available original ROM and tests synthetic wrong-hash, truncated, relocated, and contradictory historical aliases. The repository stores no ROM bytes in this evidence artifact.

## New bounded discriminator: Last Lap message

The retained Nitrodon message list calls ID `0x0F` **Last Lap** and ID `0x10` **Head Bounce**. All four ROMs have signed reward word **152** at both indices; ID `0x11` Tabletop also has 152, while `0x0D` Rollout and `0x0E` Wipeout both have `-1`. Independently, the verified `81:8050` checkpoint/finish path contains a **mode-gated** Last Lap enqueue. When the post-decrement per-player lap count at `7E:0EF1,Y` is exactly 1, it reads the low byte of SRAM play-mode word `77:074B`; if nonzero, it calls the ordinary queue helper with ID `0x0F`. This is the game's race-mode state, **not a newly discovered user option or arbitrary last-lap enable flag**. The hash-checked code and target across all four ROM builds are tested by `tools/extract_last_lap_reward_gate.py`. The separately established queue consumer can assign the message's positive reward, suggesting a possible **last-lap boost award independent of a performed stunt**.

The path still needs a native/reference **runtime** witness: choose an ordinary multi-lap circuit (Crawler Circuit has a scouting route at `tests/input/ui-circuit-result-route.script`), observe a real checkpoint that changes laps, and capture the actual `0x0F` message in the P1/P2 queue plus its later consumer. Read `77:074B` from SRAM, not the 7E WRAM image. Require an attributable change to the matching persistent boost word (`11CF/11D1`), with air state and speed recorded; compare against a mode-appropriate first-lap/no-message observation. The static gate alone does not establish whether the queued message survives any other processing branch or when its reward affects speed. Do not call this a proven player-visible last-lap bonus until that event-relative native/reference witness exists.

## What remains unproven

The cartridge bytes and the P1/P2 queue-consumer code close the **reward magnitude** question. They do not prove the **award timing** or the exact boost-to-speed response under expert play.

The next minimal, event-relative native/Snes9x check should follow one valid stunt from transient `7E:042F` progress and finalization to the first queued stunt message, the subsequent positive `11CF` reward, then the first grounded `04B7` speed response. Record `0545` air time, `0CE1/0CE3` ring indices, and the persistent/working boost pair. Use a matched failed/absent-stunt control, preserve stock 60 Hz guest input cadence, and stop once these event boundaries agree between the ROM oracle and native. Do not infer award timing from a single coarse checkpoint, or normalize the case by writing boost directly unless explicitly labeling a separate controlled-state experiment.

Expert/TAS accounts of offscreen depletion and a 640 speed ceiling remain **external observations** until reproduced as their own matched fixtures. `0x0180` is a separate observed boost clamp, not a substitute for a measured speed cap.
