# Fixed-denominator progress calculator (Windows beta v1)

The working inventory is [PROGRESS-INVENTORY.json](PROGRESS-INVENTORY.json); run the stdlib-only calculator from the repository root:

```sh
python3 tools/progress_calculator.py --format markdown
python3 tools/progress_calculator.py --format json --accepted-events 0
python3 -m unittest discover -s tests -p 'test_progress_calculator.py'
```

**Initial deterministic inventory result (2026-10-22): 48.50% provisional engineering maturity, 0% independently accepted inventory.** This is a *new metric*, not a decrease from the historical 60% subjective estimate; compare only future measurements using the same frozen v1 criteria and stage rules. Seven? No: eight of eleven inventory items have some evidence (six tested and two implemented); three remain planned. The source evidence is historical or bounded, not a current physical release assertion.

Fixed weights total 100. Each item earns 0% of its weight when planned, 50% when implemented, 75% when bounded-source tested, and 100% only after separately evidenced independent acceptance. This engineering metric rewards shipped and tested capability while withholding the last quarter for actual acceptance. It must **never** be described as percentage of formal release certification or as audited finished software. Changing weights, IDs, version or stage multipliers fails validation instead of silently shifting the goalposts. GitHub PR URLs are reviewable evidence pointers but do not in themselves prove the underlying state. Owners should audit and challenge every initial classification.

The calculator reads the unmodified [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json) to report independently awarded QA gates. Complete USA events must be supplied with `--accepted-events` only after reading their authoritative census; omitted counts are displayed as unknown, not assumed zero. Gate and event counters never determine maturity credit implicitly.

Future updates should append evidence-backed milestones to [PROGRESS-CHANGELOG.json](PROGRESS-CHANGELOG.json), then change an item's status only after the associated validation on a pinned exact source is documented. A regression lowers a status and therefore its points. Proposing scope expansion means introducing version v2, **not changing v1**. When v1 is superseded, retain this version, its weights, its scorer and its baseline for comparable historical charts.

Initial QA status: 0/12 release gates on the October 19 official ledger; 0/45 complete events on the current work queue. No end-to-end physical acceptance was conducted to create this calculator. The acceptance inventory is an initial operational model, with independent classification review still advised, and remains separate from any formal QA promotion.
