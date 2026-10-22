#!/usr/bin/env bash
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

LOCK_FILE="/tmp/wake-all-monitors-${UID}.lock"

wake_and_restore() {
    local reason="$1"
    local now
    now=$(date +%s)
    if [ -f "$LOCK_FILE" ]; then
        local last
        last=$(cat "$LOCK_FILE" 2>/dev/null || echo 0)
        if [ $((now - last)) -lt 5 ]; then
            return 0
        fi
    fi
    echo "$now" > "$LOCK_FILE"

    local disp
    disp=$(detect_display) || return 0
    export DISPLAY="$disp"

    echo "[$(date -Iseconds)] Triggered monitor wake ($reason) on DISPLAY=$DISPLAY"

    for delay in 2 3; do
        sleep "$delay"
        xset dpms force on >/dev/null 2>&1 || true

        # Query xrandr to force NVIDIA/modesetting to re-probe DP MST daisy-chain & HDMI
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
        else
            # Fallback if a monitor is still waking up its HPD or unplugged
            xrandr --auto >/dev/null 2>&1 || true
        fi
    done
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
                    wake_and_restore "DPMS $prev_state -> On" &
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
