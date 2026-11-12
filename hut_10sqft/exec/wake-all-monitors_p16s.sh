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

def find_display(displays, strict_fn, fallback_fn=None):
    match = next((c for c, d in displays.items() if strict_fn(d)), None)
    if not match and fallback_fn:
        match = next((c for c, d in displays.items() if fallback_fn(d)), None)
    return match

dell = find_display(
    edid_map,
    lambda d: d['mfg'] == 'DEL' and (d['prod'] == 17262 or 'U3225QE' in d['txt']),
    lambda d: 'U3225QE' in d['txt']
)
sceptre = find_display(
    edid_map,
    lambda d: d['mfg'] == 'SPT' and (d['prod'] == 3240 or 'Z32' in d['txt']),
    lambda d: 'Sceptre' in d['txt'] or 'Z32' in d['txt']
)
asus = find_display(
    edid_map,
    lambda d: d['mfg'] in ('AUS', 'ASU') and (d['prod'] == 13365 or 'VG34V' in d['txt']),
    lambda d: 'VG34V' in d['txt'] or 'ASUS' in d['txt']
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
def find_display(displays, strict_fn, fallback_fn=None):
    match = next((c for c, d in displays.items() if strict_fn(d)), None)
    if not match and fallback_fn:
        match = next((c for c, d in displays.items() if fallback_fn(d)), None)
    return match

dell = find_display(
    conn_map,
    lambda d: d['mfg'] == 'DEL' and (d['prod'] == 17262 or 'U3225QE' in d['txt']),
    lambda d: 'U3225QE' in d['txt']
)
sceptre = find_display(
    conn_map,
    lambda d: d['mfg'] == 'SPT' and (d['prod'] == 3240 or 'Z32' in d['txt']),
    lambda d: 'Sceptre' in d['txt'] or 'Z32' in d['txt']
)
asus = find_display(
    conn_map,
    lambda d: d['mfg'] in ('AUS', 'ASU') and (d['prod'] == 13365 or 'VG34V' in d['txt']),
    lambda d: 'VG34V' in d['txt'] or 'ASUS' in d['txt']
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

verify_secure_runtime_dir() {
    python3 -c '
import os, sys, stat
p = sys.argv[1]
try:
    if os.path.islink(p):
        sys.exit(1)
    st = os.stat(p)
    if not stat.S_ISDIR(st.st_mode):
        sys.exit(1)
    if st.st_uid != os.getuid():
        sys.exit(1)
    if (st.st_mode & 0o077) != 0:
        sys.exit(1)
    sys.exit(0)
except Exception:
    sys.exit(1)
' "$1"
}

if [ -n "${XDG_RUNTIME_DIR:-}" ] && [ -d "${XDG_RUNTIME_DIR}" ] && verify_secure_runtime_dir "${XDG_RUNTIME_DIR}"; then
    _DEFAULT_RUNTIME_DIR="${XDG_RUNTIME_DIR}"
else
    _DEFAULT_RUNTIME_DIR="${TMPDIR:-/tmp}/wake-all-monitors-${UID}"
    if ! mkdir -m 0700 "$_DEFAULT_RUNTIME_DIR" 2>/dev/null; then
        if ! verify_secure_runtime_dir "$_DEFAULT_RUNTIME_DIR"; then
            echo "Error: Insecure runtime directory: $_DEFAULT_RUNTIME_DIR" >&2
            exit 1
        fi
    fi
fi

LOCK_FILE="${LOCK_FILE:-${_DEFAULT_RUNTIME_DIR}/wake-all-monitors.lock}"
WINDOW_LAYOUT_FILE="${WINDOW_LAYOUT_FILE:-${_DEFAULT_RUNTIME_DIR}/window-layout.json}"
DEBOUNCE_SEC=15

# @summary: Snapshot geometry (x, y, width, height) of active top-level application windows.
# @param: None (queries X11 root window children via xwininfo on current $DISPLAY).
# @return: 0 if successfully saved or if monitors are not configured; 1 on failure.
save_window_layout() {
    local disp
    disp=$(detect_display) || return 0
    export DISPLAY="$disp"

    # Only save layout when all 3 monitors are verified healthy to avoid saving a transient/collapsed layout
    if ! are_monitors_configured; then
        return 0
    fi

    local target_dir
    target_dir=$(dirname "$WINDOW_LAYOUT_FILE")
    mkdir -p -m 0700 "$target_dir" 2>/dev/null || true

    local save_lock="${WINDOW_LAYOUT_FILE}.lock"
    if ! exec 201>"$save_lock"; then
        echo "Error: Failed to open save lock file: $save_lock" >&2
        return 1
    fi
    if ! flock -n 201 2>/dev/null; then
        return 0
    fi

    local ret=0
    python3 -c "
import json
import os
import re
import subprocess
import sys
import tempfile

target = sys.argv[1]
try:
    out = subprocess.check_output(['xwininfo', '-root', '-children'], timeout=3).decode('utf-8', errors='ignore')
except Exception as e:
    print(f'Error querying xwininfo: {e}', file=sys.stderr)
    sys.exit(1)

pattern = re.compile(
    r'^\s*(0x[0-9a-fA-F]+)\s+(\".*\"|\(has no name\)):\s+(\([^\)]*\))\s+(\d+)x(\d+)\+([-0-9]+)\+([-0-9]+)',
    re.M
)

wins = []
for wid, name, classes, w, h, x, y in pattern.findall(out):
    w, h, x, y = int(w), int(h), int(x), int(y)
    # Ignore tiny background helpers, full desktop root overlay, and desktop icon managers
    if w > 50 and h > 50 and w < 9000 and h < 9000 and 'Desktop Icons' not in name:
        wins.append({'id': wid, 'name': name, 'x': x, 'y': y, 'w': w, 'h': h})

if not wins:
    sys.exit(0)

target_dir = os.path.dirname(os.path.abspath(target))
tmp_path = None
try:
    os.makedirs(target_dir, mode=0o700, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=target_dir, prefix=f'{os.path.basename(target)}.{os.getpid()}.', delete=False) as tf:
        os.chmod(tf.name, 0o600)
        json.dump(wins, tf)
        tmp_path = tf.name
    os.replace(tmp_path, target)
    print(f'[{subprocess.check_output([\"date\", \"-Iseconds\"]).decode().strip()}] Saved geometry of {len(wins)} windows to {target}')
except Exception as e:
    if tmp_path and os.path.exists(tmp_path):
        try:
            os.remove(tmp_path)
        except Exception:
            pass
    print(f'Error saving window layout to {target}: {e}', file=sys.stderr)
    sys.exit(1)
" "$WINDOW_LAYOUT_FILE" || ret=$?
    flock -u 201 2>/dev/null || true
    return $ret
}

# @summary: Restore saved window geometries for active windows after display layout has stabilized.
# @param: None.
# @return: 0 if layout was restored or nothing to restore; 1 on error.
restore_window_layout() {
    local save_lock="${WINDOW_LAYOUT_FILE}.lock"
    if [ -f "$save_lock" ] && command -v flock >/dev/null 2>&1; then
        exec 201>"$save_lock"
        if ! flock -w 3 201 2>/dev/null; then
            echo "Warning: Timed out waiting for save lock $save_lock; skipping restoration" >&2
            return 1
        fi
        flock -u 201 2>/dev/null || true
    fi

    [ ! -f "$WINDOW_LAYOUT_FILE" ] && return 0
    if ! command -v xdotool >/dev/null 2>&1; then
        return 0
    fi

    local disp
    disp=$(detect_display) || return 0
    export DISPLAY="$disp"

    python3 -c "
import json
import os
import subprocess
import sys
import time

target = sys.argv[1]
if not os.path.exists(target):
    sys.exit(0)

try:
    with open(target) as f:
        wins = json.load(f)
except Exception:
    sys.exit(0)

# Allow Mutter constraint solver and desktop workarea to settle
time.sleep(0.5)

restored = 0
failed = 0
for win in wins:
    wid = win['id']
    x, y, w, h = win['x'], win['y'], win['w'], win['h']
    try:
        # Verify the window is still open on X11
        subprocess.check_output(['xdotool', 'getwindowgeometry', wid], timeout=1, stderr=subprocess.DEVNULL)
        res_m = subprocess.run(['xdotool', 'windowmove', wid, str(x), str(y)], timeout=1, stderr=subprocess.PIPE, text=True)
        res_s = subprocess.run(['xdotool', 'windowsize', wid, str(w), str(h)], timeout=1, stderr=subprocess.PIPE, text=True)
        if res_m.returncode == 0 and res_s.returncode == 0:
            restored += 1
        else:
            failed += 1
            err = res_m.stderr.strip() or res_s.stderr.strip() or 'unknown error'
            print(f'Failed to restore window {wid} ({win.get(\"name\", \"\")}): {err}', file=sys.stderr)
    except Exception:
        pass

if restored > 0:
    print(f'[{subprocess.check_output([\"date\", \"-Iseconds\"]).decode().strip()}] Restored geometry of {restored} windows from {target}')

if failed > 0:
    sys.exit(1)
" "$WINDOW_LAYOUT_FILE" >/dev/null || return 1
}

# @summary: Wake and restore display layouts if debounce window has elapsed.
# @param reason: String describing the wake trigger (e.g. DPMS change, GNOME ScreenSaver signal).
# @return: 0 if successfully restored or if debounced; 1 on failure.
wake_and_restore() {
    local reason="$1"
    if ! command -v flock >/dev/null 2>&1; then
        echo "Error: flock is required for wake locking" >&2
        return 1
    fi
    local flock_file="${LOCK_FILE}.flock"
    exec 200>"$flock_file"
    if ! flock -n 200; then
        # Another wake attempt is currently running. Wait for it to finish and check if monitors are configured.
        if flock -w 10 200; then
            if are_monitors_configured; then
                flock -u 200 2>/dev/null || true
                return 0
            fi
        else
            return 0
        fi
    fi

    local now
    now=$(date +%s)
    if [ -f "$LOCK_FILE" ]; then
        local last
        last=$(cat "$LOCK_FILE" 2>/dev/null || echo 0)
        if [ $((now - last)) -lt "$DEBOUNCE_SEC" ]; then
            flock -u 200 2>/dev/null || true
            return 0
        fi
    fi

    local disp
    disp=$(detect_display)
    if [ -z "$disp" ]; then
        flock -u 200 2>/dev/null || true
        return 0
    fi
    export DISPLAY="$disp"

    echo "[$(date -Iseconds)] Triggered monitor wake ($reason) on DISPLAY=$DISPLAY"

    xset dpms force on >/dev/null 2>&1 || true

    for delay in 2 3; do
        sleep "$delay"
        xset dpms force on >/dev/null 2>&1 || true

        # Fast-path: check cached Xorg state without re-probing DDC/EDID or reallocating PRIME dmabufs.
        if are_monitors_configured; then
            restore_window_layout
            break
        fi

        # Dynamically map and restore monitors by EDID vendor/model
        if apply_layout_by_edid; then
            xset dpms force on >/dev/null 2>&1 || true
            if are_monitors_configured; then
                restore_window_layout
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
                    restore_window_layout
                    break
                fi
            fi
        fi
    done

    date +%s > "$LOCK_FILE"
    flock -u 200 2>/dev/null || true
}

# Background watcher 1: Monitor DPMS transitions (Off/Standby/Suspend -> On) on keyboard wake
# @summary: Polling loop monitoring X11 DPMS state transitions to trigger display wake.
# @param: None.
# @return: Runs indefinitely in background until terminated.
watch_dpms() {
    local prev_state="On"
    local healthy_poll_count=0
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
                elif [ "$prev_state" = "On" ] && [ "$cur_state" != "On" ]; then
                    save_window_layout &
                elif [ "$cur_state" = "On" ]; then
                    # Periodically refresh layout while monitors are active and healthy
                    healthy_poll_count=$(( (healthy_poll_count + 1) % 15 ))
                    if [ "$healthy_poll_count" -eq 0 ]; then
                        save_window_layout &
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

# Watcher 2: Listen for GNOME ScreenSaver WakeUpScreen, ActiveChanged(false), and ActiveChanged(true) D-Bus signals
dbus-monitor --session "type='signal',interface='org.gnome.ScreenSaver'" | \
while read -r line; do
    if echo "$line" | grep -qE "member=WakeUpScreen|boolean false"; then
        wake_and_restore "GNOME ScreenSaver signal: $line" &
    elif echo "$line" | grep -q "boolean true"; then
        save_window_layout &
    fi
done
