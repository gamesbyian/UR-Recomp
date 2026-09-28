# Progression, SRAM and results

## Historical SRAM structure

TAS research reports nine 16-byte tour medal blocks:

- Crawler: `0x069C-0x06AB`;
- Jumper: `0x06AC-0x06BB`;
- Shuffler: `0x06BC-0x06CB`;
- Bounder: `0x06CC-0x06DB`;
- Walker: `0x06DC-0x06EB`;
- Runner: `0x06EC-0x06FB`;
- Hopper: `0x06FC-0x070B`;
- Sprinter: `0x070C-0x071B`;
- Hunter: `0x071C-0x072B`.

The historical interpretation is one byte per unicycle, with:

- `00`: no medal;
- `01`: bronze;
- `02`: silver;
- `03`: gold.

Tour unlock state is reported around `0x10D3-0x10E2`.

RetroAchievements independently corroborates the medal-region pattern and exposes additional stunt/result/progression addresses.

## Important ordering clue

The tour order above is not the same as some earlier provisional player-facing track ordering used during course-stream naming.

That means "tour order" is not yet one globally safe concept.

When linking:

- UI tour order;
- SRAM block order;
- runtime currentTrack IDs;
- RNC stream order;
- human course names;

record the exact mapping rather than assuming they all share one enumeration.

## Validation opportunity

The clean/hacked 8 KiB SRAM files from Halamantariel's old directory remain missing, but we can reconstruct equivalent experiments ourselves.

A useful controlled save experiment is:

1. start from a known clean SRAM;
2. change exactly one medal/result;
3. diff SRAM;
4. repeat across tours/unicycles;
5. compare with historical offsets and RetroAchievements conditions.

This would turn the old layout from historical evidence into local confirmation.

## Port requirement

Stock save/progression behavior is part of authoritative gameplay state.

Any modern save UX may wrap or expose it, but it must not silently reinterpret medal values, unlock conditions or result semantics.
