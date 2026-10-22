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

set -u

detect_display() {
    for d in "${DISPLAY:-}" ":1" ":0"; do
        [ -z "$d" ] && continue
        if DISPLAY="$d" xset q >/dev/null 2>&1; then
            echo "$d"
            return 0
        fi
    done
    return 1
}

is_screen_locked() {
    local out
    out=$(gdbus call --session \
        --dest org.gnome.ScreenSaver \
        --object-path /org/gnome/ScreenSaver \
        --method org.gnome.ScreenSaver.GetActive 2>/dev/null || true)
    echo "$out" | grep -q "true"
}

are_monitors_configured() {
    local xr_cur
    xr_cur=$(xrandr --current 2>/dev/null || true)
    echo "$xr_cur" | grep -q "^DP-1-2\.1 connected primary 3840x2160+0+400 " && \
    echo "$xr_cur" | grep -q "^DP-1-2\.8 connected 1440x2560+3840+0 left " && \
    echo "$xr_cur" | grep -q "^HDMI-1 connected 3440x1440+5280+1120 "
}

LOCK_FILE="/tmp/wake-all-monitors-${UID}.lock"
DEBOUNCE_SEC=15

wake_and_restore() {
    local reason="$1"
    local now
    now=$(date +%s)
    if [ -f "$LOCK_FILE" ]; then
        local last
        last=$(cat "$LOCK_FILE" 2>/dev/null || echo 0)
        if [ $((now - last)) -lt "$DEBOUNCE_SEC" ]; then
            return 0
        fi
    fi
    echo "$now" > "$LOCK_FILE"

    local disp
    disp=$(detect_display) || return 0
    export DISPLAY="$disp"

    echo "[$(date -Iseconds)] Triggered monitor wake ($reason) on DISPLAY=$DISPLAY"

    xset dpms force on >/dev/null 2>&1 || true

    for delay in 2 3; do
        sleep "$delay"
        xset dpms force on >/dev/null 2>&1 || true

        # Fast-path: check cached Xorg state without re-probing DDC/EDID or reallocating PRIME dmabufs.
        if are_monitors_configured; then
            break
        fi

        # Query xrandr only when a monitor actually lost its mode/CRTC after sleep.
        local xr_state
        xr_state=$(xrandr --query 2>/dev/null || true)

        if echo "$xr_state" | grep -q "^DP-1-2.1 connected" && \
           echo "$xr_state" | grep -q "^DP-1-2.8 connected" && \
           echo "$xr_state" | grep -q "^HDMI-1 connected"; then
            xrandr \
                --output DP-1-2.1 --primary --mode 3840x2160 --pos 0x400 --rotate normal \
                --output DP-1-2.8 --mode 2560x1440 --pos 3840x0 --rotate left \
                --output HDMI-1 --mode 3440x1440 --pos 5280x1120 --rotate normal >/dev/null 2>&1 || true
            xset dpms force on >/dev/null 2>&1 || true
            if are_monitors_configured; then
                break
            fi
        fi
    done

    date +%s > "$LOCK_FILE"
}

# Background watcher 1: Monitor DPMS transitions (Off/Standby/Suspend -> On) on keyboard wake
watch_dpms() {
    local prev_state="On"
    while true; do
        local disp
        if disp=$(detect_display); then
            local cur_state
            cur_state=$(DISPLAY="$disp" xset q 2>/dev/null | awk '/Monitor is / {print $3}')
            if [ -n "$cur_state" ]; then
                if [ "$prev_state" != "On" ] && [ "$cur_state" = "On" ]; then
                    # Ignore spurious HPD/DPMS wake pulses while GNOME lock screen is active.
                    if ! is_screen_locked; then
                        wake_and_restore "DPMS $prev_state -> On" &
                    fi
                fi
                prev_state="$cur_state"
            fi
        fi
        sleep 2
    done
}

watch_dpms &
DPMS_PID=$!
trap 'kill $DPMS_PID 2>/dev/null || true' EXIT

# Watcher 2: Listen for GNOME ScreenSaver WakeUpScreen and ActiveChanged(false) D-Bus signals
dbus-monitor --session "type='signal',interface='org.gnome.ScreenSaver'" | \
while read -r line; do
    if echo "$line" | grep -qE "member=WakeUpScreen|boolean false"; then
        wake_and_restore "GNOME ScreenSaver signal: $line" &
    fi
done
