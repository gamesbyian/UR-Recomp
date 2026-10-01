# Canoe compatibility patch reconstruction

The recovered 295-byte `uniracers_canoe.ips` patch is now mechanically
classified by `tools/analyze_canoe_ips.py` and independently disassembled by
the repository-owned da65 workflow.

Primary evidence:

- patch SHA-256:
  `35b695d9cc0667d09f950a05cb3066ada5f0078a50818bc04d348f5ef4f852cf`;
- successful disassembly run: GitHub Actions `36670381748`;
- source artifact: `reference/imported/patches/uniracers_canoe.ips`;
- permanent semantic test: `tests/unit/test_analyze_canoe_ips.py`;
- active-game oracle: `tools/assert_uniracers_vs_oam_seam.py`.

## What the seven IPS records do

The patch contains seven records.

| ROM offset | CPU address | Mechanical effect |
| --- | --- | --- |
| `0x007FDC` | header | Updates the LoROM checksum complement/checksum to `5D47/A2B8`; they sum to `FFFF`. |
| `0x01534C` | `02:D34C` | Replaces the stock `LDA $1599; STA $2104; RTS` path with `JSL $BF:FF00; RTS`. |
| `0x015714` | `02:D714` | Replaces stock HDMA source setup `STA $4364; STX $4362` with `JSL $BF:FF36`; the trailing `BRA +0` preserves the continuation address. |
| `0x018B16` | `03:8B16` | Changes `BEQ +4` to `BRA +4`, forcing the local return path and bypassing the alternate `JML $8094EB` path. |
| `0x01E8D1` | operand in bank 03 | Redirects a `STA long` target from `7E:2065` to `7F:FFE1`. |
| `0x01EA50` | operand in bank 03 | Redirects a `STA long` target from `7E:2069` to `7F:FFEB`. |
| `0x1FFF00` | `3F:FF00` / mirror `BF:FF00` | Installs the 230-byte replacement OAM/HDMA handler. |

The first record is bookkeeping. The other six change execution or data flow.

## Injected OAM wrapper at BF:FF00

The first injected routine selects behavior from `7E:0DDB`.

When that byte is zero, it preserves the original source write:

`7E:1599 -> $2104 (OAMDATA)`

and then writes a common final byte `$55` to `$2104`.

When `7E:0DDB` is nonzero, it instead rewrites two high-OAM source bytes:

- `7E:20A2 = (7E:20A2 & F0) | 05`;
- `7E:20A3 = (7E:20A3 & 0F) | 50`.

Those values are written back to their original WRAM locations, copied to
`7F:FFF1` and `7F:FFF4`, and written to `$2104`. The routine then performs
the same final `$55` write.

That nibble forcing is structurally significant. A source byte with high
nibble `A` becomes `A5`; a source byte with low nibble `A` becomes `5A`.
The project's independent VS regression observes exactly `$2104 <- $A5` at
scanline 0 and `$2104 <- $5A` at scanline 112 in the unpatched canonical
runtime.

## Injected HDMA setup at BF:FF36

The second routine builds two small HDMA tables in the top of WRAM bank 7F.

Channel 7 is configured as:

- `DMAP7 = $04`;
- `BBAD7 = $00`, so the four-byte transfer group begins at `$2100`;
- table pointer `7F:FFE0`.

The generated table is:

```text
6F  0F 83 0C 01
02  80 83 0C 01
60  0F 83 0C 01
00
```

The four-byte payloads therefore address `$2100..$2103`:
`INIDISP`, `OBSEL`, `OAMADDL`, and `OAMADDH`. Both ordinary payloads
select OAM address `$010C`; in byte-oriented high-OAM terms that is the
`0x218` destination already established by the project for sprites 96-99.
The short middle descriptor changes the first payload byte from `$0F` to
`$80`, i.e. the display-control value differs while the sprite/OAM selection
stays fixed.

The two IPS operand redirects feed existing game writes directly into
`7F:FFE1` and `7F:FFEB`, the first payload byte of the first and third
channel-7 descriptors. The patch therefore reuses live game state to populate
those table entries rather than freezing every value.

Channel 1 is configured as:

- `DMAP1 = $02`;
- table pointer `7F:FFF0`;
- `BBAD1` is deliberately not rewritten by this handler and is inherited
  from the surrounding game setup.

Its table is:

```text
70  55 55
70  55 55
00
```

The OAM wrapper subsequently overwrites `7F:FFF1` and `7F:FFF4`, the first
data byte in each of those two descriptors. Thus the OAM wrapper and HDMA
initializer are two halves of one workaround, not unrelated injected helpers.

## What this establishes

The Canoe patch does not merely skip the problematic active-display OAM
operation. It constructs replacement OAM/HDMA state around the same split-screen
seam:

