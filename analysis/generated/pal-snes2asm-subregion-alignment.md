# PAL/prototype snes2asm survivor subregion alignment

Refinement of the three survivors from `pal-snes2asm-homolog-alignment`; whole-window evidence is preserved.

Whole-window survivor role disagreements: **114**.
After trusted-boundary executable-island alignment: **0**.
Additional reduction: **100.0%**.

## `00:ABA9..00:ADE2`

- `00:ABA9..00:ABB8`: excluded data. Nitrodon identifies frontend/text bytes before executable `80:ABB9`.
- `00:ABB9..00:AD0F`: shift **-31**, raw similarity **0.953**, role disagreements **0**, M/X disagreements **0**.
- `00:AD10..00:AD33`: excluded embedded frontend command/text data consumed through `80:C3AB`.
- `00:AD34..00:ADE2`: shift **-13**, raw similarity **0.989**, role disagreements **0**, M/X disagreements **0**.

The shift change from -31 to -13 across embedded data is the decisive negative result: one whole-window shift was invalid.

## `00:C3A9..00:C450`

- `00:C3A9..00:C3AA`: preceding frontend-string tail, excluded.
- `00:C3AB..00:C3CA`: parser/dispatch setup, shift **-19**, raw similarity **1.000**, role disagreements **0**, M/X disagreements **0**.
- `00:C3CB..00:C3EC`: decoded 17-entry FF..EF handler-word table, excluded from executable comparison.
- `00:C3ED..00:C450`: executable handler region, shift **-19**, raw similarity **0.890**, role disagreements **0**, M/X disagreements **0**.

The previous five aligned role disagreements were table/code boundary noise.

## `00:8C49..00:8CCA`

- `00:8C49..00:8C4D`: initial boundary fragment, excluded.
- `00:8C4E..00:8C73`: executable prefix, shift **-5**, raw similarity **1.000**, role disagreements **0**, M/X disagreements **0**.
- `00:8C74..00:8C77`: **genuine PAL-retail-only four-byte JSL**. The prototype proceeds directly to the following stores.
- `00:8C78..00:8CCA`: executable suffix, shift **-9**, raw similarity **1.000**, role disagreements **0**, M/X disagreements **0**.

This is a real executable lineage delta surrounded by exact homologs. The previous 18 role disagreements and one M/X disagreement came from forcing a single shift across that insertion.

## Method conclusion

All **114** role disagreements surviving the first whole-window homolog pass disappear once trusted code/data/function boundaries and the one genuine executable insertion are represented. No bounded da65 or Ghidra escalation is warranted for these three windows because there is no analyzer disagreement left to adjudicate.

Removed disagreements remain negative evidence. Mixed code/data windows may require piecewise homolog alignment, and a genuine inserted/deleted instruction sequence can change the correct shift inside one function.
