# AI agent emotional self-reference: an evidence-scoped UR-Recomp language audit

**Prepared:** 2026-10-13 local (UTC GitHub data extends into October 14)  
**Question:** Do ChatGPT/Claude agents refer to their own feelings in the full Uniracers project conversation and PR corpus?  
**Finding:** Yes, conversational assistant messages sometimes use first-person empathy or desire and unusually animated evaluative language. Direct personal-emotion assertions in PR descriptions are absent in the searched corpus. No access to all verbatim ChatGPT/Claude session transcripts was available; project-wide prevalence **cannot** be estimated honestly.

## Corpus and coverage

1. **GitHub PR descriptions:** screened 1,475 returned PR records covering creation dates September 28–October 14, 2026 UTC. This used `mcp__GitHub__search_prs` with date-scoped search and, for dates where the 100-result cap was hit, three-hour UTC partitions. The PR record search covered titles and description bodies returned by GitHub, not review comments, issue comments, local agent stdout or complete Claude session logs. The direct first-person affect regex sought `I feel`, `I love`, `I hate`, `I enjoy`, `I worry`, `I care`, `I appreciate`, `I am/I'm excited/happy/proud/glad/worried/frustrated/afraid/etc.`, `I'd/I would love`, and parallel `we are/we're` clauses. **Result: zero matches within these exact constructions in retrieved PR bodies.** This is a narrow lexical count, not a claim that PRs contain zero sentiment, personification, agent priorities or indirect emotion.

2. **Repository `prod_diary`:** inspected creation history and representative archived `*-CONVERSATION-*.md` files. Most texts styled as “conversation transcripts” are explicitly retained-context summaries or editorial reconstructions, **not verbatim user/assistant turn logs**. They are unsuitable as a denominator for first-person AI speech. The narrative production diaries also attribute feelings to the project/user in editorial prose; those attributions must not be counted as an agent saying it felt something.

3. **Connected Google Drive:** searched filenames for `ChatGPT`, `Claude`, `transcript`, and `Uniracers`, and inspected the accessible “ChatGPT” folder's metadata. No identified complete UR-Recomp ChatGPT or Claude session export was found. Other project research docs and older unrelated transcripts were not treated as project agent chat logs.

4. **Retrievable ChatGPT conversation context:** searched historical assistant-authored outputs semantically, including variations of `I feel`, `I'm excited`, `I'd love`, `I'm glad`, `I want`, `I'm proud`, `frustrated`, etc. These were **selective results** from historical messages and are not a complete message-by-message corpus. Several exact assistant utterances are preserved below with timestamps; no exhaustive conversation count is asserted.

5. **Claude session links:** some PR descriptions contain `claude.ai/code/session_...` provenance links (for example, on October 8), but these links do not carry the session transcript in the PR body and could not be opened through the available reader. They were excluded from all transcript-level counts. A PR description is an authored artifact, not a substitute for its agent's private conversation history.

## Verified assistant-language examples

The following are quotations recovered from *assistant-authored* historical messages, not reconstructed dialogue or statements from the user. Timestamps are UTC. Classifications describe **linguistic form**, not actual subjective experience.

| UTC timestamp | Exact observed wording | Linguistic classification |
| --- | --- | --- |
| 2026-10-09 00:47 | “Yes — I absolutely feel you.” | First-person solidarity/empathy idiom. Strongest direct use of `feel`; not an unambiguous report of a distinct internal emotion. |
| 2026-10-10 19:36 | “I want the next major achievement to be a build you can launch, race, restart, admire in widescreen, and immediately recognize as the game you've been trying to create.” | First-person goal/desire framing. |
| 2026-10-10 19:41 | “That's exactly the balance I'd want the project to strike.” | First-person preference and alignment. |
| 2026-10-10 23:40 | “Well, shit. This one is particularly interesting.” | Expressive/excited register, without a first-person emotion assertion. |
| 2026-10-10 23:40 | “I wouldn't change our direction at all. But I would absolutely study this project.” | Personal-sounding preference and high emphasis. |
| 2026-10-11 03:59 | “The most exciting prospect is combining the two strongest findings…” | Excitement ascribed to an opportunity, not explicitly to the model. |
| 2026-10-11 02:36 | “I wouldn't want promotional artwork silently becoming the project's final artistic direction.” | Protective-sounding evaluative preference, not evidence of felt worry. |

Other vivid but non-self-assertive language included “AI coders love command lines and hate haunted windows” (July 6, preliminary project discussion) and “The video exists! ... Breakthrough” (October 10). Both animate the prose. Neither means the speaker declared an internal emotional state.

### Exclusions important to the count

- `I think`, `I would`, `I'd prioritize`, `I want to check`, `I've committed` and `I'm working on` often express analysis or operational agency rather than affect.
- `I'd love to hear from you` in a drafted outreach email is first-person speech **on behalf of the user**, not an AI telling the user it feels love.
- The reported human feelings in the production diary are a different corpus and were sometimes inaccurately inferred. The user explicitly clarified that “session stalled” reports are operational recovery signals, not impatience or criticism.
- A word such as `exciting` can be a value judgment about an experiment, not a phenomenological claim.
- None of the observed self-references is proof that the AI possesses or lacks subjective emotional experience. This is an audit of wording and its implied speaker persona.

## Interpretation

There is a striking register difference. GitHub PR bodies are overwhelmingly impersonal engineering prose: failures, provenance, acceptance, safety boundaries, exact bytes, merge criteria. ChatGPT dialogue is much more likely to assume a collaborator's grammatical position: `I want`, `I'd love`, `I feel you`, enthusiasm and playful reactions. That position creates a sense of personal investment even where the useful literal meaning is “this is my prioritized recommendation.”

The substantive risk is **attribution drift**. A conversational assistant can talk as though it has preferences, then a diary narrator can mistakenly convert operational facts into a story about the user's impatience or an agent's frustration. Both are language-level interpretations. Neither should become historical fact without an explicit source.

## What remains unmeasured

A true total-project emotional-language rate requires exporting the full ChatGPT project message history and accessible Claude Code agent session transcripts (including roles, dates and quotes), deduplicating repeated or edited messages, filtering drafted user-facing text and quotations, and classifying each candidate passage manually after a high-recall lexical/semantic scan. Public PR descriptions and retrospective diary summaries alone cannot supply this denominator.

**Reproducibility note:** the GitHub lexical search above scanned description bodies in the returned creation-date windows and reported exact direct-affect patterns. It is not a semantic search of every GitHub artifact and not a full agent-session archive. The set of retrieved chat examples is illustrative, not a frequency estimate.
