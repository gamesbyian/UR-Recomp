# +16 Widescreen host-capacity acceptance

Date: 2026-10-03  
Workflow run: `37086273196`

## Result

The presentation-capacity ownership seam is accepted.

The first extra column remains the accepted PR #228 guest secondary-lane path.
The second extra column exists only in host/native presentation storage. No
synthetic guest `$03xx` descriptor lane is introduced.

For this controlled proof, the second-column provider is an independent
later-stock oracle. It is deliberately test scaffolding, not the production
content generator.

## Capacity acceptance

- accepted +8 path unchanged: **yes**
- +16 first-column events: **617**
- +16 host-shadow second-column events: **617**
- exact nearest-later-stock shadow matches: **617/617**
- second column advances one low-five-bit ring position: **yes**
- provider misses: **0**
- deterministic cleanup: **yes**
- protected preparation-fixture state equal: **yes**
- nearest later-stock observation range: **27..46 px**
- +24: **fail closed at bounded host-shadow capacity**

Exact shadow correspondence includes the full compound edge word and all 32
payload bytes, not only the low-five-bit ring coordinate.

## Liveness acceptance

The independent Dragster liveness fixture compares **61** common semantic
samples with **zero protected differences** in player position, camera,
progression state or the object-map prefix.

Both runs first change progression at semantic sample `liveness-004` with the
same payload:

- next checkpoint: 1
- finish gate: 1
- laps remaining: 1

Absolute guest frame differs by one: control **1231**, +16 **1232**. This is a
one-frame-later cadence difference, not earlier activation. The accepted
event-relative rule therefore remains intact.

## Negative evidence retained

Two attempts to use guest preparation itself as a deeper random-access provider
remain rejected:

- run `37083769287`: recursive `A59E`, 557 candidates, 31 exact matches,
  60 structural misses;
- run `37084288683`: cloned camera-biased full `A52F`, 314 candidates,
  zero exact matches.

## Architectural consequence

+16 no longer needs additional authoritative guest descriptor capacity. The
next production step is narrower: replace the oracle with a host-owned
random-access strip materializer backed by the recovered course/resource
presentation model, then rerun this exact-content and liveness contract before
widening final composition.
