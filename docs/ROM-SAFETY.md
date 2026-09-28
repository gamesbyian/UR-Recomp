# ROM and Copyright Safety

## Do not commit

- commercial game ROMs;
- ROM fragments used as disguised redistribution;
- extracted graphics, music, sound samples, maps or other copyrighted assets;
- saves/states containing substantial proprietary data;
- bulk generated source that effectively reproduces proprietary ROM code;
- builds that embed the ROM.

## Appropriate project material

- hashes identifying supported revisions;
- verification/build scripts;
- reverse-engineering notes;
- symbols and addresses;
- reproducible analysis configuration;
- independently authored runtime/integration code;
- tests expressed as inputs, addresses, assertions or small factual state values;
- structural format documentation;
- transformation logic rather than bundled original content.

## Local layout

```text
private/
  Uniracers-USA.sfc
generated/
build/
```

These paths are ignored.

Before making the repo public, audit the full Git history, not merely the current tree.
