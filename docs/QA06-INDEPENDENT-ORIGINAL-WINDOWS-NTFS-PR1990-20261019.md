# Agent 6: independent original Windows NTFS archival QA of PR #1990 (2026-10-19)

**Disposition: qualified hosted original-Windows fault observations, not a Windows release gate.** This report independently rehashes real artifact bytes; no Windows processes or human hardware were exercised by QA.

## Immutable tested executable and archive identity

Original green Windows run: https://github.com/gamesbyian/UR-Recomp/actions/runs/39337845469, PR #1990. The actual tested synthetic PR-merge source is `f7db1b92fbe347f1315cfe8de8ea3451857cb5fc`, authenticated by its two GitHub commit parents `34a308f66f0d7ba9bc6857a628c2fc92157e19a1` (then-main) and `70b3fe5147e0b807f16ce083bf1453b9b38fffd7` (PR head). The former historical owner ZIP on source `11501a15…` cannot inherit this result; neither can an unbuilt later main.

Independently downloaded, SHA256 verified and ZIP CRC checked original Actions artifacts:

| Original artifact | ID | Outer ZIP SHA256 |
| --- | --- | --- |
| ROM-free package with sidecar | `12227738503` | `41a0ea31eb0d030be7fe816a478ddcdb1fc8af6a5cf655a65b58bd125c3c28e6` |
| Same-run Windows executable binding | `12227853333` | `12bc7e7a252c18b708e481c80a84efd06dd17e5d5c965ec018f97667c5a32106` |
| Original pre-intent NTFS full-volume | `12227993287` | `bdafb211fba24f1f9ce8eb6c9759cb90cd72fe2391a4c8ba4f48e8e9124908fe` |
| Original postraw/pretyped NTFS full-volume | `12227608721` | `530dd48a0fe0af40220c329e0371b86b779a46be97f35540f2969255fbb30f60` |
| Interactive original CMD R/T paths | `12227793421` | `fa78c6c066f7c44507e646747229540f394b624fa57ccb2d36647539eed959be` |

Actual **inner playable ROM-free ZIP** SHA256 `2b0ed905047a2520ba1c9ef7aa0bd781e2f58b8bee3b9598562187b73c852b55` (6,057,753 bytes); original actual **PE32+ AMD64 executable** SHA256 `d418b2e9bb812bb064b825744e33753d88a9eb3cec9668377e8a15f1072c5c6e` (20,334,080 bytes). All immutable manifest member bytes agree with the independently verified ZIP/binding. Packaged CMD SHA256 `2f2a6cdbe9d4c37e331b82577ed3c947342e545a19bd0c022d0b940fa7cac8e0`. Independent PE import parsing found 31 normal DLL imports conforming to existing Windows inbox/API-set policy, no dynamic MSVCP/VCRUNTIME/SDL import, and an empty delay-import directory. Static portability does not certify clean Windows loading or hardware.

## Actual original Windows fault evidence, independently checked

**Pre-intent:** The original 25-member ZIP has 16 independently SHA/length-verified raw binary snapshot members. The genuine extracted original game CMD on an isolated 128 MiB NTFS VHDX refused durable intent allocation before raw SRAM publication, exited `8` with a save-error warning, and the Windows substrate records actual separate process error `112` (disk full). Full original 8,192-byte SRAM, typed profile, selector and catalog remain byte-identical to baseline through the failed save and **two distinct cold Windows process boots**. This is a controlled hosted Windows VHDX, not physical power removal.

**Postraw/pretyped:** The separate 29-member original ZIP's **22** binary stage files independently match every reported SHA/length. Its starting baseline exactly equals the pre-intent population. Native guest raw SRAM changes at **74** actual byte offsets, while generation-1 typed SRAM, catalog and selector stay identical; the denied state remains identical to postraw. The actual guest exits `8` with a save error, the filler records `errno=28` (with no WinError) and an independent Windows process records Win32 `112`. The full original intent bytes equal the archived recovered-intent receipt exactly. On the **first cold boot**, the guest reports `RECOVERY_RECONCILED` and new typed generation **2** contains precisely the actual modified 8 KiB raw SRAM; selector/catalog stay unchanged. The **second** cold process reports no repeated reconciliation and all four state files remain identical. Producer fault metadata and original logs were checked separately from raw byte comparisons. Neither electrical interruption nor a genuine torn disk write was exercised.

