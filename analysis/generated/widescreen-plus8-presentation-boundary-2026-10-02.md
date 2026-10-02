# +8 Widescreen first presentation boundary

Date: 2026-10-02
Fixture: `tests/input/object-activation-dragster-tail.script`
Final discriminator run: GitHub Actions `36964990868`

## Classification

The original +8 "authoritative state divergence" was a harness false positive
over a host-presentation cadence shift. The first actual presentation failure
is host-renderer-owned.

## Event-relative boundary

| boundary | result |
| --- | --- |
| durable race state | matched 0/+8 |
| absolute guest cadence | +8 is consistently 3 frames earlier |
| center pixels through `object-tail-167` | exact match |
| first center regression | `object-tail-168`, 2 pixels at classic x=255 |
| guest OAM at `168` | byte-identical |
| BG-only at `168` | match |
| OBJ-only at `168` | match |
| first OBJ-only regression | `object-tail-169` |
| first OAM regression | `object-tail-172`, one slot with a one-pixel Y change |
| sprite limits disabled | first center regression still `168` |
| 0/255 pinned-window expansion disabled | first center regression still `168` |

## Ownership

At the first failure, independently rendered BG and OBJ surfaces still agree,
but their widened-host composite does not. The following event adds an
OBJ-raster divergence while guest OAM is still identical.

This excludes gameplay activation, course spatial semantics, preparation-list
ownership, the SNES 34-sliver limit, and the runner's pinned-window expansion
policy as causes of the first +8 failure.

The next renderer task should preserve the authentic 256-column center under
matched event-relative guest presentation state while allowing side-margin
exposure. Permanent Widescreen policy should not be chosen in this evidence PR.
