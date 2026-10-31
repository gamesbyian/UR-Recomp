#!/usr/bin/env bash
# Hosted ready-PR and trusted main-push: the same three source-owned
# real Windows offscreen package checks may run concurrently.
# Owner HP remains restricted to its separately guarded main-only worker.
set -euo pipefail
: "${RUNNER_TEMP:?missing runner scratch}"
: "${GITHUB_WORKSPACE:?missing checkout}"
: "${TEST_PACKAGE:?missing verified package}"
: "${PACKAGE_USER_DATA:?missing package user-data root}"
[[ "${GITHUB_REPOSITORY:-}" == "gamesbyian/UR-Recomp" ]] || { echo "HOSTED_BOOT_FANOUT=refused_repo" >&2; exit 2; }
if [[ "${GITHUB_EVENT_NAME:-}" == "pull_request" ]]; then
  [[ "${GITHUB_REF:-}" =~ ^refs/pull/[0-9]+/merge$ ]] || { echo "HOSTED_BOOT_FANOUT=refused_ref" >&2; exit 2; }
elif [[ "${GITHUB_EVENT_NAME:-}" == "push" ]]; then
  [[ "${GITHUB_REF:-}" == "refs/heads/main" ]] || { echo "HOSTED_BOOT_FANOUT=refused_ref" >&2; exit 2; }
else
  echo "HOSTED_BOOT_FANOUT=refused_event" >&2
  exit 2
fi
[[ "${RUNNER_OS:-}" == "Windows" ]] || { echo "HOSTED_BOOT_FANOUT=refused_os" >&2; exit 2; }
[[ -n "${RUNNER_NAME:-}" && "${RUNNER_NAME:-}" != "hpmini-ur-recomp" ]] || {
  echo "HOSTED_BOOT_FANOUT=refused_runner" >&2; exit 2;
}
# Git Bash on Windows may see GITHUB_WORKSPACE with backslashes; Actions
# supplies the checkout as the working directory, so use relative paths.
scripts=(
  "tools/ci/windows_package_special_path.sh"
  "tools/ci/windows_package_readonly_unicode.sh"
  "tools/ci/windows_package_default_appdata.sh"
)
labels=(special readonly appdata)
for script in "${scripts[@]}"; do
  [[ -f "$script" ]] || { echo "HOSTED_BOOT_FANOUT=missing_script" >&2; exit 2; }
done
pids=()
join_all() {
  # Never abandon a descendant that can still write package evidence.
  for pid in "${pids[@]}"; do
    wait "$pid" || true
  done
}
trap join_all EXIT
for i in 0 1 2; do
  log="$RUNNER_TEMP/hosted-isolated-boot-${labels[$i]}.log"
  rm -f -- "$log"
  bash "${scripts[$i]}" >"$log" 2>&1 &
  pids+=("$!")
done
echo "HOSTED_BOOT_FANOUT=started count=3"
failed=0
for i in 0 1 2; do
  rc=0
  wait "${pids[$i]}" || rc=$?
  log="$RUNNER_TEMP/hosted-isolated-boot-${labels[$i]}.log"
  echo "===== hosted isolated package check: ${labels[$i]} exit=$rc ====="
  cat "$log"
  if [[ "$rc" -ne 0 ]]; then
    failed=1
    echo "HOSTED_BOOT_FANOUT=check_failed check=${labels[$i]} rc=$rc" >&2
  fi
done
trap - EXIT
if [[ "$failed" -ne 0 ]]; then
  echo "HOSTED_BOOT_FANOUT=failed; no acceptance from parallel canary" >&2
  exit 1
fi
echo "HOSTED_BOOT_FANOUT=passed count=3"