**Interactive R/T:** The original 47-member R/T ZIP passed CRC verification and 34 original stage-file SHA checks. Its console keys were programmatically injected, with both two-process cold restarts, not an uncoached human or physical-controller test. S/Q and real noncooperating concurrent writers remain separately reviewable.

## Independent reusable verifier and exact reproduction

`tools/check_qa06_ntfs_original_archives.py` requires independent outer ZIP SHA pins, exact synthetic checkout source and packaged CMD SHA, CRC/safe bounded ZIP structure, all original member lengths/hashes, explicit original Win32 errors, full 8KiB raw-vs-typed SRAM agreement, isolated postraw divergence, immutable intent, generation advance and both cold boots. It grants zero gates and has synthetic fail-closed negative tests for outer-hash replacement, false Windows errors, altered second-cold SRAM, wrong CMD identity, and forged source.

```bash
python3 tools/check_qa06_ntfs_original_archives.py \
  --pre ORIGINAL_ARTIFACT_12227993287.zip \
  --post ORIGINAL_ARTIFACT_12227608721.zip \
  --expected-pre-sha256 bdafb211fba24f1f9ce8eb6c9759cb90cd72fe2391a4c8ba4f48e8e9124908fe \
  --expected-post-sha256 530dd48a0fe0af40220c329e0371b86b779a46be97f35540f2969255fbb30f60 \
  --source-sha f7db1b92fbe347f1315cfe8de8ea3451857cb5fc \
  --cmd-sha256 2f2a6cdbe9d4c37e331b82577ed3c947342e545a19bd0c022d0b940fa7cac8e0
```

Actual downloaded-archive offline execution returned 16 pre-intent files, 22 postraw files, 74 changed raw byte positions, recovered typed generation 2, two cold boots and `release_gate_credit=0`. See the [immutable independent receipt](../analysis/evidence/qa06-independent-pr1990-ntfs-original-review-20261019.json). The positive was executed offline here; subsequent CI on this PR is a separate test.

## Additional independently reviewed original Win32 recovery/refusal cases

Four more **original** ZIPs were independently downloaded, external-wrapper SHA256 and CRC checked, and their **complete original binary populations** checked against every producer member SHA/byte length; none is a physical end-user playtest:

| Original case | Original Actions artifact | Externally measured wrapper SHA256 | Byte finding |
| --- | --- | --- | --- |
| Programmatic console **S** | `12228118019` | `45f8060416c68868ad6a9cc02a885063e6910f43bb1dc62248a448f8e7c8cf3a` | 29/29 archived stage bytes verified; healthy B and damaged A plus unrelated C actual data unchanged; only intended selector changed, exactly retained in two subsequent real cold B boots |
| Programmatic console **Q** | `12228083147` | `9b06a8d30260a0babe5d226ae43883e494bb84a8d8a51fdd228819ae0bfc9495` | 8/8 before/after original raw, typed, selector, catalog bytes identical; original CMD exit 7 without guest/default fallback or manual archive |
| **513-byte synthetic short raw** then R refusal and T restore | `12228073233` | `1221f2c0bee62f741a4bee77a2d10d0884249ba9e2bbefc4e88c5f2006e61b05` | 21/21 original captured bytes; R leaves all four original files unchanged, T restores canonical 8192-byte SRAM and both cold boots preserve exact restored bytes; this does **not** establish a real torn disk write |
| **Actual OS sharing denial after raw** | `12228287822` | `aca4d73da3d60aaa10ae94504196fb1e119a620ecd2992685450212059fbbf71` | 22/22 original binary receipts rehashed; source game writes 74 changed raw SRAM bytes, Win32 kernel replace probe returns **5** (access denied), CMD exits **8**, raw/typed divergence preserves typed/catalog/selector, first cold reconciles typed and second remains stable |

The OS-sharing denial is a distinct, authentic Windows filesystem failure from the full-volume `112` evidence above. Its file order is causally meaningful: real original guest raw publication, preserved typed/roster/selector on denial, retained durable intent, then correct cold typed finalization. It still does **not** establish independent adversarial noncooperating writers, arbitrary denied path classes, true short physical writes, 1P/2P human journeys or electrical interruption. Complete hashes and exact qualified scope are stored in the [machine-readable Agent 6 receipt](../analysis/evidence/qa06-independent-pr1990-ntfs-original-review-20261019.json).

## Same-source actual Windows 2P earned Records and raw-file reconfirmation

