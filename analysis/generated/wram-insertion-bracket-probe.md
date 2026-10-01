# WRAM insertion-bracket operand probe

Narrow trusted-code scan for absolute 16-bit operands inside the two post-prototype WRAM insertion brackets.

## Input_CaptureAutoJoypad structural match

- USA: `80:85E4`
- pal-prototype-1994-11-29: `80:85E3`, similarity 0.969, semantic recall 1.000
  - projections: `030D→030D`, `030E→030E`, `030F→030F`, `0310→0310`, `4218→4218`, `4219→4219`, `421A→421A`, `421B→421B`
- europe-retail: `80:85E4`, similarity 0.000, semantic recall 0.500
  - projections: `030D→18AD`, `030E→1AAD`, `030F→19AD`, `0310→1BAD`, `4218→C220`, `4219→118D`, `421A→138D`, `421B→128D`

## first_plus4 026A..030D

- **usa-retail:** 140 references; `026A`×9, `026C`×1, `02A0`×2, `02B0`×3, `02B2`×3, `02BE`×1, `02C0`×5, `02C1`×1, `02C2`×2, `02C3`×2, `02C4`×2, `02C5`×2, `02C6`×2, `02C7`×2, `02CC`×4, `02CE`×3, `0300`×87, `0302`×4, `0306`×2, `0309`×1, `030D`×2
- **pal-prototype-1994-11-29:** 140 references; `026A`×9, `026C`×1, `02A0`×2, `02B0`×3, `02B2`×3, `02BE`×1, `02C0`×5, `02C1`×1, `02C2`×2, `02C3`×2, `02C4`×2, `02C5`×2, `02C6`×2, `02C7`×2, `02CC`×4, `02CE`×3, `0300`×87, `0302`×4, `0306`×2, `0309`×1, `030D`×2
- **europe-retail:** 141 references; `026A`×9, `026C`×1, `02A0`×2, `02B0`×3, `02B2`×3, `02BE`×1, `02C0`×5, `02C1`×2, `02C2`×2, `02C3`×3, `02C4`×2, `02C5`×3, `02C6`×2, `02C7`×3, `02CC`×4, `02CE`×3, `0300`×86, `0302`×4, `0306`×2, `0309`×1

## second_plus2 04FB..0541

- **usa-retail:** 175 references; `04FB`×9, `04FD`×8, `04FF`×3, `0501`×6, `0503`×3, `0505`×12, `0507`×9, `0509`×7, `050B`×4, `050D`×11, `050F`×9, `0511`×7, `0513`×4, `0515`×4, `0517`×2, `0519`×4, `051B`×2, `051D`×4, `051F`×2, `0521`×4, `0523`×2, `052B`×8, `052D`×5, `052F`×9, `0531`×5, `0533`×10, `0535`×6, `0537`×7, `0539`×4, `0541`×5
- **pal-prototype-1994-11-29:** 175 references; `04FB`×9, `04FD`×8, `04FF`×3, `0501`×6, `0503`×3, `0505`×12, `0507`×9, `0509`×7, `050B`×4, `050D`×11, `050F`×9, `0511`×7, `0513`×4, `0515`×4, `0517`×2, `0519`×4, `051B`×2, `051D`×4, `051F`×2, `0521`×4, `0523`×2, `052B`×8, `052D`×5, `052F`×9, `0531`×5, `0533`×10, `0535`×6, `0537`×7, `0539`×4, `0541`×5
- **europe-retail:** 196 references; `04FB`×10, `04FD`×18, `04FF`×9, `0501`×6, `0503`×3, `0505`×6, `0507`×3, `0509`×12, `050B`×9, `050D`×7, `050F`×4, `0511`×11, `0513`×9, `0515`×7, `0517`×4, `0519`×4, `051B`×2, `051D`×4, `051F`×2, `0521`×4, `0523`×2, `0525`×4, `0527`×2, `052F`×8, `0531`×5, `0533`×9, `0535`×5, `0537`×10, `0539`×6, `053B`×7, `053D`×4

## first_inserted_space 030A..0310

- **usa-retail:** 8 references; `030D`×2, `030E`×2, `030F`×2, `0310`×2
- **pal-prototype-1994-11-29:** 8 references; `030D`×2, `030E`×2, `030F`×2, `0310`×2
- **europe-retail:** 0 references; none
- Europe-only numeric operands in trusted code: none
- Explained by trusted relocation projection: none
- **Unexplained Europe operands:** none

## second_inserted_space 053C..0546

- **usa-retail:** 7 references; `0541`×5, `0545`×2
- **pal-prototype-1994-11-29:** 7 references; `0541`×5, `0545`×2
- **europe-retail:** 4 references; `053D`×4
- Europe-only numeric operands in trusted code: `053D`
- Explained by trusted relocation projection: `053D`
- **Unexplained Europe operands:** none

## autojoy_hardware_registers 4218..421F

- **usa-retail:** 6 references; `4218`×2, `4219`×1, `421A`×2, `421B`×1
- **pal-prototype-1994-11-29:** 6 references; `4218`×2, `4219`×1, `421A`×2, `421B`×1
- **europe-retail:** 2 references; `4218`×1, `421A`×1
- Europe-only numeric operands in trusted code: none
- Explained by trusted relocation projection: none
- **Unexplained Europe operands:** none
