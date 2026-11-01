# One-click, owner-only Windows export of additional original racer poses

This is an **optional, entirely local** handoff for the HP Windows 10 PC. It unblocks genuine additional-family original sprite evidence for ART-4K, using the **existing** deterministic original ROM composer and [verified corpus exporter](ORIGINAL-RACER-CORPUS-EXPORT.md). It does **not** install a scheduled task, ask for GitHub credentials, download a ROM, create a model, change the Windows game, or upload new source images anywhere.

## Run on a Windows 10 machine with the UR-Recomp checkout

1. Update an existing `gamesbyian/UR-Recomp` checkout to the latest `main` (or obtain the current repository using your usual approved checkout process). Keep both launcher files in `tools/art/` beside the existing Python tools.
2. Double-click **`tools/art/Prepare-Original-Racer-Corpus.cmd`** in Explorer. This starts the PowerShell helper and leaves the result/error visible.
3. Select a **locally held, legally obtained USA Uniracers ROM** using the file dialog. The launcher verifies exactly **2,097,152 bytes** and SHA-256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`. Wrong region, bad file, cancelled selection or missing Python fail before source extraction.
4. The script uses `py -3`, `python` or `python3`, requiring **Python 3.10+** and the source's ordinary stdlib compositor (no Trimesh, GPU or cloud services). It creates a unique *private* folder under `%LOCALAPPDATA%\UR-Recomp\private-original-racer-corpora\original-racer-<date-id>\`.

### Resulting private folder

```text
original-racer-<date-id>/
  source-corpus/
    source-corpus.json          # canonical-ROM-verified completion receipt
    stock/source-<SHA256>.png   # original 64x64 images; never uploaded
  research/
    roles-draft-all-diagnostic.json   # edit privately before choosing fit/holdout
    source-family-diagnostic-groups.json
```

The source exporter checks the exact canonical USA ROM, registered original source/representation IDs, unique RGBA hashes and binary silhouette hashes, and independently validates all 32 known P1/P2 frames when the existing 1205–1220 window is included. The manifest receives a true local canonical-ROM-verified composition marker. Files are published through an exclusive new directory claim, with `source-corpus.json` as the final completion marker; an interrupted run without that receipt must be discarded.

The split freezer independently rechecks the created source PNG bytes and groups animation windows that share an identical original **binary** silhouette. The provided roles start with **every family `diagnostic`**, so no claimed independent fit/held-out split is invented. An investigator may later assign `fit` and `withheld_candidate` roles to distinct verified components **before** geometry optimization. Distinct 2D source masks do not prove distinct original 1994 camera views.

### Optional unattended command-line invocation

```powershell
# Uses existing files; only run with your explicit authorization.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File \
  .\tools\art\Prepare-Original-Racer-Corpus.ps1 \
  -RomPath "D:\MyPrivateROMs\Uniracers_USA.sfc" \
  -OutputParent "D:\PrivateArtResearch"
```

PowerShell line continuation in a real `.ps1` uses backticks rather than Unix backslashes. The two-line example above is illustrative; invoke it as **one line** in a PowerShell console if pasting. The `.cmd` file is the ordinary one-click path and needs no arguments. All generated source raster bytes stay entirely on the local Windows disk by design.

## Follow-up for ART-4K agents

Only after private source availability, inspect the immutable source-receipt and shape-disjoint diagnostic groups. Freeze fit/held-out roles through `tools/art/freeze_racer_source_family_splits.py`, then run the existing [source-matched multi-pose scorer](MULTIPOSE-SOURCE-EVALUATION.md) and actual five-part GLB reviewer. Do not put a source ROM or original regenerated PNGs in the public repository, GitHub Actions artifacts, Pages or arbitrary cloud storage. If the owner voluntarily provides only the source-corpus JSON/diagnostic report, those are metadata and **do not give remote agents access to the actual original PNG bytes**. Additional pose fidelity measurements require that access through a separately authorized private mechanism.

**Support/failure modes:** the CLI explicitly refuses output inside the repository; an existing folder or symlink can never be replaced. Python missing/old, lack of NTFS same-volume hardlink support, invalid source metadata or cancelled ROM selection produce a non-success exit. An absent `source-corpus.json` means an incomplete attempt; it must never be treated as source evidence. This owner-only workflow does not schedule itself. The unrelated five hourly agents and HP research scheduler remain unchanged.