On this *same exact PR #1990 synthetic checkout/packaged PE*, QA independently downloaded actual original [Windows native player-journey ZIP `12228277849`](https://github.com/gamesbyian/UR-Recomp/actions/runs/39337845469) (52 CRC-valid members; wrapper SHA256 `7572678c890601230dad0df0896443343fcdaa8512ac5901b5b00adcbc2a4446`) and separate **pre-Records** pair archive `12227778561` (3 CRC-valid members; wrapper SHA256 `138f3bad12ff3a3c207aafbdba97fbe5a8aa4e271ef10c27e23c52094f58d6eb`). All **nine** original saved member sizes and SHA256s match the source-native manifest, and the new actual saved `.urrun`/`.urmatch` are **byte-identical** before and after fresh-process Records. Their independent FNV-1a64 checks equal actual stored trailers `a8327800e49e4c44` and `5838b68b19e040cb`.

Both distinct new frontend-created named profiles **MIKE 0** and **MARTIN 2** reached one genuine hosted Windows native stock 2P result: **P2 MARTIN wins**, MIKE 27.61 vs MARTIN 27.57 seconds, with independent fresh native Records logs from both perspectives (`LOSS 00:27.61` and `WIN 00:27.57`). Both actual raw 8,192-byte SRAM files equal their separately decoded typed-profile SRAM. The original saved run and match **payload bytes** are also exactly equal to the historically source-bound October 15 owner `.urrun`/`.urmatch` for the corresponding deterministic route, despite different timestamp-derived filenames and new source ZIP/PE. The new MIKE profile SRAM itself has a different SHA from the historic owner, and no claim of full byte-identical player save cohorts is made.

This is valuable same-executable integration evidence combining the *new* storage code with genuine scored 2P guest/Records. It is still **hosted semantic controller input, dummy audio, a single scored course, no independent Snes9x course acceptance, no actual physical two-pad/clean-owner computer**; the separate 1P earned `.urrun` raw file remains unretained. Treat it as a bounded QA-02/05/09/11 engineering positive and **zero complete release gates**.

## Source-consumed SRAM checksum and independently mutated original-log negatives

**New QA-only instrumentation of the archive consumer** computes FNV-1a32 directly from the downloaded full 8192-byte original SRAM, then verifies each source-emitted `BOOT_SRAM` line. The authentic pre-NTFS baseline is `63568e07` (warm, first cold, second cold), and recovered postraw is `255e468b` (first and second post-fault cold). All match original game logs **at the guest's first simulated frame**. The consumer also checks the initial `native_sram_intent_not_durable` refusal and `SAVE-FAILED`, the postraw `native_raw_written=1 typed_not_attempted=1` event and `io_error`, and the separately logged Win32 `exit=112`; it rejects recovery running again on cold boot two.

The tightened **original archived source** was replayed locally with both real original ZIPs: 16 before-stage state files, 22 postraw-stage files, 74 changed raw SRAM byte offsets, generation-2 typed alignment, and two cold boots still PASS. Four independently altered copies of the *real* postraw ZIP were built, with recomputed valid outer ZIP SHA256s: (1) forged first-cold `BOOT_SRAM` FNV, (2) fake repeated second-cold `RECOVERY_RECONCILED`, (3) substituted independent OS probe `exit=0`, and (4) erased the postraw `SAVE-FAILED` marker. **All four fail closed** for the corresponding missing causal witness. These mutations are local negative test fixtures, not actual Windows runs or release gate passes; no original ROM or saved profile bytes were committed.

## Evidence boundary and next owner

This is positive evidence about **one named profile on the genuine source-compiled Windows guest, in a source-qualified but unmerged synthetic PR checkout**. The postraw ZIP does not itself embed full tested source SHA; source linkage also uses the separately inspected original Actions run and matching compiled CMD. Request a separate producer-local full source/PE/ZIP receipt per future scenario. Still missing: one immutable integrated **merged-main** Windows ZIP, active competing writers, denied/share/short and electrical interruption coverage, full real 1P/2P profile/Records player journey, dissimilar clean consumer PCs, actual dual controllers, audible audio, true UHD/7:6 display and authoritative original/native USA events. Retain original nominated October 15 source and ZIP without relabeling, QA-02 in progress, physical=false, release_decision=not_assessed, **0/12 Windows release gates and 0/45 complete USA events**.
