# QA-01: one-execution original Bowl source movie + input + guest memory identity

**Scope: bounded original-USA 2014 evidence, zero accepted complete events.** No controller timing rephase, source ROM/movie edit, guest patch, extra guest build, additional Actions workflow, acceptance ledger update or byte exemption.

## Why this integration is necessary

Two independently verified genuine October 18 workflows established different pieces of the source/event evidence chain:

- [Run 39169304323](https://github.com/gamesbyian/UR-Recomp/actions/runs/39169304323) retained the exact **16 original 2014 movie WRAM/SRAM images** plus the 48 original/native handoff images, with ZIP `c2262b40e43b4e167cbdf291623b0e34207561187e103af39eca7a46fa4b0edc`. Its original 78-member archive lacked the actual source-supplied `ref.input`, `pinned-baldosa.input`, and `complete.script`.
- [Run 39170675242](https://github.com/gamesbyian/UR-Recomp/actions/runs/39170675242) independently reconstructed **593** P1 source input events per guest, exact native calibrated shift **+1**, and preserved the original input files/script plus the 48 handoff images. Its source ZIP SHA `0fe45f6116e2b9c1e90a126acb67d9530e64beb5144fb58c637c9b6a228eeaf1` was independently rehashed. Its tested branch was created before source-movie memory capture was merged, so its genuine 66-member archive lacked the 16 historical source movie images.

Both were source-authentic and both remain bounded, but neither original archive by itself attests to **all** the actual historical movie memory images, fresh-original/native memory, source P1 controller file and executed script together. Separate archives from distinct source revisions are not an identical-run certification.

## Smallest valid integrated receipt

The current **existing** Bowl workflow already performs the exact 2014 source scan and both guest replays and now contains both instrumentation paths. `tools/qa01_bowl_joint_source_provenance.py` is a read-only post-producer integrity step. After the original 48-memory raw checker and 2014-SMV-derived actual-input verifier succeed, it:

1. Requires the original `bowl-report.json`, `bowl-independent-raw-audit.json` and `bowl-source-input-identity.json` to share an **identical SHA-256 of the actual original producer bytes**. Requires the original input receipt's source controller-window digest to equal the original producer's immutable 2014 window digest, exact calibrated shift and zero input-consumption claim.
2. Reopens all **16 actual original movie** and **32 actual fresh-guest** raw WRAM/SRAM image files across eight registered Bowl-result-relative offsets, checking full 128KiB / 8192-byte extents, original per-file source SHA, source movie host frames and every source-vs-guest **unmasked byte-difference receipt**.
3. Emits `bowl-joint-source-provenance.json` with exact producer/auditor/input SHA identities, source and guest capture counts, full original-vs-guest byte difference census, explicit zero accepted course credit, and explicit limits on all-frame CPU/SPC, consumed-input, shipping Windows and OS durability.

The joint checker does **not** infer the meaning of history-dependent SRAM bytes, justify a phase shift, hide the real fresh-original/native +341/+344 Switcher onset disagreement, or assert complete event acceptance.

When the updated Bowl PR executes on its final head, only that **actual** new run may be labeled a complete *same-run source/provenance archive*. Historic original artifacts cannot retrospectively contain missing raw bytes. The independent QA-01/07 release authority and source-event census remain **0/45 accepted USA events** and **0/12 Windows release gates** unless later adjudication independently proves all necessary gameplay/product conditions.

Usage on an extracted full exact-head original archive:

```sh
python3 tools/qa01_bowl_joint_source_provenance.py \
  --artifact-root /path/to/unpacked-bowl-artifact \
  --out /tmp/bowl-joint-source-provenance.json
```

No additional source/movie emulation is necessary for this offline check. The ROM-free tests include a synthetic consistent same-producer archive and falsifications of raw source images, producer identity, controller-window digest, raw comparison values and original movie memory presence.
