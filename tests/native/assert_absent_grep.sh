#!/usr/bin/env bash
# Shared, fail-closed negative diagnostic assertion for native QA scripts.
# Standalone '! grep -q' does NOT trigger bash errexit on a forbidden match.
# Always check the call's return value explicitly (|| exit 1).
assert_absent_grep() {
  local status
  if grep "$@"; then
    echo "::error::native acceptance observed a forbidden diagnostic marker" >&2
    return 1
  else
    status=$?
  fi
  if [ "$status" -ne 1 ]; then
    echo "::error::native acceptance could not inspect a diagnostic log (grep=$status)" >&2
    return 1
  fi
  return 0
}
