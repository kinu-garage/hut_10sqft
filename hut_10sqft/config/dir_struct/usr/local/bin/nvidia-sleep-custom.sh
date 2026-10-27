#!/bin/bash

# Copyright 2026 Kinu Garage
#
# Custom sleep/resume handler for NVIDIA eGPU on ThinkPad P16s.
# Bypasses virtual terminal switching (chvt) which causes Xorg EnterVT crash on resume
# over Thunderbolt PCIe links. Preserves video memory save/restore.
# See https://github.com/kinu-garage/hut_10sqft/issues/1317

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
        exit 0
        ;;
    *)
        exit 1
        ;;
esac
