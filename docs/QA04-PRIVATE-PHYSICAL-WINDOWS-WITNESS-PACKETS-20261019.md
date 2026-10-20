# QA-04: private physical Windows witness packets

**Purpose:** Give actual independent human Windows testers a bounded, reproducible evidence envelope for one *externally nominated* source SHA, full portable ZIP SHA256 and extracted AMD64 PE SHA256. This supports QA-04 review but **can never automatically certify physical hardware, clean installation, playable audio/controller behaviour or release readiness**.

The established release requirement is **three dissimilar Windows environments**, with **at least two physically separate PCs** and **at most one isolated clean VM**, plus at least one verified clean environment. Run the *same exact source/ZIP/PE candidate* in all three. This is deliberately stricter than hosted Actions SDL input and dummy audio. The existing [Windows clean-machine acceptance procedure](WINDOWS-CLEAN-MACHINE-ACCEPTANCE.md) and `tools/Test-URRecompPortable.ps1` own the **full shipping Windows package** verification and optional launch. The historical four-member ROM-free Baldosa preview is a *different package format*: never pass it as the full shipping ZIP. Use the preview's established owner source/manifest tools for that format instead.

## What each independent tester does

1. Obtain the **source/inner portable ZIP/executable SHA256 from the independent QA nomination**, not from a self-declared manifest or the product author's PR. Save a private copy of the ZIP (and any required legally held ROM) outside the evidence folder. Verify the portable ZIP SHA256 using native Windows PowerShell `Get-FileHash -Algorithm SHA256`; verify the actual packaged or extracted executable SHA256 likewise, **before and after a normal manual gameplay session**. Preserve the unmodified verifier transcript and startup log.
2. On a clean-install or properly isolated VM, run the existing Windows package preflight for **the correct package format**. Launch the real game without injected SDL input. On physical PCs, operate actual P1 **and** P2 gamepads, listen to output on a physical audio device, view graphics on an actual display and play through relevant initial frontend, pause, 1P/2P and earned Records journeys. For 4K acceptance include a real 3840×2160 mode on at least one physical machine, not a fake offscreen framebuffer, and document aspect/pixel-aspect behaviour. This includes observations separate from file hashes.
3. Place a **privacy-reviewed** `witness.json` plus local attachments (transcript, sanitized startup log, controller P1/P2 observations, audible-output witness, visible-display witness, played journey) inside a separate private folder for each tester. A screenshot, log or human note is supporting evidence only; static device inventory can identify a driver but cannot prove active input/audio/display. No private ROM, compiled executable, SRAM, credentials, precise addresses, hardware serials, MACs or personally identifying filesystem paths belong in a shared report or Git repository.
4. Run the read-only `tools/check_qa04_physical_windows_packets.py` on **all three** private `witness.json` paths with three external hashes. It independently verifies each attached file's exact SHA256/size, refuses symlinks/path traversal, mixed source/PE/ZIP, source self-admission, duplicate hardware and missing genuine-observation claims. It prints a zero-credit preflight report. Actual QA reviewers inspect the original privately retained evidence, reproduce any disputed machine state and manually adjudicate QA-04 in the sole release ledger.

### Commands on an ordinary Windows tester PC

```powershell
Get-FileHash -Algorithm SHA256 .\UR-Recomp-Windows-x64.zip
Get-FileHash -Algorithm SHA256 .\UniracersSNESRecomp.exe
# Follow the existing Test-URRecompPortable.ps1 acceptance instructions.
# Repeat both hashes after the user-operated game session, then save transcripts.
```

The original **archive SHA** is different from the **outer GitHub Actions artifact transport ZIP SHA**. Always use the separately nominated *playable* package SHA as `artifact_sha256`, not an Actions wrapper SHA. The tested executable SHA is the actual PE byte hash, not a source hash or an `.exe` filename.

### Receipt schema: one JSON file per private tester

