#!/usr/bin/env python

# Copyright 2024 Kinu Garage Inc.
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

import argparse
import glob
import json
import logging
import os
import shutil
import subprocess
import sys
import pytest

from hut_10sqft.abst_comp_setup import AbstCompSetupFactory
from hut_10sqft.comp_debian import DebianSetup
from hut_10sqft.comp_chrome_os import ChromeOsSetup
from hut_10sqft.comp_mac_os import MacOsSetup
from hut_10sqft.comp_ubuntu import UbuntuOsSetup
from hut_10sqft.host_config import HostConf
from hut_10sqft.suco_installer import CompInitSetupConfig
from hut_10sqft_lib.os_util import OsUtil

ATTR_HOME_DIR = "user_home_dir"
ATTR_PATH_SYMLINKS_DIR = "path_symlinks_dir"

@pytest.fixture
def argparsed():
    parser = argparse.ArgumentParser(description=CompInitSetupConfig.MSG_CONSOLE_TOOL_INTRO)
    _args = parser.parse_args([])

    _os_type, _distro_type = OsUtil.get_os_type()

    _args.os_distro = _distro_type
    _args.os_type = _os_type
    _args.hostname = "suco_test_host"
    _args.user_id = "suco_test_user"
    _args.skip_setup_docker = True
    _args.conf_repo_version = "develop"
    _args.path_local_conf_repo = CompInitSetupConfig.PATH_DEFAULT_PERMANENT_CONF_REPO
    return _args

@pytest.fixture
def cfgbuilder(argparsed) -> AbstCompSetupFactory:
    if argparsed.os_type == OsUtil.TYPE_OS_LINUX:
        if argparsed.os_distro == OsUtil.TYPE_LINUX_DISTRO_DEBIAN:
            return ChromeOsSetup(args_in=argparsed)
        elif argparsed.os_distro == OsUtil.TYPE_LINUX_DISTRO_UBUNTU:
            return UbuntuOsSetup(args_in=argparsed)
    elif argparsed.os_type == OsUtil.TYPE_OS_MACOS:
        # You can add more specific checks for macOS versions if needed,
        # e.g., using platform.mac_ver()
        return MacOsSetup(args_in=argparsed)
    else:
        raise RuntimeError(f"Unsupported OS platform: {argparsed.os_distro}.")

@pytest.fixture
def init_input_params() -> dict:
    return {
        ATTR_HOME_DIR: "~",
        ATTR_PATH_SYMLINKS_DIR: "/"
    }

def test_generate_symlinks(cfgbuilder: AbstCompSetupFactory, init_input_params):
    pairs = cfgbuilder.generate_symlinks(
            rootpath_symlinks=os.path.join(init_input_params[ATTR_HOME_DIR], init_input_params[ATTR_PATH_SYMLINKS_DIR]),
            path_user_home=init_input_params[ATTR_HOME_DIR])
    assert type(pairs) == list

    # TODO Branching logic by if per each test method may not be clean way to run tests on multiple OSes,
    # but I couldnm't figure out a clean way to do this in time as of 2025/10.
    if type(cfgbuilder) == UbuntuOsSetup:
        assert len(pairs) == 12
    elif type(cfgbuilder) == ChromeOsSetup:
        assert len(pairs) == 6
    
@pytest.mark.skip(reason="Disabled due to a known issue https://github.com/kinu-garage/hut_10sqft/issues/1315")
def test_suco_main(cfgbuilder):
    """
    @note: Disabled due to a known issue https://github.com/kinu-garage/hut_10sqft/issues/1315
    @summary: End-to-end test of the main logic of SUCO.
    """
    # Just for test purpose, use an existing host config.
    _host_cfg = HostConf(CompInitSetupConfig.HOSTNAME_P16S, "bashrc_130s-p16s", "emacs_130s-p16s.el", "id_rsa_130s-p16s", "id_rsa_130s-p16s.pub")
    assert cfgbuilder.run(
        _host_cfg,
        conf_repo_remote=CompInitSetupConfig.URL_HUT,
        conf_base_path=CompInitSetupConfig.PATH_FOLDER_CONF) is True

