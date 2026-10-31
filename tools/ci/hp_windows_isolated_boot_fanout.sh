#!/usr/bin/env bash
# HP only: three independent offscreen Windows package launch contracts.
# Scripts and pass criteria are IDENTICAL to hosted serial acceptance.
set -euo pipefail
: "${RUNNER_TEMP:?missing runner scratch}"
: "${GITHUB_WORKSPACE:?missing checkout}"
[[ "${RUNNER_NAME:-}" == "hpmini-ur-recomp" ]] || { echo "HP_BOOT_FANOUT=refused_runner" >&2; exit 2; }
[[ "${GITHUB_REPOSITORY:-}" == "gamesbyian/UR-Recomp" ]] || { echo "HP_BOOT_FANOUT=refused_repo" >&2; exit 2; }
[[ "${GITHUB_REF:-}" == "refs/heads/main" ]] || { echo "HP_BOOT_FANOUT=refused_ref" >&2; exit 2; }
[[ "${GITHUB_EVENT_NAME:-}" == "push" || "${GITHUB_EVENT_NAME:-}" == "workflow_dispatch" ]] || {
  echo "HP_BOOT_FANOUT=refused_event" >&2; exit 2;
}
# The checkout is the Actions Bash working directory on Windows. The
# GITHUB_WORKSPACE environment value can contain backslashes that Bash
# cannot use as a script path, so keep the same relative paths as hosted CI.
scripts=(
  "tools/ci/windows_package_special_path.sh"
  "tools/ci/windows_package_readonly_unicode.sh"
  "tools/ci/windows_package_default_appdata.sh"
)
labels=(special readonly appdata)
pids=()
for i in 0 1 2; do
  [[ -f "${scripts[$i]}" ]] || { echo "HP_BOOT_FANOUT=missing_script" >&2; exit 2; }
done
hp_boot_join() {
  for pid in "${pids[@]}"; do
    wait "$pid" || true
  done
}
trap hp_boot_join EXIT
for i in 0 1 2; do
  log="$RUNNER_TEMP/hp-isolated-boot-${labels[$i]}.log"
  rm -f -- "$log"
  bash "${scripts[$i]}" >"$log" 2>&1 &
  pids+=("$!")
done
echo "HP_BOOT_FANOUT=started count=3"
fail=0
for i in 0 1 2; do
  rc=0
  wait "${pids[$i]}" || rc=$?
  log="$RUNNER_TEMP/hp-isolated-boot-${labels[$i]}.log"
  echo "===== HP isolated package check: ${labels[$i]} exit=$rc ====="
  cat "$log"
  if [[ "$rc" -ne 0 ]]; then
    fail=1
    echo "HP_BOOT_FANOUT=check_failed check=${labels[$i]} rc=$rc" >&2
  fi
done
trap - EXIT
if [[ "$fail" -ne 0 ]]; then
  echo "HP_BOOT_FANOUT=failed; no acceptance from this concurrent trial" >&2
  exit 1
fi
echo "HP_BOOT_FANOUT=passed count=3"
