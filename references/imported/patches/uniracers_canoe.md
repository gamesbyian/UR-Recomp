# sluffy Uniracers Canoe patch

Recovered: 2026-09-28

Original public Google Drive file:
https://drive.google.com/file/d/1LXMcLucVMd5VOHVy_G3ucJhuBFLI18IS/view

Google Drive file ID:
`1LXMcLucVMd5VOHVy_G3ucJhuBFLI18IS`

Original title:
`uniracers_canoe.ips`

Drive metadata:
- created: 2018-03-30T22:04:19.933Z
- modified: 2018-03-30T22:04:36.874Z
- size: 295 bytes

Local mirror:
`references/imported/patches/uniracers_canoe.ips`

Hashes:
- SHA-256: `35b695d9cc0667d09f950a05cb3066ada5f0078a50818bc04d348f5ef4f852cf`
- SHA-1: `9320fecbbf6dadf55c6632c00ead2c599cf7f972`
- MD5: `5ac0d418e3eac532f1c06659762922a1`
- Git blob SHA: `29115366b88185ee9ac2bbb189d397770e66e789`

## Context

This patch comes from sluffy's 2018 SNES Classic / Canoe compatibility work on Uniracers. Surviving discussion shows multiple iterations while the community worked through the game's unusual active-display OAM behavior. The recovered Drive file's March 30, 2018 timestamps place it after the March 28 discussion of the latest revision, so it is a strong candidate for the final public version. Treat that chronology as an inference until another source explicitly identifies this exact file/hash as the final revision.

The patch is preserved as research evidence, not treated as project-owned code.

## IPS record inventory

The IPS contains seven records and no RLE records:

| ROM offset | Length | Data |
| --- | ---: | --- |
| `0x007FDC` | 4 | `47 5D B8 A2` |
| `0x01534C` | 5 | `22 00 FF BF 60` |
| `0x015714` | 6 | `22 36 FF BF 80 00` |
| `0x018B16` | 1 | `80` |
| `0x01E8D1` | 3 | `E1 FF 7F` |
| `0x01EA50` | 3 | `EB FF 7F` |
| `0x1FFF00` | 230 | injected code/data |

The two records beginning with opcode `22` are 65816 JSL hooks into bank `$BF`, where the patch installs its larger handler at the end of the 2 MiB ROM. The `0x7FDC` record is in the SNES header checksum/complement area and is consistent with updating header integrity after modification.

Injected payload, verbatim hex:

```
addb0dd008ad99158d04218023afa2207e29f009058fa2207e8ff1ff7f8d0421afa3207e290f09508fa3207e8ff4ff7fa9558d04216ba9048d7043a9008d7143a2e0ff8e7243a97f8d7443a9028d1043a2f0ff8e1243a97f8d1443a96f8fe0ff7fa90f8fe1ff7fa9838fe2ff7fa90c8fe3ff7fa9018fe4ff7fa9028fe5ff7fa9808fe6ff7fa9838fe7ff7fa90c8fe8ff7fa9018fe9ff7fa9608feaff7fa90f8febff7fa9838fecff7fa90c8fedff7fa9018feeff7fa9008fefff7fa9708ff0ff7fa9558ff1ff7fa9558ff2ff7fa9708ff3ff7fa9558ff4ff7fa9558ff5ff7fa9008ff6ff7f6b
```

## Next analysis

Apply the patch to the verified US baseline, disassemble the changed routines and injected bank-BF handler, and compare its strategy against Snes9x, MAME and jgenesis. Because this was designed for Canoe rather than accurate SNES hardware, it may reveal both the original game mechanism and the specific emulator behavior sluffy needed to compensate for.
