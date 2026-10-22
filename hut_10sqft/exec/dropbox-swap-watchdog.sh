#!/usr/bin/env bash

# Copyright 2026 Kinu Garage
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

LOG_TAG="dropbox-swap-watchdog"
# Default upper limit of Dropbox swap usage: 1 GB (1048576 kB)
MAX_SWAP_KB="${DROPBOX_MAX_SWAP_KB:-$((1024 * 1024))}"
DROPBOX_CMD="${DROPBOX_CLI:-/usr/bin/dropbox}"

log_msg() {
    local msg="$*"
    logger -t "$LOG_TAG" "$msg" 2>/dev/null || true
    echo "[$(date -Iseconds)] [$LOG_TAG] $msg"
}

CURRENT_USER="${USER:-$(id -un)}"
PID="${DROPBOX_PID_OVERRIDE:-$(pgrep -u "$CURRENT_USER" -f '\.dropbox-dist/.*/dropbox' | head -n 1 || true)}"

if [[ -z "$PID" ]]; then
    log_msg "Dropbox daemon is not running. Nothing to do."
    exit 0
fi

STATUS_FILE="${DROPBOX_PROC_ROOT:-/proc}/$PID/status"
if [[ ! -r "$STATUS_FILE" ]]; then
    log_msg "Cannot read $STATUS_FILE for Dropbox PID=$PID. Exiting."
    exit 0
fi

SWAP_KB=$(awk '/^VmSwap:/ {print $2}' "$STATUS_FILE" 2>/dev/null || echo 0)
RSS_KB=$(awk '/^VmRSS:/ {print $2}' "$STATUS_FILE" 2>/dev/null || echo 0)
SWAP_KB="${SWAP_KB:-0}"
RSS_KB="${RSS_KB:-0}"

if (( SWAP_KB <= MAX_SWAP_KB )); then
    log_msg "Dropbox PID=$PID VmSwap is ${SWAP_KB} kB (VmRSS=${RSS_KB} kB), within limit (${MAX_SWAP_KB} kB). No action needed."
    exit 0
fi

log_msg "Dropbox PID=$PID VmSwap is ${SWAP_KB} kB (VmRSS=${RSS_KB} kB), exceeding limit (${MAX_SWAP_KB} kB). Checking sync status via '$DROPBOX_CMD status'..."
STATUS=$("$DROPBOX_CMD" status 2>/dev/null | head -n 1 || true)

if [[ "$STATUS" == "Up to date" ]]; then
    log_msg "Dropbox status is 'Up to date'. Executing '$DROPBOX_CMD stop' (PID=$PID)..."
    "$DROPBOX_CMD" stop

    for _ in {1..10}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            break
        fi
        sleep 1
    done

    log_msg "Executing '$DROPBOX_CMD start'..."
    "$DROPBOX_CMD" start

    NEW_PID=$(pgrep -u "$CURRENT_USER" -f '\.dropbox-dist/.*/dropbox' | head -n 1 || true)
    log_msg "Dropbox restarted successfully (new PID=${NEW_PID:-unknown})."
else
    log_msg "Dropbox status is '${STATUS}' (not 'Up to date'). Deferring restart to avoid interrupting active sync."
fi
