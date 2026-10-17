# Current-source RF-017 OAM DMA input boundary read-only check
Diagnostic-only stack on graphics PPU #1782 and clean product #1780.
Capture real source enum + $2102/$2103/$2104 PPU input chronology for guests
4029..4034 and 4173..4178; recognize a complete 544-byte zero-address
low/high OAM DMA by genuine native pointer/latch progression, not a guessed
frame shift. Compare the source payload SHA to correctly postrun-registered
2014 original field4032/4176 only at native host4030/4174 and report both
positive and negative controls, retaining only SHA, beam endpoints and
seven relevant OAM tile bytes. The same real 5484-frame RF-017 controller
and CRC identity from #1782 is mandatory. No original sprite raster, PPU,
CPU/APU clocks, Modern store, user data, ROM, HDLUT or release ledger edits.
This one-shot source probe is never promoted to Windows production; close
without merging after retaining compact source/provenance evidence.
