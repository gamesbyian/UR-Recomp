# Agent conversation preservation and diary provenance

This is a **source-preservation protocol**, not a promise that ChatGPT or other agents expose complete export APIs. It complements the [editorial guide](PRODUCTION-DIARY-EDITORIAL-GUIDE.md) and [episode index](EPISODE-PROVENANCE.json). GitHub is the canonical publication location; the Google Drive recovery Vault has a distinct purpose and must not become an uncontrolled mirror.

## Goals

1. Preserve **Ian's actual questions, ideas, instructions, corrections and decision language**, together with the agent responses and relevant verified tool outcomes whenever a genuine source export is available.
2. Preserve timestamps, source platform, session ID where permitted, subject/agent lane, completeness and source integrity without turning paraphrases into quotation evidence.
3. Allow an agent chronicler to connect specific statements to independent implementation and QA artifacts while preserving the distinction between *proposed*, *published*, *executed*, *reviewed* and *accepted*.
4. Be honest about missing conversation access. Current historic archives are often summaries. The project must not pretend a transcript exists simply because someone remembers its substance.

## Preservation classes

| Class | Meaning | Acceptable diary use |
| --- | --- | --- |
| `verbatim_export` | Actual source transcript exported by supported platform functionality, with explicit beginning/end and source identity | Quote exact visible text if approved for publication |
| `source_excerpt` | A fragment copied from an identified visible conversation, with completeness boundaries | Quote only contained spans, not inferred adjacent dialogue |
| `reconstructed_summary` | A human/agent-authored paraphrase based on accessible history and other sources | Paraphrase; **never claim verbatim coverage** |
| `agent_handoff` | An agent's own progress/status summary | Evidence about the agent's assertion; independently check implementation |
| `execution_artifact` | Exact-source CI/run/test/archive/hash record | Verify only the particular execution/output it actually covers |
| `unknown` | Inaccessible/unqualified record | Never source dialogue or technical success to it |

These classes are not ranked by writing quality. A succinct verbatim instruction can be more historically significant than a thousand-line execution trace.

## Ingestion steps

1. **Identify the source:** Which human/agent exchange or tool session is this? What are the verified date/timezone bounds, provider, repository, lane and task identity? Never manufacture these when absent.
2. **Obtain a legitimate export or visible excerpt:** Use documented platform export features, accessible chat content, or user-provided files. Do not infer that the chat assistant can silently export every session. Do not scrape inaccessible private sessions, credentials or other people's conversations.
3. **Redact before public commit:** Review for credentials, bearer tokens, email addresses, health/personal information, private Drive paths, stock ROM bytes/art, confidential code and large proprietary excerpts. Minimize sensitive context while preserving engineering meaning. Maintain a private source archive only if storage and access are authorized. Never place secrets or ROM assets in Git history.
4. **Preserve authenticity metadata:** hash the actual export bytes locally if available; record hash algorithm, source identity, collection date, original format, redaction transformation and completeness. If redacted, preserve *both* raw-source hash and published-redacted hash where handling permits, but don't publish any private location or secret.
5. **Create stable IDs:** `source_id` for the transcript or excerpt, `session_id` only if given, and unique `episode_id` for the diary. Link director questions to relevant agents' responses and GitHub evidence without claiming they share an underlying invisible session.
6. **Separate conversational claims from code outcomes:** a director instruction is an instruction, a worker's response is a proposal/claim, a commit is a write, a CI artifact is a bounded test, and the release ledger alone owns formal gate status.
7. **Write the narrative episode:** The first-person chronicler tells why the interaction mattered, who proposed what, how the evidence changed the conclusion and what remained unproved. Use direct quotes only from verified visible source text.
8. **Update the provenance index and diary:** Add `source_ids`, relative archive paths, dates, relevant PR numbers and explicit `source_coverage`. Record a reason for missing context. Do not silently expand a source's coverage beyond what it actually contains.
9. **Revisit later:** When new evidence overturns a hypothesis, write a dated correction or retrospective note. Do not rewrite the earlier state of knowledge as though the conclusion had been known all along.

## Proposed archive metadata (example, not a claim that this transcript exists)

```json
{
  "schema": "ur-agent-conversation-source/1",
  "source_id": "EXAMPLE-2026-10-20-visual-title",
  "capture_kind": "source_excerpt",
  "platform": "provided conversation excerpt",
  "observed_start": "2026-10-20",
  "observed_end": "2026-10-20",
  "time_precision": "date",
  "speaker_types": ["director", "agent"],
  "completeness": "partial",
  "source_sha256": null,
  "published_sha256": null,
  "redacted": false,
  "repo": "gamesbyian/UR-Recomp",
  "objective_id": null,
  "archive_path": null,
  "linked_episodes": [69],
  "linked_pr_numbers": [],
  "publication_review": "pending",
  "limitations": "Example metadata only. No underlying transcript is represented."
}
```

If an external exporter produces full JSONL trajectories, preserve the exact original bytes privately when authorized. Publish a **small sanitized representation** or digest/index rather than an enormous unreviewed recording, especially because tool observations can contain secrets and derived copyrighted content.

## Machine-readable episode index

[EPISODE-PROVENANCE.json](EPISODE-PROVENANCE.json) initially indexes the **71 retrospective episodes** and evidence links mechanically extracted from the rebuilt standard diary. The index is an aid to discovery, **not an independent audit**. Entries are explicitly marked `record_kind: retrospective_synthesis`, `verbatim_transcript_verified: false`, and `source_coverage: partial`; this is conservative and should only be upgraded with confirmed actual source material.

When a real transcript/excerpt is acquired, add a source registry entry (a future `CONVERSATION-SOURCES.json` if needed) and connect it through `source_ids`. Never silently change old coverage statuses because a later agent has a plausible reconstructed summary.

## Publication cadence and responsibility

An active chronicler should check for new director interactions, transcript exports and important agent reports at each scheduled diary run, **if the available interfaces allow it**. The guide targets 3–8 meaningful published episodes on active days, but an automation schedule must actually exist to make that happen. A guide in GitHub does **not** create a scheduled monitor or a capture service.

The chronicler can independently synthesize an accessible historical window; it cannot monitor chats it cannot see, recover invisible agent reasoning, or promise that an unavailable provider supports full export.

## Acceptance checklist

- Can a future reader locate or identify the source for the quotation?
- Does the archive specify whether it is verbatim, excerpted, reconstructed or missing?
- Are source identities, dates and any hashes real rather than guessed?
- Are director's original words distinguished from the agent's interpretation?
- Are PRs and tests linked as independent evidence rather than as proof that a prompt was obeyed?
- Is the publication safe from secrets, third-party private data and stock ROM content?
- Do standard and Cajun diary episodes still agree on exact facts, decisions and release holds?

If any answer is no, preserve the limitation openly. **The diary may be literary; its evidence cannot be fictional.**
