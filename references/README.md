# External reference corpus

## `reference/` versus `references/`

These names are intentionally distinct:

- `reference/` holds project-input/project-local reference material needed to reproduce work, including preserved ROM builds and historical tool packages.
- `references/` is the provenance-managed external research corpus: mirrored third-party evidence under `references/imported/`, project summaries under `references/notes/`, and this source catalogue.

Do not merge the directories merely because their names are similar.

This directory records public Uniracers / Unirally material that may help reverse engineering, validation, reimplementation, graphics study, or historical reconstruction.

This is a private computer-science research archive. Material stored here is reference evidence, not automatically project-owned code or art and not automatically intended for redistribution in any eventual release.

## Rules

1. Every item gets a source URL, retrieval date, and rights/licensing note in `catalog.yml`.
2. Pin GitHub sources to a commit where practical.
3. **Preservation is the default.** When an actually downloadable public artifact is useful to the research, mirror the artifact into this repository where technically practical even when ownership or redistribution status is unclear. Record that uncertainty instead of converting it into an artificial absence.
4. Keep mirrored third-party material under `references/imported/`; keep our summaries and technical observations under `references/notes/`. Every tracked imported artifact must also be classified in `references/imported/MANIFEST.json`; CI verifies its exact bytes and known upstream/source hashes.
5. Never silently promote imported material into project-owned implementation assets. If something is later reused in shipping code/art, evaluate that use separately.
6. Preserve original filenames when useful, plus hashes/revisions where practical, so provenance survives source-site disappearance or mutation.
7. External claims remain leads until reproduced against the project's supported ROM. Confirmed local findings belong in `docs/RESEARCH-LEDGER.md`. For executable/source imports, read `docs/THIRD-PARTY-CODE-AUDIT.md` before reusing implementation behavior.
8. Avoid duplicate ROM imports. The project's supported ROM baseline is handled separately at repository root.

## Provenance posture

For this research project, uncertainty about rights is metadata, not a reason to discard potentially important evidence. Entries should distinguish at least:

- clearly licensed / redistributable;
- publicly available, rights unclear;
- copyrighted reference material;
- source code under an upstream license;
- derived project analysis.

The corpus is deliberately provenance-first and preservation-oriented. A reference that later disappears should still leave enough material here to inspect what it actually contained and why it mattered.
