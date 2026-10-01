# Semantic propagation pass — boost/message pipeline and racer projection — 2026-09-30

This pass follows two high-value semantic anchors that directly affect gameplay fidelity and future widescreen/HD rendering.

## 1. Boost/message/stunt pipeline

### ROM-side queue semantics

The recovered bank-81 disassembly identifies `81:C5B3` as the concrete per-player message enqueue routine.

For player 1 (`Y=0`):
- queue storage begins at `7E:0CBB`;
- `7E:0CE3` is the enqueue/write index;
- `7E:0CE1` is the opposing queue index checked for full/empty separation;
- indices wrap with `AND #$1F`, proving a 32-entry ring.

For player 2:
- queue storage begins at `7E:0CE5`;
- `7E:0D0D` is the enqueue/write index;
- `7E:0D0B` is the opposing index;
- the same 32-entry wrap rule applies.

`81:C609` initializes the two rings. `81:C64E` computes occupancy/distance using the same index pairs.

The stunt finalizer at `82:9A42` calls the long-entry wrapper `81:C5AF` with concrete stunt/result message IDs. Dessyreqt's recovered USJO v14a independently reads the P1 ring at `0CBB/0CE1/0CE3`, walks queued messages, and maps message IDs to delayed boost credit.

### Consequences

1. Dessyreqt's queue-aware boost model is reading the game's actual stunt/HUD message ring, not an unrelated display buffer.
2. Delayed stunt boost and queued stunt feedback are structurally coupled strongly enough that future boost-unit work should trace the queue consumer rather than treating message display and boost as separate systems.
3. `HUD_QueueMessage` can be promoted from “probable queue/render split” to a confirmed per-player ring-buffer enqueue operation.
4. The 32-entry P1/P2 ring structure provides clean deterministic watchpoints for future stunt/boost fixtures.
5. The historical boost values inferred by v14a remain historical evidence until the ROM-side consumer that turns queued messages into boost is locally traced. Do not promote the numeric message→boost mapping as canonical yet.

## 2. Racer OAM/camera projection boundary

`Race_BuildRacerOAMState` at `82:ACA5` exposes a clean boundary between world/simulation coordinates and SNES presentation state.

For player 1 in the ordinary race path:
- vertical projection begins with `Player1_YPosition (0415) - CameraY (041D)`;
- horizontal projection begins with `Player1_XPosition (0411) - CameraX (0419)`;
- horizontal delta is scaled according to `03ED`;
- scaled X is tested against bounds `0421/0423`;
- the unscaled/wrapped X value is masked with `0D49`;
- projected P1 screen X/Y are stored at `1509/150A`;
- offscreen fallback stores `0x70,0x70` and marks `121B=1`;
- facing state `0BA1` contributes sprite attribute bit 6 in `150C`.

Player 2 repeats the same projection from `0413/0417`, using the same camera `0419/041D`, and stores projected X/Y at `150D/150E`; facing `0BA3` contributes the analogous bit in `1510`.

### Consequences for widescreen/HD work

1. `1509` is not merely a generic “screen X” watchpoint; it is the P1 projected screen-X output. `150A` is P1 screen Y, and `150D/150E` are P2 X/Y.
2. The routine cleanly separates:
   - authoritative world position: `0411/0415`, `0413/0417`;
   - camera origin: `0419/041D`;
   - viewport/culling policy: `03ED`, `0421/0423`, mode branches;
   - presentation outputs: `1509/150A/150D/150E`, attribute bytes and OAM high-table state.
3. Future true-widescreen work should preferentially alter or replace viewport/culling/projection policy while leaving world simulation coordinates untouched.
4. `0421/0423` and `03ED` are now priority candidates for semantic naming when widescreen implementation begins, because they directly gate horizontal visibility/scaling. Exact user-facing units remain open.
5. `0D49` participates directly in horizontal projection as a mask; its relationship to track width/wraparound should be reconciled with the course model before naming it more strongly.

## Stop rule

The useful boundary and queue structure are now explicit. Further work should resume when:
- tracing the ROM-side message consumer can close boost units/delayed credit;
- widescreen implementation needs exact meanings of `03ED`, `0421/0423`, or `0D49`;
- a deterministic stunt fixture can cheaply bind message IDs to resulting boost changes.
