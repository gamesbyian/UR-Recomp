# QA04: identical no-serial controller reconnect ambiguity

This is a **first-party recovered negative reproducer**, not a correction or a
Windows/device acceptance test. It transcribes the source logic from
`native/product/controller_seat_assignment_policy.h` at Git blob
`bc42a1522bd5deb56f41ec8f70d5d83aa3f311a2`, checked against current
`main` during recovery. The same source was merged by PR #2198.

Run the original recovered C99 test:

```sh
cc -std=c99 -Wall -Wextra -Werror -pedantic -O2 \
  research/qa04/controller_same_key_reconnect_repro.c -o /tmp/ur-qa04-same-key
/tmp/ur-qa04-same-key
```

Expected diagnostic (exit zero **demonstrates the defect**, not a passing
product invariant):

```text
initial: A=0 B=1; after B-first reconnect: B=0 A=1
```

Two controllers with identical SDL GUIDs and no serial produce the same
`ur_controller_device_key`. Once both seats are vacated, the P2 device's
return is incorrectly labeled a P1 reclaim; the old P1 later takes P2.
The identical key supplies no credible device-specific identity, so a fix
needs a deliberate ambiguity policy and actual SDL/Windows review. Do not
merely assume the returned pad is its former P1 owner.

**Provenance:** Restricted Drive Incoming archive
`1C57qeOCaNH7EHxVDNZaM6qcy3W7SeCji`,
`UR-WINQA-01-2198-same-key-review-20261021.zip`, member `repro.c`,
SHA-256 `b79c249d6ba6a34ada84bf5384c5ce01f4aa83a59f083d1617b19b44dcc56452`.
Published `controller_same_key_reconnect_repro.c` preserves those bytes
exactly. The prior GitHub **PR #2198 comment** invocation was explicitly
safety-refused and has not been retried; this separate source/test publication
does not purport to complete that refused operation.

Owner action: design and test same-key ambiguity handling in the *actual*
seat assignment/header/host, challenge it with independent Windows QA,
and preserve no-steal and different-identity reconnect behavior. No
physical controller evidence, exact compiled game, human review, parity
or release gate credit is claimed.
