# Checkpoint / finish structural island: USA 81:8050..82E0

Object code 0x14 dispatches to 81:8050. The handler rejoins the shared object-handler continuation at 81:82E1.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| entry_time_prefix | 178 | 81:8050..81:8101 (+0; sim 0.904; op 75; other 0) | 81:8050..81:8101 (+0; sim 0.904; op 75; other 0) | 81:8050..81:8101 (+0; sim 1.000; op 75; other 0) |
| frame_normalization_usa_shape | 22 | 81:8102..81:8117 (+0; sim 0.955; op 10; other 0) | none | 81:8102..81:8117 (+0; sim 1.000; op 10; other 0) |
| post_normalization | 125 | 81:8118..81:8194 (+0; sim 0.976; op 63; other 0) | 81:810A..81:8186 (-14; sim 0.944; op 63; other 0) | 81:8118..81:8194 (+0; sim 1.000; op 63; other 0) |
| lap_hud | 63 | 81:8195..81:81D3 (+0; sim 0.857; op 24; other 0) | 81:8187..81:81C5 (-14; sim 0.825; op 24; other 0) | 81:8195..81:81D3 (+0; sim 1.000; op 24; other 0) |
| late_pre_contractions | 60 | 81:81D4..81:820F (+0; sim 0.983; op 25; other 0) | 81:81C6..81:8201 (-14; sim 0.983; op 25; other 0) | 81:81D4..81:820F (+0; sim 1.000; op 25; other 0) |
| pal_delete_1 | 6 | none | none | 81:8210..81:8215 (+0; sim 1.000; op 3; other 0) |
| late_after_delete_1 | 17 | 81:8210..81:8220 (-6; sim 1.000; op 8; other 0) | 81:8202..81:8212 (-20; sim 1.000; op 8; other 0) | 81:8216..81:8226 (+0; sim 1.000; op 8; other 0) |
| pal_delete_2 | 6 | none | none | 81:8227..81:822C (+0; sim 1.000; op 3; other 0) |
| late_after_delete_2 | 17 | 81:8221..81:8231 (-12; sim 1.000; op 8; other 0) | 81:8213..81:8223 (-26; sim 1.000; op 8; other 0) | 81:822D..81:823D (+0; sim 1.000; op 8; other 0) |
| pal_delete_3 | 6 | none | none | 81:823E..81:8243 (+0; sim 1.000; op 3; other 0) |
| late_after_delete_3 | 15 | 81:8232..81:8240 (-18; sim 1.000; op 7; other 0) | 81:8224..81:8232 (-32; sim 1.000; op 7; other 0) | 81:8244..81:8252 (+0; sim 1.000; op 7; other 0) |
| pal_delete_4 | 7 | none | none | 81:8253..81:8259 (+0; sim 1.000; op 3; other 0) |
| late_after_delete_4 | 30 | 81:8241..81:825E (-25; sim 0.933; op 11; other 0) | 81:8233..81:8250 (-39; sim 0.867; op 11; other 0) | 81:825A..81:8277 (+0; sim 1.000; op 11; other 0) |
| pal_delete_5 | 4 | none | none | 81:8278..81:827B (+0; sim 1.000; op 4; other 0) |
| late_after_delete_5 | 101 | 81:825F..81:82C3 (-29; sim 0.901; op 38; other 0) | 81:8251..81:82B5 (-43; sim 0.891; op 38; other 0) | 81:827C..81:82E0 (+0; sim 1.000; op 38; other 0) |

## Lineage edits

Europe retail alone contracts the USA 22-byte frame-normalization block at 81:8102..8117 to 8 bytes at 81:8102..8109, contributing -14 bytes before the later shared PAL-line edits.

The PAL prototype and Europe both omit five instruction-aligned USA blocks later in the handler:
- 81:8210..81:8215 (6 bytes): 8a 99 39 0e a5 00 = TXA; STA $0E39,Y; LDA $00
- 81:8227..81:822C (6 bytes): 8a 99 3d 0e a5 00 = TXA; STA $0E3D,Y; LDA $00
- 81:823E..81:8243 (6 bytes): 8a 99 41 0e a5 00 = TXA; STA $0E41,Y; LDA $00
- 81:8253..81:8259 (7 bytes): 99 35 0e 8a 99 45 0e = STA $0E35,Y; TXA; STA $0E45,Y
- 81:8278..81:827B (4 bytes): ea ea ea ea = NOP; NOP; NOP; NOP

Those five deletions total 29 bytes. Therefore the PAL prototype finishes the handler at shift -29 relative to USA; Europe finishes at -43 after layering the earlier -14 timer contraction.
