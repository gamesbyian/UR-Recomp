# Native build smoke optimization conversation transcript

Captured: 2026-10-03

Source: project conversation **Native Build Smoke Slowness**.

> The Native build and boot smoke gha workflow seems pretty slow. Is that expected?

The user approved investigation and optimization after observing long native UI evidence runs. The monolithic smoke workflow was split into a faster gate plus a separate Native UI evidence workflow, then the expensive evidence work was sharded into parallel capture jobs with aggregation while preserving atlas/artifact contracts.
