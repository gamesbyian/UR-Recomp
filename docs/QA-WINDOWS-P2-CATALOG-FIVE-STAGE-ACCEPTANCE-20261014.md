# QA-02: independent five-stage Windows P2 catalog recovery acceptance

**Status: ACTUAL same-run native Windows source, five raw stages and packaged candidate independently downloaded and rehashed; read-only consumer's exact-head unit regression pending.** No release gate promotion or final Windows candidate nomination is implied.

## Source and reuse

Modern #1564 genuinely created MIKE and MARTIN in separate Windows native game processes, deliberately restored the old one-row catalog, recovered MARTIN through the production gamepad-semantic P2 selector and reached stock two-seat GO in a fourth process. QA #1571 independently rehashed the retained native source ZIP, but its report did not contain actual catalog, typed SRAM and mutex bytes. Modern #1573 is adding those original bytes to a separate five-stage CI-only artifact without changing the source route or existing match archive.

The three-project reuse preflight selects the existing UR source/byte QA consumers and candidate-evidence envelope, Baldosa real source-driven routes and Malmazuke-style exact input manifests. The new independent Python reader reuses the established raw typed-profile/SRAM codec. It does not introduce another test runner, build or storage authority.

## Exact real-archive discriminator

The independent tool is tools/check_baldosa_win32_p2_catalog_stage_qa.py. It requires **two separately downloaded, full-SHA-256-pinned Actions ZIP archives**: the four-native-process source logs/report, and the five-stage saved bytes. The caller must separately confirm that both artifact IDs belong to the *same* green Win32 run, exact source PR head and proper producer-step ordering; a producer stage-name string alone is not an independent timestamp.

Command, substituting the actually computed SHA-256 hashes:

    python3 tools/check_baldosa_win32_p2_catalog_stage_qa.py \
      --source-zip /tmp/native-source.zip \
      --expected-source-sha256 <actual SHA-256> \
      --stage-zip /tmp/five-stage-raw.zip \
      --expected-stage-sha256 <actual SHA-256>

The source ZIP must contain precisely one report plus four distinct native process logs, same disposable user root, controller-semantic MIKE and MARTIN creation, native catalog-only recovery and original stock GO frame2353, with zero physical joysticks and no claimed scored result. The stage ZIP must contain exactly **37** canonical manifest/raw members over five fixed stages. Each file's bytes and SHA-256 are independently checked, including MIKE rider0 and MARTIN rider2 in both typed and 8192-byte raw saved SRAM, and the empty P2 CAS mutex.

The five required saved states, in order, are:

1. After native P1: one-row MIKE catalog, selected MIKE and typed/raw MIKE SRAM.
2. After native P2: two-row MIKE+MARTIN catalog, selected MIKE, typed/raw SRAM for both and empty P2 mutex.
3. After catalog-only loss: exactly the original one-row catalog; MIKE typed/raw, MARTIN typed/raw and empty mutex **byte-identical to the previous stage**.
4. After native recovery: the original two-row catalog, still selected MIKE and unchanged MARTIN typed/raw and mutex.
5. After stock two-player GO: exactly the same two-row catalog and unchanged original MARTIN typed/raw and mutex.

The reader allows MIKE's game-driven SRAM to change after genuine fresh processes; it requires exact MIKE bytes across the **catalog-only rollback**, where no game executes. Unknown archive files, duplicated names, symlinks, malformed catalogs, mismatched typed/raw identities, a changed P2 mutex or self-consistently re-signed forged release claims fail closed.

## Negative qualification

The stage producer's file order is not an independent OS crash or power-loss time oracle. The test injects the catalog rollback after the prior native process exits. No physical gamepad, real audible sound, concurrently racing Windows owner, genuine disk-full/power-cut failure, completed scored result/Records in this subroute, original-USA full-event parity or finally nominated merged-main executable follows. Preserve QA-02 in_progress, QA-05/12 unverified, final candidate null and strict USA complete-event acceptance 0/45.

