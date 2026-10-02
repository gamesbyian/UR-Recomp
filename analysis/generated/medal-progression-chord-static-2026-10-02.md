# Stock medal-progression controller shortcut

Static recovery identifies a retail-ROM controller shortcut into the ordinary
medal/progression writer.

At USA `83:879A`, the results/progression routine:

1. waits through a controller-polling boundary via `83:A923`;
2. calls `80:D1D7`;
3. `80:D1DB..D1E6` copies hardware joypad registers `$4218/$421A` into
   scratch words `$72/$74`;
4. compares P1's resulting `$72` against `0x2050`;
5. on equality branches directly to `83:881B`, the same medal writer that
   indexes `77:069C`, increments/saturates the medal value, derives unlock
   tiers, and recomputes SRAM checksums.

SNES joypad register bit order decodes `0x2050` as **Select + X + R**.
The project's deterministic 12-bit input grammar represents those same buttons
as `0x004 | 0x200 | 0x800 = 0xA04`.

This is shipped game code reached through ordinary controller input, not a
test-only hook or guest-state poke. It is therefore suitable as a black-box
save/load acceptance trigger if runtime evidence confirms the medal matrix
changes and the resulting SRAM reloads with its checksum intact.

The runtime fixture is `tests/input/medal-progression-chord.script`.


## Runtime disposition

The bounded runtime acceptance reached the intended controller chord but did
not mutate SRAM. In run `36957806366`, the before/after 8 KiB SRAM images were
byte-identical, checksums remained valid, reload was byte-identical, and no
medal/tier change was observed.

Therefore the shortcut is **not** accepted as a medal-winning black-box
trigger in the tested fixture. Retain the recovered static path and bounded
search tooling as evidence, but keep real game-authored medal mutation/reload
acceptance open for a future fixture.
