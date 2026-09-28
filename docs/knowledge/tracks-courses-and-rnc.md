# Tracks, courses and RNC data

## What is confirmed

Each preserved ROM build contains exactly **45 valid RNC Method 1 streams**.

The project-owned decoder successfully decodes all 45 streams in all four preserved builds and validates both packed and unpacked CRC16 values.

The preserved builds currently show:

- USA retail and the historical GoodSNES-labelled beta: all 45 streams byte-identical;
- USA retail and the 1994-11-29 PAL prototype: all 45 streams byte-identical at the same offsets;
- Europe retail: 38 streams unchanged and seven decoded streams changed.

The seven changed Europe-retail stream ordinals are currently 4, 16, 20, 26, 27, 35 and 36.

The original RNC Method 1 unpacker has been identified structurally in ROM:

- USA / legacy beta: `01:B8F1`;
- Europe retail: `01:B8E2`;
- PAL prototype: `01:B8D1`.

A direct call site exists near USA LoROM `02:B322`, with a small wrapper around `02:B320`.

## Strong current interpretation

**Supported.** The 45-stream corpus is very likely one payload per shipped track/event.

The strongest structural clue is decoded byte offset 2. It equals decimal 45 on exactly nine stream ordinals:

`3, 8, 13, 18, 23, 28, 33, 38, 43`

Those are exactly the third item in each group of five, matching the game's nine 45-second stunt events.

This is much stronger than merely observing "45 streams and 45 tracks": one field also follows the expected event cadence.

## Runtime track IDs

The recovered 2014 bot uses a current-track domain of **0 through 44** at historical working address `7E:00CE`.

Its race/circuit-specific control tables omit exactly these IDs:

`2, 7, 12, 17, 22, 27, 32, 37, 42`

Again, those are exactly the third item in each group of five.

Therefore the runtime track-ID system and the RNC corpus independently expose the same nine-event cadence.

## Important unresolved mapping

A tempting hypothesis is:

```
RNC stream ordinal = currentTrack + 1
```

Do not promote this yet.

The bot and historical SRAM material suggest an internal tour ordering that may differ from the provisional player-facing track-name ordering previously attached to RNC streams. The next runtime loader trace should resolve this cheaply.

## Historical structural leads

Still to verify locally:

- course width reported as 256 tiles;
- decompressed structures described as 64x64 blocks;
- relationship to 8x8 SNES tiles;
- WRAM around `7E:2080` seen in historical course/tilemap work;
- visual layout and collision/physics data can apparently be perturbed independently.

These are useful predictions, not established schema.

## Expected data path

Current working model:

```
selected/current track ID
        |
        v
stream selector / pointer logic
        |
        v
RNC1_Unpack
        |
        v
decompressed course payload in WRAM
        |
        +--> visual / tilemap consumer
        +--> collision / track-contact consumer
        +--> object / hazard / boost consumer
        +--> start / finish / checkpoint semantics
```

The highest-value course experiment is still to select one known track, trace the RNC source and destination, and follow the destination into its first semantic consumers.

See `docs/COURSE-FORMAT.md` for detailed evidence and experiment history.
