# Uniracers SPC archaeology

Recovered/analyzed: 2026-09-29

## Provenance

The public Zophar Uniracers SPC archive was acquired transiently from:

- page: `https://www.zophar.net/music/nintendo-snes-spc/uniracers`
- archive URL: `https://fi.zophar.net/soundfiles/nintendo-snes-spc/uniracers/Uniracers%20%28EMU%29.zophar.zip`
- archive size: 491,821 bytes
- archive SHA-256: `85a3f00cfe46cddd18caa714374ef54da6835f0d293557ce499de352b8d4fdb0`

The archive contains ten valid SPC snapshots. Their ID666 tags consistently identify the game as `Uniracers` and the dumper as `KungFuFurby`, including `Unused Song 1` and `Unused Song 2`.

The source archive is **not redistributed in this repository**. The underlying game audio remains copyrighted; the public URL, archive hash, per-track hashes and derived structural measurements are sufficient to reproduce the analysis without turning this repository into another soundtrack mirror.

Durable machine-readable result:

- `analysis/generated/uniracers-spc-summary.json`

Reusable analyzer:

- `tools/analyze_spc_set.py`

## Strong structural findings

Across all ten snapshots, 20,109 of 65,536 APU RAM bytes are identical, or 30.6839%.

Two common regions dominate:

| APU range | Length | Evidence-backed interpretation |
| --- | ---: | --- |
| `$03D5-$1527` | 4,435 bytes | Strong audio-driver/code candidate. Every captured SPC program counter lies inside this byte-identical region. |
| `$3000-$5F87` | 12,168 bytes | Beginning of a shared BRR sample bank. Every snapshot points DSP DIR to `$FF00`; valid sample data begins at `$3000`. |

Neither large region occurs verbatim in the canonical USA ROM (SHA-256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`). That makes a simple raw-ROM blob hypothesis unlikely and points the next investigation toward CPU-side APU upload, packing, decompression or reconstruction.

## Unused-song families

### Unused Song 1

`Unused Song 1` is strongly aligned with the Demo Race state:

- 87.4512% of APU RAM bytes match Demo Race;
- it has 19 valid BRR samples;
- all 19 sample payloads are present in Demo Race;
- all 19 occur at the same sample indices in Demo Race;
- only 11 of those indices match the five-numbered-race consensus bank.

That is strong evidence for a demo-side audio family, not just a generic similarity.

### Unused Song 2

`Unused Song 2` is strongly aligned with the numbered-race family:

- it has 24 valid BRR samples;
- all 24 appear at the same indices in every numbered race snapshot;
- 24 of its samples match the 30-sample same-index consensus shared by all five numbered races;
- whole-APU-RAM identity is 88.7619%-88.9587% against the five numbered race tracks.

This makes it a strong race-family composition candidate.

## What this does not yet establish

The SPC snapshots do not by themselves identify:

- the SNES CPU-side upload/decompression routine;
- the ROM-side song or instrument tables;
- which selector values correspond to the two unused compositions;
- whether either unused song is referenced by dormant retail code, data, debug paths or only by otherwise unreachable table entries.

Those are now the useful next discriminators. The compact SPC fingerprints give local tests something precise to hunt for rather than treating the soundtrack as an opaque asset blob.
