#!/bin/bash

# Copyright 2026 Kinu Garage
#
# @summary: Custom systemd sleep/resume handler for NVIDIA eGPU configurations on ThinkPad P16s.
#   Interfaces with the NVIDIA kernel driver via /proc/driver/nvidia/suspend to save and
#   restore video memory allocations during system power state transitions (suspend, hibernate, resume).
#   Bypasses virtual terminal switching (chvt 63 / chvt <XORG_PID>) present in the default
#   /usr/bin/nvidia-sleep.sh, preventing fatal Xorg EnterVT crashes upon resume over Thunderbolt
#   PCIe links while preserving full video memory state.
# @see: https://github.com/kinu-garage/hut_10sqft/issues/1317
# @see: https://github.com/kinu-garage/hut_10sqft/issues/1505
#
# @param $1 (input): Target power state operation string. Expected values:
#   - "suspend": Instructs NVIDIA kernel driver to save video memory allocations and enter suspend.
#   - "hibernate": Instructs NVIDIA kernel driver to save video memory allocations and enter hibernate.
#   - "resume": Instructs NVIDIA kernel driver to restore video memory allocations upon wake.
#   - "is-suspend-then-hibernate-supported": Checks if systemd version is >= 248.
#
# @return (output):
#   - Side effects: Writes operation string ("suspend", "hibernate", or "resume") directly to
#     the kernel interface at /proc/driver/nvidia/suspend.
#   - Exit status:
#     - 0 on success, or if /proc/driver/nvidia/suspend is not present (NVIDIA driver not loaded).
#     - Non-zero on invalid arguments, failure writing to /proc, or if systemd version is too old.
#   - Standard error: Emits diagnostic error message if unsupported argument or incompatible systemd.

if [ ! -f /proc/driver/nvidia/suspend ]; then
    exit 0
fi

case "$1" in
    is-suspend-then-hibernate-supported)
        systemd_version=$(systemctl --version | head -n1 | cut -d' ' -f2)
        if [ "$systemd_version" -gt 247 ]; then
            exit 0
        fi

        echo "systemd version $systemd_version is too old to support suspend-then-hibernate with NVIDIA." 2>&1
        echo "Please upgrade to systemd 248 or newer." 2>&1
        exit 1
        ;;
    suspend|hibernate)
        echo "$1" > /proc/driver/nvidia/suspend
        exit $?
        ;;
    resume)
        echo "$1" > /proc/driver/nvidia/suspend
        exit $?
        ;;
    *)
        exit 1
        ;;
esac
