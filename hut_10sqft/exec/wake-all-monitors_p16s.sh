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

# @summary: Detect an active and reachable X11 display.
# @param: None directly (inspects environment variable $DISPLAY, then falls back to ":1", ":0").
# @return: 0 if an active X display is reachable (prints display string e.g. ":1" to stdout);
#          1 if no reachable X display is found.
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

# @summary: Check if GNOME ScreenSaver / lock screen is currently active.
# @param: None.
# @return: 0 (true) if screen is locked; 1 (false) otherwise.
is_screen_locked() {
    local out
    out=$(gdbus call --session \
        --dest org.gnome.ScreenSaver \
        --object-path /org/gnome/ScreenSaver \
        --method org.gnome.ScreenSaver.GetActive 2>/dev/null || true)
    echo "$out" | grep -q "true"
}

# @summary: Fast-path check verifying the 3 target monitors (EDID-matched Sceptre, Dell, and Asus) are active with expected modes and orientations.
# @param: None (queries cached Xorg state via xrandr --current --verbose without mutating display state).
# @return: 0 if primary 4K landscape (Sceptre), portrait-left 4K (Dell), and ultrawide (Asus) are active; 1 otherwise.
are_monitors_configured() {
    python3 -c "
import re
import subprocess
import sys

try:
    out = subprocess.check_output(['xrandr', '--current', '--verbose'], timeout=2).decode('utf-8', errors='ignore')
except Exception:
    sys.exit(1)

def parse_edid(hex_str):
    try:
        raw = bytes.fromhex(hex_str)
        if len(raw) >= 12:
            m = int.from_bytes(raw[8:10], 'big')
            c1 = chr(((m >> 10) & 0x1f) + 64)
            c2 = chr(((m >> 5) & 0x1f) + 64)
            c3 = chr((m & 0x1f) + 64)
            mfg = f'{c1}{c2}{c3}'
            prod = int.from_bytes(raw[10:12], 'little')
        else:
            mfg, prod = '', 0
        txt = ''.join(chr(b) if 32 <= b < 127 else ' ' for b in raw)
        return {'mfg': mfg, 'prod': prod, 'txt': txt}
    except Exception:
        return {'mfg': '', 'prod': 0, 'txt': ''}

edid_map = {}
line_map = {}
curr = None
edid_hex = ''
for line in out.splitlines():
    if ' connected' in line:
        if curr and edid_hex:
            edid_map[curr] = parse_edid(edid_hex)
        curr = line.split()[0]
        line_map[curr] = line
        edid_hex = ''
    elif ' disconnected' in line:
        if curr and edid_hex:
            edid_map[curr] = parse_edid(edid_hex)
        curr = None
        edid_hex = ''
    elif curr and line.startswith('\t\t') and len(line.strip()) == 32:
        edid_hex += line.strip()

if curr and edid_hex:
    edid_map[curr] = parse_edid(edid_hex)

dell = next(
    (c for c, d in edid_map.items()
     if (d['mfg'] == 'DEL' and (d['prod'] == 17262 or 'U3225QE' in d['txt']))
     or ('U3225QE' in d['txt'] or ('DELL' in d['txt'] and '32' in d['txt']))),
    None
)
sceptre = next(
    (c for c, d in edid_map.items()
     if (d['mfg'] == 'SPT' and (d['prod'] == 3240 or 'Z32' in d['txt']))
     or ('Sceptre' in d['txt'] or 'Z32' in d['txt'])),
    None
)
asus = next(
    (c for c, d in edid_map.items()
     if (d['mfg'] in ('AUS', 'ASU') and (d['prod'] == 13365 or 'VG34V' in d['txt']))
     or ('VG34V' in d['txt'] or 'ASUS' in d['txt'])),
    None
)

if not (dell and sceptre and asus):
    sys.exit(1)

sceptre_ok = bool(re.search(r' connected primary 3840x2160\+[0-9]+\+[0-9]+ ', line_map.get(sceptre, '')))
dell_ok = bool(re.search(r' connected 2160x3840\+[0-9]+\+[0-9]+ .*?\bleft\b', line_map.get(dell, '')))
asus_ok = bool(re.search(r' connected 3440x1440\+[0-9]+\+[0-9]+ ', line_map.get(asus, '')))

sys.exit(0 if (sceptre_ok and dell_ok and asus_ok) else 1)
" >/dev/null 2>&1
}

