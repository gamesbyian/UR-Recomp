# QA-01: source-earned Zoom Zoo cold guest record reload

**Owner:** QA-01/07 original/native gameplay and record correctness. **Status:** opt-in experiment pending real execution. No course/gate credit.

## Why it is a decision-changing missing experiment

Corrected Zoom Zoo reaches the same true Circuit result (+5163 on both independent race clocks), awards MIKE a Crawler/Zoom Zoo best lap **2510 centiseconds** at result+16, and exposes the authentic original/native 8192-byte battery snapshots through result+72. Original/new native RF-017 local and hosted receipts now show six post-result full SRAM pairs equal, including result-to-next-track transition; nevertheless all previous captures are **inside the same guest process**. The original game is only useful to a player if a subsequent boot actually reads the newly earned result. The release ledger still has zero complete USA events.

The opt-in `tools/qa01_cold_result_record.py` uses the **existing** source-qualified original/native campaign's captured +72 battery images as the only seed. It first checks ROM, 2014 archived original movie/controller hashes, course/result identity, source-frame equality, native/reference executable digests, independent image SHA-256, MIKE's original 2510 record/holder, and complete 150-record checksum. Nothing is synthesized or written into either SRAM after recording.

It then starts **two wholly new guest processes**, one original Snes9x and one pinned native Baldosa, with their own independently captured 8 KiB image. It uses only the existing `snesref` runner and `run_pinned_baldosa` isolated save-root wrapper; zero controller inputs, read-only `wait 300; dump; wait 120; dump`. Both guests must produce valid fresh 8 KiB battery images at the exact original/native host frames 300 and 420. At both samples the *entire* original 150-word record table, all 150 record holders, stored checksum and MIKE rank-0 best lap must be preserved byte-for-byte and must agree across engines. A missing/changed image, course/source SHA mismatch or invalid checksum fails closed. No source controller inputs, game state or runtime implementation are modified. The manual campaign's new `qa01_cold_guest_reload` flag requires `selected=zoom-zoo` and `source_followthrough=true`; it adds work only after the existing source-qualified producer/classifier succeeds and shares the prebuilt binaries.

## Claims this can and cannot support

A successful execution proves a genuine source-earned record can be **loaded from its raw battery image by independently restarted original and native guest processes**. The harness stages these images into their fresh startup save locations. It does **not** prove the shipping Windows host actually fsyncs, publishes or recovers its own game-generated `save.srm`, that interrupted/force-killed processes are safe, that the cold boot follows the exact earlier player's original in-tour history, or that every unobserved frame matched. Neither the new snapshots nor equal records substitute for strict race/result/transition parity. Independent release QA owns disk and physical Windows candidate acceptance.

### Stop rule

One successful cold original/native reload of source-earned MIKE 25.10 under an exact corrected guest is sufficient for this bounded question. If a failure occurs, inspect only the first invalid input source SHA, process boot/record step or host-side save substitution, not a generic 45-course survey. Repeat on the RF-017 Windows-integrated exact candidate if necessary. **Release complete-event credit remains 0/45 until the strict complete source event, actual product linkage, required progression and disk durability are independently admitted.**
