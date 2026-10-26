# CI evidence retention: read-only producer metadata preflight

Use GitHub Actions metadata **before deciding to rerun a costly producer**.
This supplements the local typed receipt index in
tools/index_ci_receipts.py and the live agent integration preflight. It
does not download, preserve or republish raw private artifacts.

    python3 tools/artifact_retention_preflight.py \
      --live-run-id 40252059691 \
      --expected-sha d5fb2dd14ecf42eb5a9424bd5da53cd96782daad \
      --json-out /tmp/artifact-retention.json

Uses the repository's existing read-only Python API transport in
`tools/ops_live_status.py`, with optional `GH_TOKEN` or
`GITHUB_TOKEN` for authenticated Actions access. No separate
GitHub CLI dependency or custom HTTP implementation. Offline
replay accepts a saved GitHub runs/{id} response and its original
runs/{id}/artifacts?per_page=100 response through --saved-run and
--saved-artifacts. The source/identity/availability checks are
fail-closed, and a partial API page is **not** a complete census.

The report records observed artifact IDs, bounded artifact names, outer
GitHub SHA256 digest *as metadata*, expiration timestamps, estimated
hours to expiry, exact expected workflow-run head matching, and whether
the producer run passed. Missing --expected-sha is UNKNOWN, not
source-equal. Metadata ready for independent byte audit is NOT proof
that an artifact is currently downloadable, has good bytes, contains
a particular binary, is safe to share, or qualifies the release. A
synthetic PR merge's run head may not equal a developer's PR head or
the actual built checkout; inspect producer manifest receipts before
making source-equality assertions.

When an artifact is near expiry, route an authorized **rights-safe
receipt** to the owning existing PR/vault, not ROM or player save bytes
to a new public artifact. A different ZIP SHA256 or PE SHA256 is still
a distinct Windows candidate. Physical Windows and 45 genuine
original/native game events require their own independent acceptance.
No GitHub write, artifact download or retention extension is attempted.

Synthetic contract tests:

    python3 -m unittest -v tests.unit.test_artifact_retention_preflight
