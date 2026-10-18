# QA-01 independent real-USA Dragster → Zoo memory recheck

**18 October 2026. Complete USA events accepted: 0/45; release QA gates passed: 0/12.**

## Genuine source and verdict

Actual [original/native Dragster→Zoo run 39174631932](https://github.com/gamesbyian/UR-Recomp/actions/runs/39174631932) used immutable source `542205bd596306ef14a753dd005e391f60a8d413`. Its original [69-member Actions archive 12154480620](https://github.com/gamesbyian/UR-Recomp/actions/runs/39174631932/artifacts/12154480620) was **independently downloaded and byte-hashed**, SHA-256 `f036f80d72000b05a5c2edb42152eb433b89fa44c5fc36238ccc73bd143e2947`. The genuine 2014 source trace file hashes to `3de122406937fcf839988d7990972e9275b8e7bbd47db1b958fea20113c27c54`; its sampled source movie, fresh Snes9x and fresh Baldosa clocks remain separately registered. The 14 actual original and 14 native host dump acknowledgments match the claimed guest frame exactly.

**Independent strict result:** Source 2014 Dragster Race A result at frame **2874**, followed by sustained active Zoo at source +316, while fresh Snes9x enters Zoo at result **+315**, native at **+318**. The preceding finished Dragster duration itself was fresh Snes9x **+2081** versus native **+2079**, versus source movie +2080. The green run is a **bounded diagnostic exit, not complete original/native course fidelity**. No input frames were shifted, no sampled WRAM bytes masked, and there is no eligible 45-event promotion.

Reopening all **28 full WRAM images** and **28 full SRAM images** at 14 paired samples independently gave **3,616 unmasked full-WRAM differing-byte occurrences**, 14/14 nonexact original/native 128-KiB pairs, and **13 identical differing SRAM offsets at each sample**, 14/14 nonexact 8-KiB SRAM pairs (182 differing occurrences). Both games preserve the 2508-centisecond ranked Dragster result and valid original 150-word record-table checksum. Earliest significant observed race-state separation is +315, when fresh original has entered Zoo while native has not. Even after both are active the 128-KiB images remain nonidentical. The precise by-offset data and the 13 SRAM addresses are in [the immutable independent review](../analysis/data/qa01-dragster-zoo-independent-raw-archive-verification-20261018.json).

## Independently reusable archive auditor

`tools/qa01_dragster_zoo_raw_archive_audit.py` reads the **extracted genuine original workflow archive**, not a made-up testcase, and uses the already merged independent Bowl `raw_wram_pair` logic rather than the Dragster producer's comparator.

```bash
python3 tools/qa01_dragster_zoo_raw_archive_audit.py \
  --archive-root /path/to/extracted/qa01-dragster-next-zoo-original-native \
  --out /tmp/qa01-independent-dragster-zoo-audit.json
```

It requires the original source and producer JSON, SHA-256 authentic source trace, exact source movie frame/sample identities, full unaltered source/movie/ROM/input/compiled-binary hash shapes, independent original/native host dump log acknowledgments, 14 pairs of real 131072-byte WRAM and 8192-byte SRAM images and the raw guest state/record hashes. It recalculates the **entire** original/native WRAM byte difference report at each sample, genuine SRAM equality, all three individual entry brackets, original/native record-three-rank table/holder/checksum and every producer aggregate based on those raw guest bytes. Falsified positive flags, contradictory host or source clocks and missing/tampered raw files are **invalid evidence** (nonzero exit); a genuine observed guest state difference remains a verified **strict negative** with exit zero and accepted-events zero.

The original 2014 movie is retained as source trace and named states, **not a third 128-KiB movie capture** at each checkpoint. Zoo's canonical RNC course payload is only asserted in the original producer guest report; source course payload bytes were not independently rehashed from this archive by this auditor. Reported source movie eight-consecutive-active-frame status is similarly sourced from the source trace scanner; merely verifying the full source trace's hash does not independently replay that scanner. Compiled native ELF and shipping Windows PE, all intervening gameplay frames, consumed controller-port reads, CPU↔SPC common-age phase and Windows disk cold/power-cut evidence are still unproved.

ROM-free synthetic unit tests exercise complete 14-sample genuine-file-layout contracts, real mismatched frame entry, corrupt/missing captured RAM, forged clocks, changed source trace, false ranked records and attempted event-credit promotion. These synthetic examples are **integrity regression tests only**.

Source-specific Dragster fixture implementation and future genuine controller/CPU research remain with the alternative-event and CPU/APU agents. This read-only verifier is independent QA-01/07 only. **No game logic, CPU/SPC timing, workflow, automatic trigger, additional emulator build or release ledger is changed.**
