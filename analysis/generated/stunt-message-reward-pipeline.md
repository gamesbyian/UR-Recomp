# Stunt message reward pipeline

This compact static analysis closes three open questions from the recovered Nitrodon/Dessyreqt material without adding runtime capture cost.

## 1. The 625-byte response table is a binary praise gate

`Stunt_FinalizeAndScoreAirTricks` builds the exact base-5 index

`125*flips + 25*rolls + 5*twists + zflips`

and loads `82:9DAA[index]` at `02:9D22`. The loaded byte is masked to 8 bits and compared only with `0xFE` at `02:9D29`.

- `FE` branches directly to cleanup at `02:9D68`.
- Every non-`FE` byte follows the same praise path.
- The response-table byte is never used again on that path.
- A full bank-82 listing scan finds no second `$829DAA` reference.
- `FF` therefore has no separate runtime meaning in this consumer. It belongs to the same allow-praise class as the other non-`FE` bytes.

The praise IDs themselves are computed after the gate from racer/course state and `$A5 & 0x0F`.

## 2. Message consumption is the delayed stunt-reward boundary

`01:C5AF HUD_QueueMessage` only enqueues. The later bank-81 consumer applies score and boost rewards.

P1 path `81:C0E8..C225`:
- pops from `7E:0CBB+`;
- adds its score reward to `77:07BB` at `C13D-C141`;
- indexes signed word table `81:C4AA` by `message_id - 1`;
- if the table value is nonnegative, adds it directly to persistent boost `7E:11CF` at `C16D-C171`.

P2 path `81:C228..C369` mirrors this:
- pops from `7E:0CE5+`;
- adds score to `77:0825` at `C282-C286`;
- applies the same boost table directly to `7E:11D1` at `C2B0-C2B4`.

This explains the delayed boost accounting used by Dessyreqt's later bot: trick recognition and message enqueue happen first, while the persistent reward lands when the queued message is consumed.

## 3. `7E:12AF` is a score display cache

At `81:C37F`, bank 81 loads `77:07BB`, compares it with `7E:12AF`, and stores a changed value to `12AF`. The following code decomposes that cached value into decimal display digits. Thus:

- `77:07BB`: P1 stunt-track score backing word.
- `77:0825`: P2 stunt-track score backing word.
- `7E:12AF`: P1 score display cache, not the underlying accumulator.

## Stopping condition

These static paths are direct and symmetric, so a new runtime trace would not change the current semantic classification. Dynamic work is only warranted if exact player-visible boost units, auxiliary reward words, or a concrete fidelity discrepancy becomes important.
