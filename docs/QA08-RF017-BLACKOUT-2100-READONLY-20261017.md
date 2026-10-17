# QA-08: current RF017 result blackout INIDISP source boundary, one-shot

**Diagnostic-only stacked on clean product #1780. Do not merge into shipping.**

The strict source-authorized original 2014 Snes9x callback4015 is black at all 57,344 real 256x224 pixels; native current RF017+V0 guest4016 is nonblack at 53,667. Original independently observed $2100 source value remains 80 at postrun4015/4016; its guest CPU writes 02,04,06,08,0A,0C,0E at original source frames 4017..4023 V230/231. An *older, different guest* Windows source epoch c782.. observed CPU + raster replay source frame offsets; that is not evidence of the **current RF017** phase.

This bounded one-shot probe records **actual current** Windows CPU, DMA, HDMA and host replay $2100 writes with source tags and V/H, twelve native effective three-line PPU INIDISP states at guests 4015/4016/4017/4022 and three corresponding live source pixels at guest4016. It requires actual 5,484 guest CRC transcript b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568, controller exact route ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194, and game/core revision pins 10b864b9/075fbe4c. No change to $2100 writes, guest/NMI clock, PPU brightness, pixel output, 256x224 source, 7:6, 342-wide, 4x fallback, Modern persistence, HD art, independent release ledger or release status.

A same-source current 4016 PPU state of 02 plus CPU $2100=02 already delivered before native frame4016, contrasted with source 2014 original 4016 still 80, would localize the **upstream CPU-to-render field phase**, not justify painting black, shifting output, or adopting a global brightness LUT. If PPU $2100 is actually 80 while rendered nonblack, investigate the real PPU render state ordering in the graphics lane. A source-epoch discrepancy requires rejection, not reinterpretation.

Retain bounded ZIP JSON and PR/runs as provenance. Close this temporary diagnostic PR without merge after extracting compact machine evidence and update the single graphics source authority docs/QA08-RESULT-GREY-PHASE-112-CYCLE-20261017.md. Clean production #1780 remains on hold for independent integrated Windows/QA-08/10 acceptance.
