# ROM-free Baldosa Windows candidate: independent archive and source inspection

**Scope:** release engineering and QA handoff; **not** an acceptance gate, second
Windows packager, official release nomination or assertion of complete USA
original/native event fidelity. The sole mutable release authority remains
[`RELEASE-QUALITY-LEDGER.json`](RELEASE-QUALITY-LEDGER.json).

The existing native Windows build produces
`UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip`, a SHA-256 sidecar and a canonical
`BALDOSA-CANDIDATE-MANIFEST.json` inside the ZIP. A source revision and
three member digests are present, but a *self-described manifest* alone cannot
authenticate either its own data or the exact source used for the executable.
The historical extracted-CMD acceptance checked the executable member hash
while relying on the producer for the other immutable members.

The independent, ROM-free, OS-agnostic pre-extraction consumer now lives at
`tools/audit_baldosa_romless_candidate.py`. It verifies, before extracting or
launching anything:

- **Exact four-member canonical ZIP**: ordered, non-duplicated paths under a
  single fixed prefix; no unexpected ROM, save, run, extra file, directory,
  symlink or encrypted member; bounded decompression and archive size.
- **Exact immutable manifest**: UTF-8 canonical JSON, correct ROM-free product
  identity and pinned expected USA ROM digest; one ordered, SHA-256/size-bound
  record for the PE32+ candidate, CMD launcher and README.
- **Actual bytes**: bounded streaming SHA-256 and sizes of *each* member, plus
  the README's terminal source-revision line, checked against the manifest.
- **External identity, when supplied**: explicit checked-out source revision
  and independently acquired ZIP SHA-256. The result prints the original ZIP,
  executable, launcher and README hashes, with no ROM or profile bytes.

## Source- and artifact-pinned QA command

```sh
python3 tools/audit_baldosa_romless_candidate.py \
  --zip /path/to/UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip \
  --expected-revision <actual-checkout-revision> \
  --expected-zip-sha256 <independently-verified-inner-ZIP-sha256>
```

The `--expected-revision` should be the SHA actually checked out for the
candidate build, normally `git rev-parse HEAD` from the producing checkout.
On a GitHub `pull_request` run, `GITHUB_SHA` and the ZIP manifest may identify
a **synthetic test-merge commit**, not the PR contribution's
`pull_request.head.sha`. Record both, along with base SHA, workflow run,
artifact wrapper digest, inner ZIP digest and PE digest. Never label a
PR-test-merge binary as a post-merge `main` candidate.

If an independently verified ZIP digest is unavailable, the tool still
checks internal consistency but cannot establish provenance or authenticity.
The printed hashes do not certify Windows runtime behavior, 2 physical
controllers, safe persistence under power loss, full native 1P/2P journeys,
OS/audio/display compatibility or 45-event parity.

The existing `verify_baldosa_windows_extracted_launcher.py` calls this
inspection *before it creates an extraction root*, then rehashes the
extracted PE, CMD and README before any CMD invocation. Its evidence report
now retains checked manifest source and executable SHA. The existing Windows
CI passes the job's exact `GITHUB_SHA` as the expected revision and runs the
new ROM-free adversarial unit tests before compiling; no extra workflow,
runner, broad automatic trigger or new candidate producer is introduced.

**Adversarial tests:** `tests/unit/test_audit_baldosa_romless_candidate.py`
checks the real deterministic packager fixture, source/ZIP SHA mismatch,
tampered member, a self-consistent but independently untrusted rehash, extra
mutable member, reordered ZIP, redirected executable entry and invalid
ROM-bundling metadata.

**Release handoff:** once the owning lanes and independent QA agree on one
integrated source, run the *existing* Windows build from that exact merged
`main`, preserve its artifact bytes and independent ZIP/PE hashes, and verify
the same package across the end-to-end clean-root journey. Do not combine
one PR's raw profile evidence with another binary's ZIP hash or promote
`candidate.commit_sha` / `candidate.zip_sha256` until QA has independently
accepted the exact nominated candidate.
