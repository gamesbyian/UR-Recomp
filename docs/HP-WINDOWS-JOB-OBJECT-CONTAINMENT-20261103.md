# HP Windows process-tree containment experiment

Status: experimental standalone helper, not connected to the live broker,
GHA service, runner hooks, or scheduled ChatGPT agents.

The new `tools/hp_windows_job_object.py` uses documented Win32 Job Objects
with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`. It launches the direct process
with `CREATE_SUSPENDED`, assigns its handle to the Job Object *before*
resuming the primary thread through a Toolhelp thread snapshot, and closes
the job on exit or launch failure.

The intent is to eliminate the gap between `Popen` and process containment:
a subprocess must not get a chance to spawn an untracked descendant before
assignment. A failed assignment or failed resume kills the suspended process
rather than allowing uncontained execution. It uses only Python standard
library `ctypes`; `pywin32` and `psutil` are not dependencies.

## Actual owner HP proof

`python -W error::ResourceWarning -m unittest discover -s tests/unit -p
test_hp_windows_job_object.py -v`

- Suspended launch, assignment, resume, standard output and clean exit PASS.
- Spawn a live 30-second grandchild, verify it is alive, close the parent
  Job Object, and verify the grandchild process handle signals within five
  seconds PASS.
- Inject resume failure and verify the suspended process never reaches the
  marker-write instruction PASS.
- Pipe handles close without `ResourceWarning` PASS.

This authentic HP proof is **not** Windows product release acceptance.

## Qualification needed before deployment

- Keep this helper as an independent, import-only prototype. Do not run
  user-submitted command strings or add new broker job kinds based only on
  these tests.
- Review and test under the real NETWORK SERVICE GHA runner identity;
  assignment may fail under nested or restricted Windows Job Objects.
  Such failures must remain fail-closed.
- Test nested processes, inherited stdout/stderr handles, cancellation,
  forced termination, process-exit code, and long-run resource limits.
- Integrate bounded stdout/stderr readers and output receipts with the
  contained process. Merely containing a process does not bound its output,
  memory, CPU usage or execution time.
- Add externally enforced maximum runtime, verified child-tree shutdown
  and durable receipt on every failure path. Test machine restart as a
  distinct, potentially uncertain outcome.
- Coordinate exclusive reservations with the existing native Windows GHA
  runner **before** enabling CPU-intensive tasks. Job Objects provide
  containment, not ownership of the machine's execution resources.
- Independently review the current exact source head and current full
  unit/hygiene CI before merge.

The existing standalone broker proof remains in
`docs/HP-SAFE-JOB-BROKER-PILOT-20261103.md` (PR #3102 as of this experiment).
Do not confuse a native containment unit test with installed runner hooks,
a service restart or deployed unattended execution.
