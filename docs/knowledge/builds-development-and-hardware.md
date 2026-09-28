# Builds, development history and hardware seams

## Preserved build corpus

The repository currently uses four ROM builds as a differential corpus:

- USA retail, canonical recompilation input;
- Europe retail;
- historical GoodSNES-labelled `Uniracers (Beta)`;
- 1994-11-29 PAL prototype released from a development cartridge.

Exact hashes and header facts belong in the generated ROM inventory, not here.

## Structural observations

The legacy beta differs from USA retail in only hundreds of isolated bytes while sharing the 45-stream RNC corpus.

The November PAL prototype also shares the full 45-stream RNC corpus with USA retail.

Europe retail changes seven decoded streams while leaving 38 unchanged.

This makes the corpus useful for separating:

- executable versus compressed-data changes;
- regional changes;
- late fixes;
- stable code signatures across nearby builds.

## Original development environment

Developer evidence identifies:

- SNasm, a bespoke 65816 macro assembler lineage;
- an SN Systems 65816 development kit;
- Super Magicom copier-based iteration;
- an Amiga-to-SNES link;
- SNES graphics and MIDI converters;
- a dedicated Unicycle Compression/Editor;
- an A0 plotter for Uniracers material.

Mike Dailly also said in 2008 that he had rediscovered old SNES framework source. No public copy has yet been found.

## Consequence for reverse engineering

Do not assume the binary reflects conventions from ca65, WLA-DX or Nintendo's official assemblers.

Repeated idioms may come from DMA's own framework and SNasm macros. Historical SNasm descendants are useful syntax/lineage evidence, but should not be treated as the exact 1993 build environment without proof.

## Copier-sensitive protection

Andrew Innes described discovering a behavioral difference between proper cartridges and DMA's copier/development setup, then using that distinction for anti-piracy logic.

This makes odd cartridge-, timing- or mapping-sensitive paths especially dangerous to dismiss as dead code.

The protection path is still unidentified.

## Hardware-sensitive rendering

Uniracers also deliberately depends on unusual active-display OAM behavior. This is separate from copy protection.

The combination means the project should be conservative about "fixing" strange low-level behavior until it has been classified.

## Audio

Colin Anderson is the credited music/SFX author. Preservation sources contain eight normal tracks plus two unused pieces.

A Software Creations driver-family attribution exists in secondary material, but the exact ROM driver still needs binary verification.

## Product implication

The build corpus and original-development history are not merely historical color. They provide differential tests and priors about how the binary was produced, where tool-generated structures may exist, and which unusual behaviors may be intentional.