1. the stock OAM write routine is intercepted;
2. high-OAM bytes are normalized into two phase-specific values and mirrored
   into a synthetic HDMA table;
3. a second HDMA table repeatedly selects the known high-OAM address while
   controlling display state;
4. two stock long stores are retargeted into that synthetic table;
5. a separate conditional path is forced unconditionally.

This strongly corroborates that the historical compatibility problem is the
same raster-time OAM mechanism reproduced by the current VS fixture. It does
not establish that Canoe's workaround is hardware-faithful, and it should not
be copied into the remaster as the desired implementation. The project goal
remains a correct general model of the SNES behavior, with the Canoe patch used
as an independent description of what a constrained emulator needed to
synthesize.

## Cross-emulator model comparison

The source-level comparison now separates three distinct implementation
strategies. Source revisions are recorded so this comparison does not drift
silently with emulator development.

| Implementation | Source revision | Active-display OAM model | Relationship to the VS seam |
| --- | --- | --- | --- |
| Snes9x / project `snesref` | `snes9xgit/snes9x@1bcc369e89f08243e0a462882fb1f3e42e51de3a` | Explicit game-specific HDMA hack. When the Uniracers ROM fix is active and an HDMA channel targets `$2104`, `S9xDoHDMA` forces `PPU.OAMAddr = 0x10C` and `PPU.OAMFlip = 0` immediately before the transfer. Its own comment says this exists because Snes9x does not understand OAM address invalidation. | `REGISTER_2104` maps high-OAM address `0x10C` to byte `0x218` on the first write. The local `snesref` debug patch only journals state; it does not alter this compatibility behavior. |
| MAME | `mamedev/mame@573fd0e2df004e533c560cd04d7dd9166125f772` | Generic but fixed-target workaround. During active display, `write_oam` replaces the requested address with `0x0218`. The source comment explicitly identifies Uniracers and describes the fixed address as an approximation because the real address varies with rendering. | Reproduces the same `0x218` destination without tracking the live sprite pipeline. |
| ares | `ares-emulator/ares@4cb8d92b441557cb6bcaf133c4cbc7f6819b1122` | Dynamic PPU model. Object evaluation/fetch continually updates `latch.oamAddress` with the sprite being processed. Active-display `writeOAM` ignores the normal CPU-selected target and redirects low/high OAM accesses through that live latch. | For high OAM the physical address is `0x200 | (latch.oamAddress >> 2)`; a live sprite index of 96 therefore gives `0x218`. |
| jgenesis | `jsgroth/jgenesis@cc10b2bdd32deb51f1f7a15efa18bae2ba20a41f` | Dynamic PPU model with explicit mid-scanline progression. Before an active-display OAM write it advances sprite evaluation/tile fetch to the current dot, obtains the current sprite index from that state, and writes high OAM at `oam_idx >> 2`. If evaluation found no sprites it deliberately carries the last fetched sprite index; the source explicitly notes that Uniracers VS mode depends on this. | High-array index `24` corresponds to physical byte `0x218`; unlike the fixed-target models, the destination is a consequence of raster-time sprite state. |

The models agree on the concrete Uniracers observation while disagreeing on how
general the rule is. That distinction matters for the remaster:

- Snes9x proves only that forcing the game's HDMA seam to the known address is
  sufficient for its renderer.
- MAME generalizes the same destination to all active-display OAM accesses,
  while labeling the behavior an approximation.
- ares and jgenesis model the address as a by-product of the sprite pipeline.
  Their independently written implementations therefore provide the strongest
  source-level basis for a general solution.
- The recovered Canoe patch is a fourth, orthogonal witness. It explicitly
  selects the same high-OAM destination while synthesizing HDMA/OAM state
  around the game's split-screen seam.

This source comparison does **not** prove which cycle-level details are exact
SNES silicon behavior. It does narrow the implementation target: UR-Recomp
should preserve raster-time sprite-engine state strongly enough that the
Uniracers seam naturally resolves to the observed destination, rather than
embedding the ROM-name/address shortcuts used by Snes9x or MAME.

## Remaining comparison work

The disassembly and source-model comparison items are closed. The source-level
reduction is also explicit in `tools/compare_active_oam_models.py`: sprite
index 96 is the convergence case (`0x218` everywhere), while sprite index 64
is the one-variable discriminator (dynamic models `0x210`, fixed-target
models `0x218`). The next compatibility task is to express that exact
discriminator as a tiny runtime fixture and drive it through the available
cores, without relying on the full Uniracers race. In parallel, resolve the
inherited channel-1 B-bus destination from the stock Canoe setup and determine
which parts of that workaround compensate for Canoe limitations rather than
describing original hardware behavior.
