# QA-02: independent five-stage Windows P2 catalog recovery acceptance

**Status: independent consumer and synthetic adversarial tests, pending actual #1573 Windows raw-stage evidence.** No release gate promotion or final Windows candidate nomination is implied.

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