def test_read_conf_os_release(cfgbuilder):
    """
    @description: Test `OsUtil.read_conf` with /etc/os-release or /usr/lib/os-release file.
    """
    if type(cfgbuilder) not in [UbuntuOsSetup, ChromeOsSetup]:
        pytest.skip(f"For the time being this test is only for Linux-based OS, not for '{type(cfgbuilder)}'.")
    os_release_data = OsUtil.read_conf("/etc/os-release", path_alternative="/usr/lib/os-release")
    assert isinstance(os_release_data, dict)
    assert "NAME" in os_release_data
    assert "VERSION_ID" in os_release_data
    assert "ID" in os_release_data
    assert "VERSION_CODENAME" in os_release_data
    assert os_release_data["NAME"]  # Not empty
    assert os_release_data["VERSION_ID"]  # Not empty
    assert os_release_data["ID"]  # Not empty
    assert os_release_data["VERSION_CODENAME"]  # Not empty

def test_gitconfig_uses_separate_host_specific_file():
    repo_root = os.path.dirname(os.path.dirname(__file__))
    path_gitconfig = os.path.join(repo_root, "config", "dot_gitconfig")
    path_gitconfig_local = os.path.join(repo_root, "config", "dot_gitconfig_local")
    path_gitconfig_wsl2 = os.path.join(repo_root, "config", "dot_gitconfig_local_il80d4kk")

    with open(path_gitconfig, "r", encoding="utf-8") as fh:
        gitconfig = fh.read()
    with open(path_gitconfig_local, "r", encoding="utf-8") as fh:
        gitconfig_local = fh.read()
    with open(path_gitconfig_wsl2, "r", encoding="utf-8") as fh:
        gitconfig_wsl2 = fh.read()

    assert "[include]" in gitconfig
    assert "path = ~/.gitconfig_local" in gitconfig
    assert "/mnt/" not in gitconfig
    assert "Empty by default" in gitconfig_local
    assert "directory = /mnt/" in gitconfig_wsl2


def test_setup_configs_removes_old_autostart_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "debian"
    setup._user_home_dir = str(tmp_path)

    path_autostart = tmp_path / ".config" / "autostart"
    path_autostart.parent.mkdir(parents=True, exist_ok=True)
    path_target = tmp_path / "old.desktop"
    path_target.write_text("[Desktop Entry]\n", encoding="utf-8")
    path_autostart.symlink_to(path_target)

    calls = []

    def fake_setup_file(conf, overwrite=False):
        calls.append((conf.path_source, conf.path_dest, overwrite))

    monkeypatch.setattr(setup, "setup_file", fake_setup_file)

    host_config = HostConf("test-host", "bashrc_130s-p16s", "emacs_130s-p16s.el", "id_rsa_130s-p16s", "id_rsa_130s-p16s.pub")
    setup.setup_configs(host_config=host_config, abs_path_confdir=str(tmp_path / "conf"), abs_path_private_confdir=str(tmp_path / "private"))

    assert not path_autostart.exists()
    assert len(calls) > 0