# @summary: Parse EDID from xrandr and apply multi-monitor layout matching specific monitors.
# @param: None (queries xrandr --verbose on current $DISPLAY).
# @return: 0 if all 3 monitors were identified and layout was applied; 1 otherwise.
apply_layout_by_edid() {
    python3 -c "
import subprocess
import sys

try:
    out = subprocess.check_output(['xrandr', '--verbose'], timeout=5).decode('utf-8', errors='ignore')
except Exception:
    sys.exit(1)

def parse_edid(hex_str):
    try:
        raw = bytes.fromhex(hex_str)
        if len(raw) >= 12:
            m = int.from_bytes(raw[8:10], 'big')
            c1 = chr(((m >> 10) & 0x1f) + 64)
            c2 = chr(((m >> 5) & 0x1f) + 64)
            c3 = chr((m & 0x1f) + 64)
            mfg = f'{c1}{c2}{c3}'
            prod = int.from_bytes(raw[10:12], 'little')
        else:
            mfg, prod = '', 0
        txt = ''.join(chr(b) if 32 <= b < 127 else ' ' for b in raw)
        return {'mfg': mfg, 'prod': prod, 'txt': txt}
    except Exception:
        return {'mfg': '', 'prod': 0, 'txt': ''}

conn_map = {}
curr = None
edid_hex = ''
for line in out.splitlines():
    if ' connected' in line:
        if curr and edid_hex:
            conn_map[curr] = parse_edid(edid_hex)
        curr = line.split()[0]
        edid_hex = ''
    elif ' disconnected' in line:
        if curr and edid_hex:
            conn_map[curr] = parse_edid(edid_hex)
        curr = None
        edid_hex = ''
    elif curr and line.startswith('\t\t') and len(line.strip()) == 32:
        edid_hex += line.strip()

if curr and edid_hex:
    conn_map[curr] = parse_edid(edid_hex)

# Match target displays specifically by manufacturer ID and product/model identifier to avoid
# ambiguity with other Dell displays or generic devices, with printable brand text as secondary fallback.
# - Dell U3225QE: mfg DEL (0x10ac), prod_id 17262 (0x436e), model U3225QE
# - Sceptre Z32:   mfg SPT (0x4e14), prod_id 3240 (0x0ca8), model Z32
# - ASUS VG34V:    mfg AUS (0x06b3), prod_id 13365 (0x3435), model VG34V
dell = next(
    (c for c, d in conn_map.items()
     if (d['mfg'] == 'DEL' and (d['prod'] == 17262 or 'U3225QE' in d['txt']))
     or ('U3225QE' in d['txt'] or ('DELL' in d['txt'] and '32' in d['txt']))),
    None
)
sceptre = next(
    (c for c, d in conn_map.items()
     if (d['mfg'] == 'SPT' and (d['prod'] == 3240 or 'Z32' in d['txt']))
     or ('Sceptre' in d['txt'] or 'Z32' in d['txt'])),
    None
)
asus = next(
    (c for c, d in conn_map.items()
     if (d['mfg'] in ('AUS', 'ASU') and (d['prod'] == 13365 or 'VG34V' in d['txt']))
     or ('VG34V' in d['txt'] or 'ASUS' in d['txt'])),
    None
)

if dell and sceptre and asus:
    cmd = [
        'xrandr',
        '--output', sceptre, '--primary', '--mode', '3840x2160', '--pos', '0x1680', '--rotate', 'normal',
        '--output', dell, '--mode', '3840x2160', '--pos', '3840x0', '--rotate', 'left',
        '--output', asus, '--mode', '3440x1440', '--pos', '6000x2400', '--rotate', 'normal'
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.exit(0)
sys.exit(1)
" >/dev/null 2>&1
}

LOCK_FILE="/tmp/wake-all-monitors-${UID}.lock"
DEBOUNCE_SEC=15

# @summary: Wake and restore display layouts if debounce window has elapsed.
# @param reason: String describing the wake trigger (e.g. DPMS change, GNOME ScreenSaver signal).
# @return: 0 if successfully restored or if debounced; 1 on failure.
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

        # Dynamically map and restore monitors by EDID vendor/model
        if apply_layout_by_edid; then
            xset dpms force on >/dev/null 2>&1 || true
            if are_monitors_configured; then
                break
            fi
        else
            # Fallback for known static connector names if dynamic EDID lookup had not completed
            local xr_state
            xr_state=$(xrandr --query 2>/dev/null || true)
            if echo "$xr_state" | grep -q "^DP-1-2 connected" && \
               echo "$xr_state" | grep -q "^DP-1-0 connected" && \
               echo "$xr_state" | grep -q "^HDMI-1 connected"; then
                xrandr \
                    --output DP-1-2 --primary --mode 3840x2160 --pos 0x1680 --rotate normal \
                    --output DP-1-0 --mode 3840x2160 --pos 3840x0 --rotate left \
                    --output HDMI-1 --mode 3440x1440 --pos 6000x2400 --rotate normal >/dev/null 2>&1 || true
                xset dpms force on >/dev/null 2>&1 || true
                if are_monitors_configured; then
                    break
                fi
            fi
        fi
    done

    date +%s > "$LOCK_FILE"
}

# Background watcher 1: Monitor DPMS transitions (Off/Standby/Suspend -> On) on keyboard wake
# @summary: Polling loop monitoring X11 DPMS state transitions to trigger display wake.
# @param: None.
# @return: Runs indefinitely in background until terminated.
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
