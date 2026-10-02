# Camera-demand → prepared VRAM strip → NMI DMA causal contract

Date: 2026-10-02  
Representative fixture: deterministic Dragster race, sustained rightward camera motion  
Evidence run: GitHub Actions run `36966728136`

## Result

The representative camera-driven presentation-preparation boundary is the
descriptor queue built by `81:A52F..A59D` / `81:AB88..ACF9` and consumed
during NMI by `80:87E1 -> 82:D197/D19B..D2D0`.

The older compact `$0DCD/$0DCF` lists are a real static mechanism, but they
remain zero throughout the same moving fixture and are not the active scrolling
transport here.

## Demand

`81:A52F` first updates camera position from camera velocity, including
`$0419 += $04F5`. The camera/window helper then derives edge addresses and
strip counts before `81:A59A` calls `81:AB88`.

For horizontal movement, the recovered state includes:

- current entering-edge VRAM coordinate `$0505`;
- wrapped companion coordinate `$0509`;
- primary/secondary strip counts `$052B/$052F`.

When the derived edge has not advanced, those counts are zero and no horizontal
descriptor is prepared. When the edge advances, the counts partition one
16-word column. At a ring boundary the transfer may split across two
descriptors.

Vertical movement has the mirrored row form through
`$050D/$0511` and `$0533/$0537`, partitioning a 17-word row.

## Prepared/pending state

`81:ACB1` materializes up to eight descriptor slots. For slot `n`:

- ready flag: `$03B9 + 2*n`;
- low-WRAM source: `$0399 + 2*n`;
- byte count: `$03A9 + 2*n`;
- VRAM destination: `$03C9 + 2*n`;
- VMAIN mode: `$03D9 + 2*n`.

Single-view horizontal motion uses slot 2. In steady rightward Dragster motion,
a representative descriptor is:

`source $0433 -> VRAM $0D80, size $0020, VMAIN $0081`.

The destination is exactly `$0C00 + $0505`. With VMAIN `$81`, the 32-byte
payload supplies one 16-word entering column.

## Runtime ordering

Run `36966728136` observed:

- 681 non-empty build events;
- 676 non-empty NMI-consume observations;
- 680 build→consume pairs.

After the fixture reaches steady rightward camera motion, preparation and
consumption occur in the same guest frame. For example, frame 1185 has:

- camera X = 1089;
- camera X velocity = +15;
- entering edge `$0505 = $0180`;
- one ready descriptor in slot 2;
- source `$0433`;
- VRAM destination `$0D80`;
- size `$20` bytes;
- VMAIN `$81`;
- NMI consumption in frame 1185.

The PC-level PPU journal independently observes `82:D276`, the slot-2
consumer's `$2116` write site, 667 times during the bounded run.

## Consumer and hardware emission

NMI reaches the queue via `80:87E1 -> 82:D197 -> 82:D19B`.
The consumer scans the ready flags in reverse slot order. For each ready slot it:

1. clears the ready flag;
2. writes the queued destination to `$2116`;
3. writes the queued low-WRAM source address to DMA channel 0 `$4302`;
4. writes the queued byte count to `$4305`;
5. writes the queued VMAIN mode to `$2115`;
6. triggers channel 0 through `$420B`, streaming the payload to B-bus
   register `$2118`.

This closes the representative runtime chain from camera demand through prepared
state to concrete VRAM emission.

## Preparation horizon / scheduling rule

For the steady rightward Dragster scene, preparation is demand-driven and
edge-strip based rather than multi-frame prefetch:

- camera state is advanced first;
- the entering tilemap edge is derived from that settled camera state;
- one 16-word horizontal column is prepared when that edge advances;
- the descriptor is consumed in the same guest frame's NMI/VBlank;
- the VRAM destination runs as a 32-column ring and wraps cleanly, e.g.
  `$0D9F -> $0D80`.

Thus the authentic representative horizon is the entering ring-buffer strip for
the current camera frame. There is no evidence here of a deeper multi-frame
background-preparation lookahead.

A widened renderer that needs extra horizontal presentation slack should extend
which entering columns are scheduled before NMI, while preserving camera and
authoritative simulation state. The compact `$0DCD/$0DCF` mechanism should
not be used as the primary Widescreen preparation seam for this scene.

## Regression contract

`.github/workflows/preparation-emission-probe.yml` now requires:

- a same-frame positive-X horizontal strip descriptor;
- slot 2 source `$0433`, size `$20`, VMAIN `$81`;
- destination equality `VRAM = $0C00 + $0505`;
- an observed 32-column ring wrap at edge `$0180 -> VRAM $0D80`;
- live execution of the slot-2 hardware consumer at `82:D276`.

This is intentionally a representative causal contract, not a claim that every
presentation family or split-screen mode uses the same slot mix.
