# QA-02: independent 306-member Windows native fault archive audit

**2026-10-17. Bounded hosted Win32 source-byte evidence, no release gate.**

Original Actions artifact **12114666724**, SHA256 **d599deef5859a30b2d8d3192c11c97eb48c84b518eac395795adc602ce563a84**, is from green [Windows run 39068318622](https://github.com/gamesbyian/UR-Recomp/actions/runs/39068318622). Its actual tested PR-merge source **503464180dad14bb0275e9fea03f1902c1b5c861** has parents then-main b80ad58e and Modern #1713 head c42f1f4a. The original package/binding artifacts **12114487315 / 12114019652** separately bound the same ROM-free ZIP SHA256 **33eb094ef5a9c2c959f79b03823e434f8f036ff05bf00fa3cb98bd96fd6bc596** and AMD64 PE SHA256 **2dfef82712ab6eae160d5b2962bcf828d604c03ac0630e287771b6a36388673b**. This is not the immutable older nominated owner candidate.

Independent original Actions ZIP inspection: **306 unique members**, all ZIP CRC clean, all fixed scenario-root names valid, **211 rehashed source-original binary SHA receipts across eleven groups, zero mismatches**; **195** contain independently checked reported byte lengths, while **16** F3 stage hashes are SHA-only (source bytes still opened and compared). [The QA-only offline checker](../tools/check_qa02_win32_full_original_fault_archive.py) requires the external original SHA256 and fails closed on mutated or incomplete evidence.

| Source group | Verified original binary receipts | Bounded observation |
| --- | ---: | --- |
| Legacy postraw unjournaled crash | 12 | Exact original raw/typed mismatch preserved |
| Journaled postraw crash/recovery | 16 | Durable original intent permits authorized typed replay |
| Postraw recovery under actual OS denial | 18 | Old state preserved until Windows filesystem restoration |
| Posttyped pre-intent-retirement crash | 16 | Raw/typed already agree and cold boots are byte-stable |
| Durable pre-raw-intent Exit(84) cut | 17 | All four canonical files identical before/crash/two cold boots |
| Real crashed B with healthy alternate A | 24 | Unrelated A untouched and interrupted B source raw retained |
| Journaled B crash with healthy A | 32 | Original A/B and staged B intent independently retained |
| **Actual Win32 prewrite NTFS DACL denial** | **12** | Every canonical original file byte-identical before/denied/second cold |
| **Actual live postraw Win32 typed-publication denial** | **22** | Original raw changes by **28 bytes**; typed blocked, then two consistent cold recoveries |
| Three-profile damaged A / healthy B / unrelated C | 29 | A/B/C source snapshots preserved; C on-disk typed absence remains producer-reported |
| **Synthetic** 513-byte truncated SRAM with explicit rollback | 13 | Windows recovery is real; the partial write itself was deliberately injected |

Original typed-profile full 8192-byte stock SRAM data was decoded independently and matched original raw images at required baseline and recovered stages. The postraw intent was byte-identical to its recovered immutable receipt. Real Win32 denial logs displayed the failure; prewrite ACL denial happened **before raw publication**, whereas the separately tested postraw sharing denial happened **after original guest raw changed**. The packaged save-refusal artifact reports **74** changed raw bytes on its different source route, and must never be conflated with the fault archive's **28**.

The original archive also contains the optional **19-member flat QA02 journaled recovery source ZIP**, SHA256 **ac3758b2c2e12950d4e17cae14f06f22bbc03a303a15a3bf1e18a19aacc7619d**. Its original checksum sidecar matches, and all nineteen nested members are **byte-for-byte identical** to the corresponding source-original full fault archive files. This confirms the corrected flat export's schema and fixed member population; earlier incompatible 18-member exports remain historical negatives. No additional process execution is inferred from nested byte equality.

**Limits:** Hosted original Windows producer execution and offline retained-byte verification are not a physical power-cut test, true disk-full or short NTFS write, human R/T/S/Q operation, real two gamepads/audio/UHD, integrated Modern+graphics build or independently accepted complete USA event. Preserve P0 #1214, Modern #1713 and graphics #1780 holds. Release ledger **0/12** and original event census **0/45**; immutable owner source 11501a15 / ROM-free ZIP SHA256 5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7 unchanged.