```json
{
  "schema": "ur-windows-physical-witness/1",
  "source_commit": "40 lowercase hex of nominated source",
  "artifact_sha256": "64 lowercase hex of the nominated playable ZIP",
  "tested_executable_sha256": "64 lowercase hex of the extracted actual PE",
  "zip_sha256_before_launch": "same 64 hex ZIP",
  "zip_sha256_after_launch": "same 64 hex ZIP",
  "pe_sha256_before_launch": "same 64 hex PE",
  "pe_sha256_after_launch": "same 64 hex PE",
  "package_unchanged_after_launch": true,
  "independent_review_completed": false,
  "operator_notes": "Description of observed real controller/audio/video, no personal data",
  "hardware": {
    "setup_id": "unique anonymous machine/tester setup",
    "environment": "physical",
    "clean_environment": true,
    "windows_version": "Windows version/build; no system serial",
    "gpu": "GPU and driver family",
    "display": "physical display model and observed mode",
    "controller": "both distinct physical P1 and P2 pads",
    "audio": "physical speaker/headphone device and route",
    "physical_controller_observed": true,
    "audible_output_observed": true,
    "visible_display_observed": true
  },
  "attachments": [
    {"kind":"portable-verifier", "path":"portable-verifier.txt", "bytes":123, "sha256":"64 lowercase hex of file"},
    {"kind":"startup-log", "path":"startup-log-redacted.txt", "bytes":123, "sha256":"64 lowercase hex of file"},
    {"kind":"controller-p1", "path":"controller-p1-observation.txt", "bytes":123, "sha256":"64 lowercase hex of file"},
    {"kind":"controller-p2", "path":"controller-p2-observation.txt", "bytes":123, "sha256":"64 lowercase hex of file"},
    {"kind":"audio-output", "path":"audio-output-observation.txt", "bytes":123, "sha256":"64 lowercase hex of file"},
    {"kind":"visible-display", "path":"visible-display-observation.txt", "bytes":123, "sha256":"64 lowercase hex of file"},
    {"kind":"played-journey", "path":"played-journey.txt", "bytes":123, "sha256":"64 lowercase hex of file"}
  ]
}
```

Replace placeholder SHA strings with the **real canonical lowercase** hashes and each `bytes` with the exact original attachment file length. Set `clean_environment` only if independently warranted. For one isolated clean VM, use `environment=isolated-clean-vm`, mark physical-observation flags **false**, and provide at least verifier, startup log and played journey attachments. That VM can complement two actual physical PCs; it does not itself prove a physical controller.

```bash
python3 tools/check_qa04_physical_windows_packets.py \
  private-pc-a/witness.json private-pc-b/witness.json private-pc-c/witness.json \
  --source-sha YOUR_INDEPENDENT_40_HEX_SOURCE \
  --portable-zip-sha256 YOUR_INDEPENDENT_64_HEX_PLAYABLE_ZIP \
  --executable-sha256 YOUR_INDEPENDENT_64_HEX_AMD64_PE
```

## What a successful preflight **does not** say

The only positive output is `structural_three_setup_coverage=true` and `original_private_attachments_hash_verified=true`, indicating packet structure and local file-byte consistency. Crucially the output still has **`independent_hardware_observation_certified_by_tool=false`** and **`release_gate_credit=0`**. Text files or photographs can be falsified; the tool cannot verify the claimed machines existed. The separate reviewer must inspect operator input, timestamped original machine observations, physical player experience, audio/display quality and candidate identity before *any* L5 evidence is considered for QA-04. Never append self-authored `passed`, `physical_hardware_verified` or release verdict keys to the packet; the checker rejects self-admission.

**As of October 19:** The repository holds four source-qualified hosted Windows binaries and an older nominated October 15 owner ZIP, but still has no completed three-setup independent hardware campaign, stable-main P0 recovery release build or physical gamepad/audio/UHD certification. QA-04 remains **unverified**; all **0/12** Windows release gates and **0/45** complete USA original/native events remain unchanged.