def test_ubuntu_setup_configs_no_recursion(tmp_path, monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    monkeypatch.setattr(UbuntuOsSetup, "ubuntu_desktop_cleanup", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")
    setup = UbuntuOsSetup(args_in=args)
    setup._os_name = "ubuntu"
    setup._user_home_dir = str(tmp_path)

    calls = []

    def fake_setup_file(conf, overwrite=False):
        calls.append((conf.path_source, conf.path_dest, overwrite))

    monkeypatch.setattr(setup, "setup_file", fake_setup_file)

    host_config = HostConf("test-host", "bashrc_130s-p16s", "emacs_130s-p16s.el", "id_rsa_130s-p16s", "id_rsa_130s-p16s.pub")
    setup.setup_configs(host_config=host_config, abs_path_confdir=str(tmp_path / "conf"), abs_path_private_confdir=str(tmp_path / "private"))

    assert len(calls) > 0

@pytest.mark.skip(reason="Disabled due to a known issue about installing rosdep https://github.com/kinu-garage/hut_10sqft/issues/1315")
def test_setup_rosdep():
    """
    @note: Disabled due to a known issue about installing rosdep https://github.com/kinu-garage/hut_10sqft/issues/1315
    """
    #_manual_args = ["--skip_setup_docker"]
    config_dict = {
        "hostname": "test-host",
        "msg_endroll": "msg endroll test",
        "os_distro": "Ubuntu",
        "os_type": "Linux",
        "skip_setup_docker": True,
        }
    parser = argparse.ArgumentParser(description="")
    args = argparse.Namespace(**config_dict)
    ubuntu = UbuntuOsSetup(args_in=args)
    ubuntu.set_ros_apt_source()

    output, error, ret_code = OsUtil.subproc_bash(f"rosdep update")
    assert ret_code == 0


@pytest.mark.skipif(sys.platform == "darwin", reason="Antigravity CLI setup has only been verified for Linux so far on SUCO.")
def test_setup_antigravity_cli_for_linux(monkeypatch, caplog):
    """The shared Linux setup should install Antigravity CLI via pipx and export its PATH."""
    parser = argparse.ArgumentParser(description="")
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")
    monkeypatch.setattr(DebianSetup, "apt_update", lambda self: None)
    setup = DebianSetup(args_in=args)

    called = {}

    def fake_apt_install(deb_pkgs, logger=None):
        called["apt"] = deb_pkgs

    def fake_install_pip_adhoc(pip_pkgs=[], logger=None, allow_break=False):
        called["pip"] = pip_pkgs

    def fake_subproc_bash(cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False):
        called.setdefault("cmds", []).append(cmd)
        if "install.sh" in cmd:
            path_user_home = getattr(setup, "_user_home_dir", os.path.expanduser("~"))
            path_bin = os.path.join(path_user_home, ".local", "bin")
            os.makedirs(path_bin, exist_ok=True)
            with open(os.path.join(path_bin, "agy"), "w", encoding="utf-8") as fh:
                fh.write("#!/bin/sh\n")
        return "", "", 0

    monkeypatch.setattr(OsUtil, "apt_install", fake_apt_install)
    monkeypatch.setattr(OsUtil, "install_pip_adhoc", fake_install_pip_adhoc)
    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc_bash)

    with caplog.at_level(logging.INFO):
        setup.setup_antigravity_cli()

    assert called["apt"] == ["curl", "gh"]
    assert called["pip"] == []
    assert any("install.sh" in cmd for cmd in called["cmds"])
    assert any("gh auth status" in cmd for cmd in called["cmds"])
    path_user_home = getattr(setup, "_user_home_dir", os.path.expanduser("~"))
    path_bashrc = os.path.join(path_user_home, ".bashrc")
    if not os.path.exists(path_bashrc):
        with open(path_bashrc, "w", encoding="utf-8") as fh:
            fh.write("")
    with open(path_bashrc, "r", encoding="utf-8") as fh:
        assert "antigravity" in fh.read().lower()


def test_ubuntu_setup_egpu(tmp_path, monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    monkeypatch.setattr(UbuntuOsSetup, "ubuntu_desktop_cleanup", lambda self: None)
    args = argparse.Namespace(hostname=CompInitSetupConfig.HOSTNAME_P16S, skip_setup_docker=True, user_id="test-user")
    setup = UbuntuOsSetup(args_in=args)

    # Create dummy source files
    xorg_file = tmp_path / "10-nvidia.conf"
    xorg_file.write_text("Section OutputClass\nEndSection\n", encoding="utf-8")
    modprobe_file = tmp_path / "nvidia-runtimepm.conf"
    modprobe_file.write_text("options nvidia\n", encoding="utf-8")
    prime_run_file = tmp_path / "prime-run"
    prime_run_file.write_text("#!/bin/bash\n", encoding="utf-8")

    installed_files = []
    def fake_install(src, dest, mode="644"):
        installed_files.append((src, dest, mode))

    initramfs_called = []
    def fake_initramfs():
        initramfs_called.append(True)

    udev_called = []
    def fake_udev():
        udev_called.append(True)

    monkeypatch.setattr(setup, "_install_system_file", fake_install)
    monkeypatch.setattr(setup, "_update_initramfs", fake_initramfs)
    monkeypatch.setattr(setup, "_reload_udev_rules", fake_udev)

    setup.setup_egpu(
        path_xorg_conf=str(xorg_file),
        path_modprobe_conf=str(modprobe_file),
        path_prime_run=str(prime_run_file))

    assert len(installed_files) == 3
    assert (str(xorg_file), "/etc/X11/xorg.conf.d/10-nvidia.conf", "644") in installed_files
    assert (str(modprobe_file), "/etc/modprobe.d/nvidia-runtimepm.conf", "644") in installed_files
    assert (str(prime_run_file), "/usr/local/bin/prime-run", "755") in installed_files
    assert len(initramfs_called) == 1
    assert len(udev_called) == 1


def test_ubuntu_setup_configs_p16s_egpu(tmp_path, monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    monkeypatch.setattr(UbuntuOsSetup, "ubuntu_desktop_cleanup", lambda self: None)
    args = argparse.Namespace(hostname=CompInitSetupConfig.HOSTNAME_P16S, skip_setup_docker=True, user_id="test-user")
    setup = UbuntuOsSetup(args_in=args)
    setup._os_name = "ubuntu"
    setup._user_home_dir = str(tmp_path)

    monkeypatch.setattr(setup, "setup_file", lambda conf, overwrite=False: None)

    called_egpu = []
    def fake_setup_egpu(**kwargs):
        called_egpu.append(kwargs)

    called_wake = []
    def fake_setup_wake(**kwargs):
        called_wake.append(kwargs)

    monkeypatch.setattr(setup, "setup_egpu", fake_setup_egpu)
    monkeypatch.setattr(setup, "setup_wake_monitors_service", fake_setup_wake)

    # Test non-p16s host
    host_other = HostConf("other-host", "bashrc_130s-p16s", "emacs_130s-p16s.el", "id_rsa_130s-p16s", "id_rsa_130s-p16s.pub")
    setup.setup_configs(host_config=host_other, abs_path_confdir=str(tmp_path / "conf"), abs_path_private_confdir=str(tmp_path / "private"))
    assert len(called_egpu) == 0
    assert len(called_wake) == 0

    # Test p16s host
    host_p16s = HostConf(CompInitSetupConfig.HOSTNAME_P16S, "bashrc_130s-p16s", "emacs_130s-p16s.el", "id_rsa_130s-p16s", "id_rsa_130s-p16s.pub")
    setup.setup_configs(host_config=host_p16s, abs_path_confdir=str(tmp_path / "conf"), abs_path_private_confdir=str(tmp_path / "private"))
    assert len(called_egpu) == 1
    assert "path_xorg_conf" in called_egpu[0]
    assert "path_modprobe_conf" in called_egpu[0]
    assert "path_prime_run" in called_egpu[0]
    assert len(called_wake) == 1
    assert "path_service_src" in called_wake[0]


def test_ubuntu_setup_wake_monitors_service(tmp_path, monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    monkeypatch.setattr(UbuntuOsSetup, "ubuntu_desktop_cleanup", lambda self: None)
    args = argparse.Namespace(hostname=CompInitSetupConfig.HOSTNAME_P16S, skip_setup_docker=True, user_id="test-user")
    setup = UbuntuOsSetup(args_in=args)
    setup._user_home_dir = str(tmp_path)

    service_src = tmp_path / "wake-all-monitors.service"
    service_src.write_text("[Unit]\nDescription=Test\n", encoding="utf-8")

    dispatched = []
    monkeypatch.setattr(setup, "setup_file", lambda conf, overwrite=False: dispatched.append((conf, overwrite)))

    cmds = []
    def fake_subproc_bash(cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False):
        cmds.append((cmd, does_sudo))
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc_bash)

    setup.setup_wake_monitors_service(path_service_src=str(service_src))

    assert len(dispatched) == 1
    conf, overwrite = dispatched[0]
    assert conf.path_source == str(service_src)
    assert conf.path_dest == str(tmp_path / ".config" / "systemd" / "user" / "wake-all-monitors.service")
    assert conf.is_symlink is True
    assert overwrite is True
    assert len(cmds) == 1
    assert "systemctl --user enable --now wake-all-monitors.service" in cmds[0][0]
    assert cmds[0][1] is False


def test_ubuntu_setup_dropbox_swap_watchdog(tmp_path, monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    monkeypatch.setattr(UbuntuOsSetup, "ubuntu_desktop_cleanup", lambda self: None)
    args = argparse.Namespace(hostname=CompInitSetupConfig.HOSTNAME_P16S, skip_setup_docker=True, user_id="test-user")
    setup = UbuntuOsSetup(args_in=args)
    setup._user_home_dir = str(tmp_path)

    service_src = tmp_path / "dropbox-swap-watchdog.service"
    service_src.write_text("[Unit]\nDescription=Test Service\n", encoding="utf-8")
    timer_src = tmp_path / "dropbox-swap-watchdog.timer"
    timer_src.write_text("[Unit]\nDescription=Test Timer\n", encoding="utf-8")

    dispatched = []
    monkeypatch.setattr(setup, "setup_file", lambda conf, overwrite=False: dispatched.append((conf, overwrite)))

    cmds = []
    def fake_subproc_bash(cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False):
        cmds.append((cmd, does_sudo))
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc_bash)

    setup.setup_dropbox_swap_watchdog(path_service_src=str(service_src), path_timer_src=str(timer_src))

    assert len(dispatched) == 2
    conf_svc, overwrite_svc = dispatched[0]
    assert conf_svc.path_source == str(service_src)
    assert conf_svc.path_dest == str(tmp_path / ".config" / "systemd" / "user" / "dropbox-swap-watchdog.service")
    assert conf_svc.is_symlink is True
    assert overwrite_svc is True

    conf_tmr, overwrite_tmr = dispatched[1]
    assert conf_tmr.path_source == str(timer_src)
    assert conf_tmr.path_dest == str(tmp_path / ".config" / "systemd" / "user" / "dropbox-swap-watchdog.timer")
    assert conf_tmr.is_symlink is True
    assert overwrite_tmr is True

    assert len(cmds) == 1
    assert "systemctl --user enable --now dropbox-swap-watchdog.timer" in cmds[0][0]
    assert cmds[0][1] is False


def test_dropbox_swap_watchdog_script(tmp_path):
    test_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.normpath(os.path.join(test_dir, "..", "exec", "dropbox-swap-watchdog.sh"))

    fake_pid = "999999"
    proc_dir = tmp_path / "proc" / fake_pid
    proc_dir.mkdir(parents=True)
    status_file = proc_dir / "status"

    log_file = tmp_path / "dropbox_cli.log"
    fake_cli = tmp_path / "fake_dropbox"
    state_file = tmp_path / "dropbox_status.txt"

    fake_cli.write_text(
        f"#!/usr/bin/env bash\n"
        f"echo \"$1\" >> \"{log_file}\"\n"
        f"if [[ \"$1\" == \"status\" ]]; then\n"
        f"  cat \"{state_file}\"\n"
        f"fi\n",
        encoding="utf-8",
    )
    fake_cli.chmod(0o755)

    env = os.environ.copy()
    env["DROPBOX_PID_OVERRIDE"] = fake_pid
    env["DROPBOX_PROC_ROOT"] = str(tmp_path / "proc")
    env["DROPBOX_CLI"] = str(fake_cli)

    # 1. Below 1 GB limit (500 MB) -> no CLI calls
    status_file.write_text("VmRSS:\t 1200000 kB\nVmSwap:\t  512000 kB\n", encoding="utf-8")
    state_file.write_text("Up to date\n", encoding="utf-8")
    res = subprocess.run([script_path], env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert "within limit (1048576 kB)" in res.stdout
    assert not log_file.exists()

    # 2. Above 1 GB limit (1.2 GB) but currently syncing -> checks status, defers restart
    status_file.write_text("VmRSS:\t 1200000 kB\nVmSwap:\t 1258291 kB\n", encoding="utf-8")
    state_file.write_text("Syncing 42 files...\n", encoding="utf-8")
    res = subprocess.run([script_path], env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert "Deferring restart" in res.stdout
    assert log_file.read_text(encoding="utf-8").splitlines() == ["status"]

    # 3. Above 1 GB limit (1.2 GB) and "Up to date" -> checks status, stops, and starts
    log_file.unlink()
    state_file.write_text("Up to date\n", encoding="utf-8")
    res = subprocess.run([script_path], env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert "Dropbox restarted successfully" in res.stdout
    assert log_file.read_text(encoding="utf-8").splitlines() == ["status", "stop", "start"]




def test_emacs_lisp_syntax():
    """Verify all Emacs Lisp configuration files have valid syntax and balanced parentheses."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    emacs_dir = os.path.normpath(os.path.join(test_dir, "..", "config", "emacs"))
    el_files = glob.glob(os.path.join(emacs_dir, "**/*.el"), recursive=True)
    assert len(el_files) > 0, f"No .el files found in {emacs_dir}"

    for filepath in el_files:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        in_string = False
        escape = False
        in_comment = False
        stack = []
        for line_idx, line in enumerate(content.splitlines(), start=1):
            in_comment = False
            for col_idx, ch in enumerate(line, start=1):
                if in_comment:
                    continue
                if escape:
                    escape = False
                    continue
                if ch == "\\":
                    escape = True
                    continue
                if ch == '"' and not in_comment:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == ";":
                    in_comment = True
                    continue
                if ch in "([{":
                    stack.append((ch, line_idx, col_idx))
                elif ch in ")]}":
                    matching = {"(": ")", "[": "]", "{": "}"}
                    assert stack, f"Unmatched closing '{ch}' at {filepath}:{line_idx}:{col_idx}"
                    open_ch, o_line, o_col = stack.pop()
                    assert matching[open_ch] == ch, (
                        f"Mismatched bracket '{open_ch}' (line {o_line}:{o_col}) "
                        f"closed by '{ch}' at {filepath}:{line_idx}:{col_idx}"
                    )
        assert not stack, f"Unclosed '{stack[-1][0]}' from line {stack[-1][1]}:{stack[-1][2]} in {filepath}"

    if shutil.which("emacs"):
        emacs_el = os.path.join(emacs_dir, "emacs.el")
        res = subprocess.run(
            ["emacs", "--batch", "--eval", f'(load-file "{emacs_el}")'],
            capture_output=True,
            text=True
        )
        assert res.returncode == 0, f"Emacs batch load failed: {res.stderr}"


def test_swap_caps_ctrl(monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")
    setup = DebianSetup(args_in=args)

    verified_pkgs = []
    monkeypatch.setattr(setup, "verify_deb_installed", lambda pkg: verified_pkgs.append(pkg))

    executed_cmds = []
    def fake_subproc_bash(cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False):
        executed_cmds.append((cmd, does_sudo))
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc_bash)

    setup.swap_caps_ctrl()
    assert verified_pkgs == [DebianSetup._DEB_CAPS_CTRL_UTIL]
    assert len(executed_cmds) == 1
    assert "gsettings set org.gnome.desktop.input-sources xkb-options \"['ctrl:swapcaps']\"" in executed_cmds[0][0]
    assert executed_cmds[0][1] is False

    # Verify failure raises RuntimeError
    monkeypatch.setattr(
        OsUtil,
        "subproc_bash",
        lambda cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False: ("", "dconf error", 1)
    )
    with pytest.raises(RuntimeError, match="Failed to configure Caps/Ctrl swap"):
        setup.swap_caps_ctrl()



def test_setup_agent_skills(tmp_path, monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._user_home_dir = str(tmp_path / "home")

    conf_dir = tmp_path / "conf"
    skills_dir = conf_dir / "skills" / "test-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("---\nname: test-skill\n---\n", encoding="utf-8")

    dispatched = []
    monkeypatch.setattr(setup, "setup_file", lambda conf, overwrite=False: dispatched.append((conf, overwrite)))

    setup.setup_agent_skills(path_local_perm_conf=str(conf_dir))

    # Should dispatch symlink to both ~/.gemini/antigravity/skills and ~/.claude/skills
    assert len(dispatched) == 2
    paths_dest = [conf.path_dest for conf, overwrite in dispatched]
    assert str(tmp_path / "home" / ".gemini" / "antigravity" / "skills" / "test-skill") in paths_dest
    assert str(tmp_path / "home" / ".claude" / "skills" / "test-skill") in paths_dest
    for conf, overwrite in dispatched:
        assert conf.is_symlink is True
        assert overwrite is True


def test_setup_agent_remote_control(tmp_path, monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._user_home_dir = str(tmp_path / "home")

    executed_cmds = []
    def fake_subproc(cmd, does_sudo=False, logger=None):
        executed_cmds.append(cmd)
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)
    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/local/bin/agy" if cmd == "agy" else None)

    setup.setup_agent_remote_control()

    # Claude Code settings.json
    path_claude_settings = tmp_path / "home" / ".claude" / "settings.json"
    assert path_claude_settings.exists()
    data = json.loads(path_claude_settings.read_text(encoding="utf-8"))
    assert data.get("remoteControlAtStartup") is True

    # Antigravity remote-control command
    assert any("remote-control start" in cmd for cmd in executed_cmds)
