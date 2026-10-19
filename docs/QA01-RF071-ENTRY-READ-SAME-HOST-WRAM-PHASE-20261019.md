# QA01 RF071: actual original getset-entry bytes versus separately sampled WRAM

**19 October 2026.** Read-only independent QA complement to merged [RF071 actual original source-getter proof](RF071-AUTHENTIC-ORIGINAL-GETSET-RETURN-TRANSACTIONS-20261019.md) and merged [RF066 post-return phase counterexample](QA01-RF066-RETURN-VS-FRAME-OBSERVATION-PHASE-20261019.md). **No guest emulator run, gameplay modification, native reader fabrication, clock shift or byte mask is undertaken by this verifier.**

## Source and exact witness

RF071 independently reopened the **actual original Snes9x compiled clean-getter** execution from genuine RF069 Zoo [run 39307624432](https://github.com/gamesbyian/UR-Recomp/actions/runs/39307624432): immutable [artifact 12215281695](https://github.com/gamesbyian/UR-Recomp/actions/runs/39307624432/artifacts/12215281695), ZIP SHA256 `90b03d7e035c7a1939b488211b98165615e3fc63226fe57ac718fc7e3e772763`. RF071's merged source reads/returns contract binds 903 true original `QA01RF063ORIGBUS kind=rb/rw phase=getset_entry` events to 903 genuine RF064/RF066 post-getter returns, matching exact physical stack addresses/widths/returned bytes and source-local sequence. Twelve real getters cross an original Snes9x video scanline, so a fabricated single-frame H-clock ordering is especially hazardous. The `PC` at getset entry remains observed *source PC context*, not an independently decoded native/original opcode-fetch PC.

This same archive retains true unmasked 128KiB original and native WRAM at race-relative `scene-00001/00002/00004`, actual successful source/native script-dump ACKs and original/native guest controller files sourced from the historical 2014 SMV. The script-dump memory bytes have a **different observation phase** from the physical getset-entry read values despite sharing host-frame numbers. The relative chronological order between the original getset-event recorder and script dump is **not independently established** by their separately buffered text log streams.

## Positive actual source evidence, strict negative inference

`tools/qa01_rf071_getter_vs_script_dump.py` first calls the **merged** `qa01_rf071_original_real_read_join.authenticated_case` to revalidate immutable source, original/native movie/ROM/input authority and all **903 actual original getter-entry→return joins**. It then independently reopens the actual pinned 2014 movie controller sample bytes and both native/original supplied input-file SHA/duration/mask sequences, separately rehashes both guest logs and rechecks each guest's real `scene` ACK frame against its own observed origin. It finally reopens all six full original/native WRAM images and **reuses merged #1949's bounded phase comparator** to count every physical original getter-entry byte sample at one of the four genuine original/native differing `7E:01ED..01F0` stack addresses.

| Same-host relative sample | Actual original getter-entry READ operations touching differing bytes | Real getter-entry byte positions | Matches original script-dump only | Matches native script-dump only | Matches neither guest dump |
|---|---:|---:|---:|---:|---:|
| +1 | 74 | 104 | 3 | 6 | 95 |
| +2 | 91 | 119 | 3 | 5 | 111 |
| +4 | 97 | 128 | 3 | 5 | 120 |
| **Total** | **262** | **351** | **9** | **16** | **326** |

These counts were independently explored directly from the genuine RF069 source ZIP before writing the new consumer; the new **archive-only** CI workflow repeats the entire authenticated source/read/raw claim from source bytes rather than relying on that exploration. A word GETTER returns one operation, potentially two compared physical bytes. The 16 instances matching only the **native dump** remain original-side reads; they **are not real native getter observations**.

Consequently, the genuine original original CPU `getset_entry` value itself is **not** in general replaceable by **either** host-script `dump` value for a same-named frame. There is no evidence of exact cross-recorder or original/native clock-phase equivalence. The original native read producer RF062 still must provide actual native decoded opcode PC/operand, genuine physical bus values and a comparable execution phase; do not retrofit a matching native source read, exempt any stack bytes, or infer a player's accepted result.

## Reproduce with no emulator build

```bash
python3 tools/qa01_rf071_getter_vs_script_dump.py \
  --archive /archive/rf069-real-zoo-12215281695.zip \
  --movie reference/imported/tas-bots/dessyreqt-4250-submission.smv \
  --metadata analysis/generated/historical-2014-smv-metadata.json \
  --output /new/rf071-original-getset-entry-versus-WRAM.json
```

The opt-in `.github/workflows/qa01-rf071-getter-vs-script-dump.yml` performs the same read-only source-authentic archived-file test and negative unit cases, and preserves only the compact verdict. Unit fixtures are **not** counted as source proof. CI success remains a diagnostic only; factory preflight retains its independent strict HOLD, as do **0/45 USA complete events and 0/12 Windows release QA gates**.


## Actual offline qualified-run receipt

[GitHub Actions source-authentic run 39312840489](https://github.com/gamesbyian/UR-Recomp/actions/runs/39312840489) **passed** its genuine 2014 original movie/source RF071 getset-entry→return and three original/native pair tests with all byte masks zero. I independently downloaded the retained one-member verdict archive, artifact `12216122314`: outer ZIP SHA-256 `b97bccd7ae82d40c3c4acfe685f1298943e81a7964127a1c01db99db5359a758`, inner `getter-vs-dump.json` SHA-256 `c58099abbebc5597f01dc0020f271750f673c80d4caf61bbd4c159578490a8de`. The exact real-case counters were confirmed: **903** joined original real getset read/returns, **12** Snes9x scanline-crossing getter calls, 3 raw original/native 128KiB pairs, 262 source getset reads touching four differing stack addresses, **351** byte comparisons and **326** neither-dump values. Full immutable ZIP/case identities are retained in [the compact independent machine receipt](../analysis/data/qa01-rf071-authentic-original-getter-vs-same-host-wram-20261019.json).

Both the workflow and the machine receipt explicitly refuse to equate original/source getter-entry PC context with an independently decoded opcode PC, to order buffered script dump against a getter event, or to claim any paired **native** executed read. A successful original getset read→return join is not the same scientific proposition as a first *cross-guest* causally consumed difference. The next productive experiment must capture the native physical bus returned value with its actual decoded guest opcode context and original semantic-phase counterpart, not sample more host WRAM as a surrogate. **0/45 USA events; 0/12 Windows release gates.**