Synthetic unit fixtures in tests/unit/test_check_baldosa_win32_p2_catalog_stage_qa.py establish reader invariants **only**. Once #1573 supplies genuine artifacts, independently download both complete ZIPs, compute their hashes, run the read-only checker against those exact bytes, retain a bounded machine-readable disposition and update only supportable QA-02 ledger fields.

## First actual real Windows stage-byte acceptance, 2026-10-14

Merged Modern #1573 exact product head 96787078e8ab66fdb867f0e0089ef09a95eb51c6 passed the real [Windows workflow run 38625129151](https://github.com/gamesbyian/UR-Recomp/actions/runs/38625129151). Independent QA downloaded three ORIGINAL unchanged artifacts from that one successful job and rehashed them in full:

| Same-run Windows artifact | GitHub artifact ID | Complete SHA-256 |
| --- | --- | --- |
| Four distinct real native game logs + source report, 5,548 bytes | 11923603156 | 16f1d2c78e078beb268ce71a67562864fac40cd1192d86816b1f268e94c28c12 |
| Five stage/raw archive, 37 retained canonical files, 18,029 ZIP bytes | 11924352730 | d43546a7a95abaeb779182dbd6aaaec06e9878ae844ed0a11d523eafa688950c |
| ROM-free Windows product wrapper, 5,944,556 ZIP bytes | 11923603148 | f9e0cf076fcf118534c1b34306ecb43088f1a4bd31caeed1646bf3a0d6a28a08 |

The package contains exact independently rehashed inner ZIP SHA256 **38ce585e5b57b92756f3014c3e81cf49a9e1325d35c44b6cb5622b3a3bc60f28** and authentic **AMD64 PE32+** executable SHA256 **399b6bb0c7c407fdb7cbfe19b7872ee3249a68fed6686576af4f60ed2902494c**. This executable is from the **producer PR head**, not yet a separately nominated final merged-main release binary.

The 37 actual source files have each been independently read and rehashed against all five JSON manifests, not merely counted. Original saved MIKE0 and MARTIN2 identities decode from the raw 8KiB SRAM and match their exact typed mirrors. The MIKE active selector has identical bytes in all five stages. The MIKE-only catalog SHA256 **5bd5875d01de17c498c90c389b3c7dd466f52762463b04b29f294585d4d5228b** switches to the two-row MIKE+MARTIN SHA256 **830ee6809c08c881439db6065633125025cf72129d4f10502e24cb4c0137d671**, switches back only at the deliberate lost-row stage, and returns to the exact **same** two-row bytes after the native controller recovery and original stock two-player GO.

The actual original MARTIN typed file, SRAM and zero-byte CAS mutex have identical bytes through **all four** later stages; the source raw SRAM SHA256 is **f3058e5fcd57042c8b0f04d9e3daf1fb81749c30da70b9596553afb89fb89102**, typed file SHA256 **0ff1202337488ec94fbc1d8a92ebe4c96f073f8f8d4d4f86a159b83011c4f251**. MIKE's typed/raw bytes remain identical across the test-only cut, while later authentic guest processes can legitimately change MIKE's 8KiB SRAM. All four source logs independently maintain the same test-owned root, semantic native P1/P2 creation, genuine source catalog recovery and GO at host frame2353. Every game reports **zero detected physical joysticks** and dummy or disabled audio.

A compact non-sensitive, machine-readable [independent review](../analysis/evidence/baldosa-win32-38625129151-p2-five-stage-independent-review.json) preserves all true ZIP/source/inner-PE hashes and negative gate flags. **This closes the previous missing raw-stage inspection**, but is still **an after-exit CI catalog-only rollback**, not an actual process-death or disk-durability test. Actual independent execution of the checked-in reusable reader against both original ZIPs is a separate regression requirement; this source review independently performed the same file checks. QA-02 remains in_progress, all other gates and release candidate unchanged, strict USA 0/45.
