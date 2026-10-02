# Gameplay object activation vs presentation — static boundary

Date: 2026-10-01  
Scope: Dragster checkpoint/finish resource family only

## Result

The gameplay-activation path and the camera-driven presentation/update path are
mechanically distinct before any new runtime instrumentation is added.

For the representative checkpoint/finish family, the authoritative behavior
cells are present in the course runtime plane before the active race. They are
not activated by entering the camera window. Activation is selected from the
current player's collision/contact state inside the racer simulation pass.

The camera-filtered `$0DCD/$0DCF` lists are a separate VRAM-update mechanism
and must not be widened or repurposed as gameplay liveness state.

## Authoritative existence

Dragster resource `0x24` owns `7E:C000[6..14]`. All nine bytes are
`0x14`, and object code `0x14` dispatches to
`Race_HandleCheckpointFinish` at USA `81:8050`.

The same resource iteration that selects `0x24` performs its VRAM DMA before
materializing the paired runtime planes:

1. `82:E1D9..` reads the next course resource ID.
2. `82:E216..` configures DMA to `$2118` with VRAM destination through
   `$2116`.
3. `82:E307..` uses that same resource ID to select the bank-17 runtime
   materialization source.
4. `82:E342` writes the resource's A-plane contribution to `7E:A000+`.
5. `82:E37C` writes the resource's behavior contribution to `7E:C000+`.

Thus resource-level graphics preparation and authoritative behavior
materialization happen during course load, before later camera-edge visibility
decisions. This does **not** yet identify which loaded graphic cells correspond
visually to each of the nine `0x14` behavior cells.

## Gameplay activation boundary

The active racer update calls the course-object dispatcher from inside gameplay
simulation:

- P1: `82:8C32 -> 81:82E2`;
- P2: `82:911C -> 81:82E2`.

The dispatcher at `81:82E6`:

1. gates on current-player state `$0EE7`;
2. derives an object index solely from `$0F09`;
3. reads `7E:C000,X`;
4. masks bit 0 and dispatches through `81:8320`;
5. sends code `0x14` to `81:8050`.

The relevant index expression is:

```
index = (($0F09 & $03F0) >> 2) + (($0F09 & $000F) >> 1)
```

`$0F09` is current-player collision/contact state. P1 marshaling begins from
persistent collision state at `81:8D48..8D4B`, while the collision resolver at
`81:8FB8..` clears and reconstructs it from gathered collision candidates.
For example, `81:903A..9040` and `81:9065..906A` copy candidate words from
`$0260` into `$0F09`. The resolved value is persisted back for P1 at
`81:8DF3..8DF6`.

No camera position, camera edge, `$0DCD/$0DCF` count, or VRAM-update-list
state participates in the `81:82E6` activation decision.

## Presentation/update boundary

The camera-derived update mechanism has different inputs, storage and consumer:

- `81:AA40..` uses camera-window edge state including `$0505/$050D` and
  camera velocity `$04F5` to filter compact update lists;
- list counts are `$0DCD/$0DCF`, with flags at `$0D6D/$0D7D` and encoded
  VRAM words at `$0D8D/$0DAD`;
- `82:D383..D3C4` consumes those lists by writing the encoded words to
  `$2116` and values selected from `$7E2132` to `$2118`.

That is a presentation/preparation path. It does not read the C000 behavior
plane and is not the checkpoint/finish activation gate.

## Current Widescreen constraint

A safe Widescreen implementation must preserve the collision/contact domain that
feeds `$0F09 -> 81:82E6 -> 7E:C000` independently of any widened camera or
render rectangle.

The camera/window and VRAM-update domain may eventually be widened for
presentation, but doing so must not cause new C000 object codes to be selected
or dispatched.

## Remaining discriminator

The existing deterministic Dragster finish route is being sampled around one
actual checkpoint/finish progression. The runtime pass must still localize:

- the behavior-event frame;
- camera position at that event;
- direct VRAM-update activity around it;
- the representative feature's visible boundary crossing.

Do not infer an object-specific draw/visibility relation from the resource-level
VRAM DMA alone. The dynamic pass exists specifically to close that final gap.
