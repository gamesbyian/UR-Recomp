# LLE-only analyzer variants: 80:91DC M1X0 and 80:94EB M1X0

SNESRecomp reconnaissance retained two exact variants as LLE-only:

1. `80:91DC M1X0` — unproven call continuation at `80:886D -> 83:8AF7`
2. `80:94EB M1X0` — unproven call continuation at `80:94F4 -> 80:C3AB`

Static disassembly plus the recovered frontend command grammar explains both control-flow ambiguities.

## 83:8AF7 is a cartridge/memory self-test with a fatal tail exit

The call from the main initialization path is:

```
80:886D  JSL 83:8AF7
80:8871  JSR 80:8C4E
```

The callee performs a destructive probe while preserving the original first byte:

```
83:8AF7  PHP
83:8AFA  LDA 77:0000
83:8AFE  PHA
83:8AFF  LDA #$12
83:8B01  STA 77:0000
83:8B05  REP #$20
83:8B07  LDA #$3456
83:8B0A  STA 77:1FFF
83:8B0E  SEP #$20
83:8B10  LDA 77:0000
83:8B14  CMP #$34
83:8B16  BEQ 83:8B1C
83:8B18  JMP 80:94EB
83:8B1C  PLA
83:8B1D  STA 77:0000
83:8B21  PLP
83:8B22  RTL
```

The write to `77:1FFF` causing `77:0000 == 0x34` establishes the expected mirroring/availability condition. If the probe succeeds, the routine restores the original byte and returns normally. If it fails, it deliberately **does not return**: it tail-jumps to the fatal path at `80:94EB`.

This is why a simple analyzer expecting a single proved callee exit cannot prove the continuation at `80:8871`. Semantically, the continuation is valid precisely on the self-test success branch.

## 80:94EB is the "game pak not found" fatal screen

The failure target begins:

```
80:94EB  LDA #$04
80:94ED  JSL 83:8B51
80:94F1  LDX #$9505
80:94F4  JSR 80:C3AB
80:94F7  JSR 80:FAC9
...
```

The byte stream at `80:9505` decodes as:

- `F9 07` — set text/tile attribute selector;
- `FC 0E` — centered-position control;
- ASCII-like text `game_pak_not_found`;
- `FF` — terminate/return.

All control bytes in this stream are now mechanically mapped in `analysis/generated/frontend-text-command-dispatch.md`. None can escape the interpreter into an unknown target:

- `F9 -> 80:C546`, then continue;
- `FC -> 80:C4A7`, then continue;
- `FF -> 80:C440`, restoring parser state and `RTS`.

Therefore the call at `80:94F4` has a normal return to `80:94F7` for this concrete stream. The earlier analyzer proof gap came from the unresolved generic `JMP ($005D)` inside `80:C3AB`, not from an actual ambiguous runtime destination in the fatal-screen stream.

## Disposition

These two variants remain useful examples of analyzer conservatism, but they are no longer semantic unknowns:

- `80:91DC M1X0`: initialization path with a cartridge/memory self-test whose failure branch intentionally tail-jumps to a fatal screen;
- `80:94EB M1X0`: fatal "game pak not found" presentation path whose concrete text stream returns normally through the now-bounded frontend interpreter.

Do not spend runtime-tracing budget on these variants unless improving SNESRecomp's static proof engine itself becomes a product priority. They do not block faithful execution or current semantic mapping.
