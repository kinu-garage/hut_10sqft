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
import socket
import subprocess
import sys
import pytest

from hut_10sqft.abst_comp_setup import AbstCompSetupFactory
from hut_10sqft.comp_debian import DebianSetup
from hut_10sqft.comp_chrome_os import ChromeOsSetup
from hut_10sqft.comp_mac_os import MacOsSetup
from hut_10sqft.comp_ubuntu import UbuntuOsSetup
from hut_10sqft.host_config import HostConf
from hut_10sqft.suco_installer import CompInitSetupConfig, SucoInstaller
from hut_10sqft.suco_main import CompInitSetup
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
def test_setup_antigravity_cli_for_linux(tmp_path, monkeypatch, caplog):
    """The shared Linux setup should install Antigravity CLI via curl installer and export its PATH."""
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    monkeypatch.setattr(DebianSetup, "apt_update", lambda self: None)

    called = {}

    def fake_apt_install(deb_pkgs, logger=None):
        called["apt"] = deb_pkgs

    def fake_install_pip_adhoc(pip_pkgs=[], logger=None, allow_break=False):
        called["pip"] = pip_pkgs

    monkeypatch.setattr(OsUtil, "apt_install", fake_apt_install)
    monkeypatch.setattr(OsUtil, "install_pip_adhoc", fake_install_pip_adhoc)

    parser = argparse.ArgumentParser(description="")
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")
    setup = DebianSetup(args_in=args)
    home_dir = tmp_path / "home"
    setup._user_home_dir = str(home_dir)
    os.makedirs(home_dir, exist_ok=True)

    def fake_subproc_bash(cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False):
        called.setdefault("cmds", []).append(cmd)
        if "install.sh" in cmd:
            path_user_home = getattr(setup, "_user_home_dir", os.path.expanduser("~"))
            path_bin = os.path.join(path_user_home, ".local", "bin")
            os.makedirs(path_bin, exist_ok=True)
            with open(os.path.join(path_bin, "agy"), "w", encoding="utf-8") as fh:
                fh.write("#!/bin/sh\necho 'mock agy'\n" + "x" * 2000)
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
    path_bashrc = os.path.join(str(home_dir), ".bashrc")
    with open(path_bashrc, "r", encoding="utf-8") as fh:
        assert "antigravity" in fh.read().lower()
    path_agy = os.path.join(str(home_dir), ".local", "bin", "agy")
    assert os.path.exists(path_agy)

    # Verify cleaning up corrupted stub (< 1000 bytes) triggers reinstallation
    with open(path_agy, "w", encoding="utf-8") as fh:
        fh.write("#!/bin/sh\n")  # 10 byte stub
    called["cmds"].clear()
    setup.setup_antigravity_cli()
    assert any("install.sh" in cmd for cmd in called["cmds"])

    # Verify existing ~/.gemini/bin/agy gets symlinked
    os.remove(path_agy)
    gemini_bin = home_dir / ".gemini" / "bin"
    gemini_bin.mkdir(parents=True, exist_ok=True)
    gemini_agy = gemini_bin / "agy"
    gemini_agy.write_text("#!/bin/sh\n" + "y" * 2000, encoding="utf-8")
    gemini_agy.chmod(0o755)
    called["cmds"].clear()
    setup.setup_antigravity_cli()
    assert os.path.islink(path_agy)
    assert os.path.realpath(path_agy) == str(gemini_agy)
    assert not any("install.sh" in cmd for cmd in called["cmds"])

    # Verify non-executable agy gets repaired with execute permissions without re-running installer
    os.remove(path_agy)
    with open(path_agy, "w", encoding="utf-8") as fh:
        fh.write("#!/bin/sh\n" + "z" * 2000)
    os.chmod(path_agy, 0o644)
    assert not os.access(path_agy, os.X_OK)
    called["cmds"].clear()
    setup.setup_antigravity_cli()
    assert os.access(path_agy, os.X_OK)
    assert not any("install.sh" in cmd for cmd in called["cmds"])

    # Verify 0600 mode only becomes executable for owner (0700), not group or others
    os.remove(path_agy)
    with open(path_agy, "w", encoding="utf-8") as fh:
        fh.write("#!/bin/sh\n" + "w" * 2000)
    os.chmod(path_agy, 0o600)
    setup.setup_antigravity_cli()
    assert os.stat(path_agy).st_mode & 0o777 == 0o700

    # Verify _make_executable_for_readers preserves mode and raises PermissionError when owner read is missing
    os.chmod(path_agy, 0o200)
    with pytest.raises(PermissionError):
        DebianSetup._make_executable_for_readers(path_agy)
    assert os.stat(path_agy).st_mode & 0o777 == 0o200


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

    daemon_reload_called = []
    def fake_daemon_reload():
        daemon_reload_called.append(True)

    patch_sleep_called = []
    def fake_patch(target="/usr/bin/nvidia-sleep.sh"):
        patch_sleep_called.append(target)

    monkeypatch.setattr(setup, "_install_system_file", fake_install)
    monkeypatch.setattr(setup, "_update_initramfs", fake_initramfs)
    monkeypatch.setattr(setup, "_reload_udev_rules", fake_udev)
    monkeypatch.setattr(setup, "_systemctl_daemon_reload", fake_daemon_reload)
    monkeypatch.setattr(setup, "_patch_nvidia_sleep_script", fake_patch)

    sleep_custom_file = tmp_path / "nvidia-sleep-custom.sh"
    sleep_custom_file.write_text("#!/bin/bash\n", encoding="utf-8")
    suspend_override_file = tmp_path / "suspend_override.conf"
    suspend_override_file.write_text("[Service]\n", encoding="utf-8")
    resume_override_file = tmp_path / "resume_override.conf"
    resume_override_file.write_text("[Service]\n", encoding="utf-8")
    hibernate_override_file = tmp_path / "hibernate_override.conf"
    hibernate_override_file.write_text("[Service]\n", encoding="utf-8")
    apt_hook_file = tmp_path / "99-nvidia-sleep-no-chvt"
    apt_hook_file.write_text("DPkg::Post-Invoke {};\n", encoding="utf-8")

    setup.setup_egpu(
        path_xorg_conf=str(xorg_file),
        path_modprobe_conf=str(modprobe_file),
        path_prime_run=str(prime_run_file),
        path_nvidia_sleep_custom=str(sleep_custom_file),
        path_suspend_override=str(suspend_override_file),
        path_resume_override=str(resume_override_file),
        path_hibernate_override=str(hibernate_override_file),
        path_apt_hook=str(apt_hook_file))

    assert len(installed_files) == 8
    assert (str(xorg_file), "/etc/X11/xorg.conf.d/10-nvidia.conf", "644") in installed_files
    assert (str(modprobe_file), "/etc/modprobe.d/nvidia-runtimepm.conf", "644") in installed_files
    assert (str(prime_run_file), "/usr/local/bin/prime-run", "755") in installed_files
    assert (str(sleep_custom_file), "/usr/local/bin/nvidia-sleep-custom.sh", "755") in installed_files
    assert (str(suspend_override_file), "/etc/systemd/system/nvidia-suspend.service.d/override.conf", "644") in installed_files
    assert (str(resume_override_file), "/etc/systemd/system/nvidia-resume.service.d/override.conf", "644") in installed_files
    assert (str(hibernate_override_file), "/etc/systemd/system/nvidia-hibernate.service.d/override.conf", "644") in installed_files
    assert (str(apt_hook_file), "/etc/apt/apt.conf.d/99-nvidia-sleep-no-chvt", "644") in installed_files
    assert len(initramfs_called) == 1
    assert len(udev_called) == 1
    assert len(daemon_reload_called) == 1
    assert len(patch_sleep_called) == 1

    # Verify that missing sleep script source skips sleep script and overrides
    installed_files.clear()
    setup._list_runtime_issues.clear()
    patch_sleep_called.clear()
    setup.setup_egpu(
        path_xorg_conf=str(xorg_file),
        path_modprobe_conf=str(modprobe_file),
        path_prime_run=str(prime_run_file),
        path_nvidia_sleep_custom=str(tmp_path / "nonexistent-sleep-custom.sh"),
        path_suspend_override=str(suspend_override_file),
        path_resume_override=str(resume_override_file),
        path_hibernate_override=str(hibernate_override_file),
        path_apt_hook=str(apt_hook_file))

    # Overrides and sleep custom script should NOT be installed
    assert (str(sleep_custom_file), "/usr/local/bin/nvidia-sleep-custom.sh", "755") not in installed_files
    assert (str(suspend_override_file), "/etc/systemd/system/nvidia-suspend.service.d/override.conf", "644") not in installed_files
    assert (str(resume_override_file), "/etc/systemd/system/nvidia-resume.service.d/override.conf", "644") not in installed_files
    assert (str(hibernate_override_file), "/etc/systemd/system/nvidia-hibernate.service.d/override.conf", "644") not in installed_files
    # Base configs and apt hook are still installed
    assert (str(xorg_file), "/etc/X11/xorg.conf.d/10-nvidia.conf", "644") in installed_files
    assert (str(apt_hook_file), "/etc/apt/apt.conf.d/99-nvidia-sleep-no-chvt", "644") in installed_files
    assert len(patch_sleep_called) == 1
    # Runtime issue recorded
    assert any("Sleep-file set is incomplete" in str(issue) for issue in setup._list_runtime_issues)


def test_patch_nvidia_sleep_script(tmp_path, monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    monkeypatch.setattr(UbuntuOsSetup, "ubuntu_desktop_cleanup", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")
    setup = UbuntuOsSetup(args_in=args)

    executed_cmds = []
    def fake_subproc_bash(cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False):
        executed_cmds.append((cmd, does_sudo))
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc_bash)

    # 1. Target script does not exist -> returns cleanly without running command
    setup._patch_nvidia_sleep_script(str(tmp_path / "nonexistent.sh"))
    assert len(executed_cmds) == 0

    # 2. Target script exists -> executes patch command with sudo
    target_sh = tmp_path / "nvidia-sleep.sh"
    target_sh.write_text("#!/bin/sh\nchvt 63\n", encoding="utf-8")
    setup._patch_nvidia_sleep_script(str(target_sh))
    assert len(executed_cmds) == 1
    cmd, does_sudo = executed_cmds[0]
    assert does_sudo is True
    assert "chvt" in cmd
    assert str(target_sh) in cmd

    # 3. Nonzero return code raises RuntimeError
    monkeypatch.setattr(
        OsUtil,
        "subproc_bash",
        lambda cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False: ("", "sed error", 1)
    )
    with pytest.raises(RuntimeError, match="Failed to patch"):
        setup._patch_nvidia_sleep_script(str(target_sh))


def test_systemctl_daemon_reload(monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")
    setup = DebianSetup(args_in=args)

    executed_cmds = []
    def fake_subproc_bash(cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False):
        executed_cmds.append((cmd, does_sudo))
        return "reloaded", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc_bash)

    # 1. Successful reload executes sudo systemctl daemon-reload
    setup._systemctl_daemon_reload()
    assert len(executed_cmds) == 1
    assert executed_cmds[0] == ("systemctl daemon-reload", True)

    # 2. Failure with nonzero exit code raises RuntimeError
    monkeypatch.setattr(
        OsUtil,
        "subproc_bash",
        lambda cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False: ("", "systemd reload failed", 1)
    )
    with pytest.raises(RuntimeError, match="Failed to reload systemd daemon"):
        setup._systemctl_daemon_reload()


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
    assert "path_nvidia_sleep_custom" in called_egpu[0]
    assert "path_suspend_override" in called_egpu[0]
    assert "path_resume_override" in called_egpu[0]
    assert "path_hibernate_override" in called_egpu[0]
    assert "path_apt_hook" in called_egpu[0]
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


def test_wake_all_monitors_window_layout(tmp_path):
    """Verify save_window_layout snapshots valid windows and restore_window_layout restores them."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.normpath(os.path.join(test_dir, "..", "exec", "wake-all-monitors_p16s.sh"))

    layout_file = tmp_path / "window-layout.json"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    fake_xwininfo = bin_dir / "xwininfo"
    fake_xwininfo.write_text(
        "#!/bin/sh\n"
        "cat << 'EOF'\n"
        "xwininfo: Window id: 0x64f (the root window) (has no name)\n"
        "     0x2e0001c \"Chrome\": (\"google-chrome\" \"Google-chrome\")  3063x1727+777+1702  +777+1702\n"
        "     0x800004 \"Emacs\": (\"mutter-x11-frames\" \"mutter-x11-frames\")  1250x1478+4576+2224  +4576+2224\n"
        "     0x4f00012 \"Search \"example\" - Google Chrome\": (\"google-chrome\" \"Google-chrome\")  1920x1080+100+200  +100+200\n"
        "     0x6a00010 \"Desktop Icons\": (\"gjs\" \"Gjs\")  3440x1440+6000+2400  +6000+2400\n"
        "     0x2400004 (has no name): ()  10x10+10+10  +10+10\n"
        "     0x3500001 \"Huge Canvas\": (\"canvas\" \"Canvas\")  1920x9500+0+0  +0+0\n"
        "EOF\n",
        encoding="utf-8",
    )
    fake_xwininfo.chmod(0o755)

    xdotool_log = tmp_path / "xdotool.log"
    fake_xdotool = bin_dir / "xdotool"
    fake_xdotool.write_text(
        f"#!/bin/sh\necho \"$*\" >> '{xdotool_log}'\n",
        encoding="utf-8",
    )
    fake_xdotool.chmod(0o755)

    runner = tmp_path / "run_test.sh"
    runner.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"export PATH=\"{bin_dir}:$PATH\"\n"
        f"export WINDOW_LAYOUT_FILE=\"{layout_file}\"\n"
        f"export DISPLAY=\":99\"\n"
        f"detect_display() {{ echo \":99\"; }}\n"
        f"are_monitors_configured() {{ return 0; }}\n"
        f"eval \"$(sed -n '/^save_window_layout()/,/^}}/p' '{script_path}')\"\n"
        f"eval \"$(sed -n '/^restore_window_layout()/,/^}}/p' '{script_path}')\"\n"
        f"save_window_layout\n"
        f"restore_window_layout\n",
        encoding="utf-8",
    )
    runner.chmod(0o755)

    res = subprocess.run([str(runner)], capture_output=True, text=True)
    assert res.returncode == 0
    assert layout_file.exists()

    with open(layout_file, "r", encoding="utf-8") as f:
        saved = json.load(f)
    assert len(saved) == 3
    assert saved[0]["id"] == "0x2e0001c"
    assert saved[0]["w"] == 3063 and saved[0]["h"] == 1727
    assert saved[0]["x"] == 777 and saved[0]["y"] == 1702
    assert saved[1]["id"] == "0x800004"
    assert saved[1]["w"] == 1250 and saved[1]["h"] == 1478
    assert saved[1]["x"] == 4576 and saved[1]["y"] == 2224
    assert saved[2]["id"] == "0x4f00012"
    assert saved[2]["w"] == 1920 and saved[2]["h"] == 1080
    assert saved[2]["x"] == 100 and saved[2]["y"] == 200

    assert xdotool_log.exists()
    xdotool_cmds = xdotool_log.read_text(encoding="utf-8").splitlines()
    assert any("windowmove 0x2e0001c 777 1702" in cmd for cmd in xdotool_cmds)
    assert any("windowsize 0x2e0001c 3063 1727" in cmd for cmd in xdotool_cmds)
    assert any("windowmove 0x800004 4576 2224" in cmd for cmd in xdotool_cmds)
    assert any("windowsize 0x800004 1250 1478" in cmd for cmd in xdotool_cmds)
    assert any("windowmove 0x4f00012 100 200" in cmd for cmd in xdotool_cmds)
    assert any("windowsize 0x4f00012 1920 1080" in cmd for cmd in xdotool_cmds)

    # Verify per-user XDG_RUNTIME_DIR default resolution when WINDOW_LAYOUT_FILE is unset
    xdg_runtime = tmp_path / "run" / "user" / str(os.getuid())
    xdg_runtime.mkdir(parents=True, mode=0o700)
    xdg_runtime.chmod(0o700)
    runner_xdg = tmp_path / "run_test_xdg.sh"
    runner_xdg.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"unset WINDOW_LAYOUT_FILE\n"
        f"export XDG_RUNTIME_DIR=\"{xdg_runtime}\"\n"
        f"export PATH=\"{bin_dir}:$PATH\"\n"
        f"export DISPLAY=\":99\"\n"
        f"detect_display() {{ echo \":99\"; }}\n"
        f"are_monitors_configured() {{ return 0; }}\n"
        f"eval \"$(sed -n '/^verify_secure_runtime_dir()/,/^DEBOUNCE_SEC=15/p' '{script_path}')\"\n"
        f"eval \"$(sed -n '/^save_window_layout()/,/^}}/p' '{script_path}')\"\n"
        f"save_window_layout\n"
        f"echo \"RESOLVED_FILE=$WINDOW_LAYOUT_FILE\"\n",
        encoding="utf-8",
    )
    runner_xdg.chmod(0o755)
    res_xdg = subprocess.run([str(runner_xdg)], capture_output=True, text=True)
    assert res_xdg.returncode == 0
    assert f"RESOLVED_FILE={xdg_runtime}/window-layout.json" in res_xdg.stdout
    assert (xdg_runtime / "window-layout.json").exists()
    st_xdg = os.stat(xdg_runtime / "window-layout.json")
    assert oct(st_xdg.st_mode & 0o777) == "0o600"

    # Verify insecure XDG_RUNTIME_DIR (loose permissions) is rejected and falls back
    insecure_xdg = tmp_path / "insecure_xdg"
    insecure_xdg.mkdir(mode=0o777)
    insecure_xdg.chmod(0o777)
    fallback_parent = tmp_path / "fallback_parent"
    fallback_parent.mkdir()
    runner_insecure_xdg = tmp_path / "run_test_insecure_xdg.sh"
    runner_insecure_xdg.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"unset WINDOW_LAYOUT_FILE\n"
        f"export XDG_RUNTIME_DIR=\"{insecure_xdg}\"\n"
        f"export TMPDIR=\"{fallback_parent}\"\n"
        f"eval \"$(sed -n '/^verify_secure_runtime_dir()/,/^DEBOUNCE_SEC=15/p' '{script_path}')\"\n"
        f"echo \"RESOLVED_DIR=$_DEFAULT_RUNTIME_DIR\"\n",
        encoding="utf-8",
    )
    runner_insecure_xdg.chmod(0o755)
    res_insecure_xdg = subprocess.run([str(runner_insecure_xdg)], capture_output=True, text=True)
    assert res_insecure_xdg.returncode == 0
    assert str(insecure_xdg) not in res_insecure_xdg.stdout
    assert f"RESOLVED_DIR={fallback_parent}/wake-all-monitors-{os.getuid()}" in res_insecure_xdg.stdout

    # Verify fallback directory with 0700 permissions when XDG_RUNTIME_DIR is unset
    custom_tmp = tmp_path / "custom_tmp"
    custom_tmp.mkdir()
    runner_fallback = tmp_path / "run_test_fallback.sh"
    runner_fallback.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"unset WINDOW_LAYOUT_FILE\n"
        f"unset XDG_RUNTIME_DIR\n"
        f"export TMPDIR=\"{custom_tmp}\"\n"
        f"export PATH=\"{bin_dir}:$PATH\"\n"
        f"export DISPLAY=\":99\"\n"
        f"detect_display() {{ echo \":99\"; }}\n"
        f"are_monitors_configured() {{ return 0; }}\n"
        f"eval \"$(sed -n '/^verify_secure_runtime_dir()/,/^DEBOUNCE_SEC=15/p' '{script_path}')\"\n"
        f"eval \"$(sed -n '/^save_window_layout()/,/^}}/p' '{script_path}')\"\n"
        f"save_window_layout\n"
        f"echo \"RESOLVED_FILE=$WINDOW_LAYOUT_FILE\"\n",
        encoding="utf-8",
    )
    runner_fallback.chmod(0o755)
    res_fallback = subprocess.run([str(runner_fallback)], capture_output=True, text=True)
    assert res_fallback.returncode == 0
    expected_fallback_dir = custom_tmp / f"wake-all-monitors-{os.getuid()}"
    assert expected_fallback_dir.exists()
    st_dir = os.stat(expected_fallback_dir)
    assert oct(st_dir.st_mode & 0o777) == "0o700"
    assert (expected_fallback_dir / "window-layout.json").exists()

    # Verify reusing existing fallback directory succeeds when valid and private
    res_fallback_reuse = subprocess.run([str(runner_fallback)], capture_output=True, text=True)
    assert res_fallback_reuse.returncode == 0

    # Verify rejection of insecure symlink fallback runtime directory
    symlink_tmp = tmp_path / "symlink_tmp"
    symlink_tmp.mkdir()
    target_dir = tmp_path / "other_target"
    target_dir.mkdir()
    symlink_fallback = symlink_tmp / f"wake-all-monitors-{os.getuid()}"
    symlink_fallback.symlink_to(target_dir)

    runner_symlink = tmp_path / "run_test_symlink.sh"
    runner_symlink.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"unset WINDOW_LAYOUT_FILE\n"
        f"unset XDG_RUNTIME_DIR\n"
        f"export TMPDIR=\"{symlink_tmp}\"\n"
        f"eval \"$(sed -n '/^verify_secure_runtime_dir()/,/^DEBOUNCE_SEC=15/p' '{script_path}')\"\n",
        encoding="utf-8",
    )
    runner_symlink.chmod(0o755)
    res_symlink = subprocess.run([str(runner_symlink)], capture_output=True, text=True)
    assert res_symlink.returncode == 1
    assert "Insecure runtime directory" in res_symlink.stderr

    # Verify rejection of fallback directory with loose (non-private) permissions
    bad_perm_tmp = tmp_path / "bad_perm_tmp"
    bad_perm_tmp.mkdir()
    bad_dir = bad_perm_tmp / f"wake-all-monitors-{os.getuid()}"
    bad_dir.mkdir(mode=0o777)
    bad_dir.chmod(0o777)

    runner_bad_perm = tmp_path / "run_test_bad_perm.sh"
    runner_bad_perm.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"unset WINDOW_LAYOUT_FILE\n"
        f"unset XDG_RUNTIME_DIR\n"
        f"export TMPDIR=\"{bad_perm_tmp}\"\n"
        f"eval \"$(sed -n '/^verify_secure_runtime_dir()/,/^DEBOUNCE_SEC=15/p' '{script_path}')\"\n",
        encoding="utf-8",
    )
    runner_bad_perm.chmod(0o755)
    res_bad_perm = subprocess.run([str(runner_bad_perm)], capture_output=True, text=True)
    assert res_bad_perm.returncode == 1
    assert "Insecure runtime directory" in res_bad_perm.stderr

    # Verify save_window_layout exports DISPLAY before checking are_monitors_configured
    runner_disp = tmp_path / "run_test_disp.sh"
    runner_disp.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"unset DISPLAY\n"
        f"detect_display() {{ echo \":42\"; }}\n"
        f"are_monitors_configured() {{\n"
        f"    if [ \"$DISPLAY\" != \":42\" ]; then exit 2; fi\n"
        f"    return 1\n"
        f"}}\n"
        f"eval \"$(sed -n '/^save_window_layout()/,/^}}/p' '{script_path}')\"\n"
        f"save_window_layout\n",
        encoding="utf-8",
    )
    runner_disp.chmod(0o755)
    res_disp = subprocess.run([str(runner_disp)], capture_output=True, text=True)
    assert res_disp.returncode == 0

    # Verify save_window_layout propagates failure when xwininfo fails
    fail_bin = tmp_path / "fail_bin"
    fail_bin.mkdir()
    (fail_bin / "xwininfo").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    (fail_bin / "xwininfo").chmod(0o755)

    runner_fail = tmp_path / "run_test_fail.sh"
    runner_fail.write_text(
        f"#!/usr/bin/env bash\n"
        f"export PATH=\"{fail_bin}:$PATH\"\n"
        f"export WINDOW_LAYOUT_FILE=\"{tmp_path / 'fail.json'}\"\n"
        f"export DISPLAY=\":99\"\n"
        f"detect_display() {{ echo \":99\"; }}\n"
        f"are_monitors_configured() {{ return 0; }}\n"
        f"eval \"$(sed -n '/^save_window_layout()/,/^}}/p' '{script_path}')\"\n"
        f"save_window_layout\n",
        encoding="utf-8",
    )
    runner_fail.chmod(0o755)
    res_fail = subprocess.run([str(runner_fail)], capture_output=True, text=True)
    assert res_fail.returncode == 1
    assert "Error querying xwininfo" in res_fail.stderr

    # Verify wake_and_restore serializes execution and sets lock timestamp on finish
    lock_file = tmp_path / "test_wake.lock"
    runner_wake = tmp_path / "run_test_wake.sh"
    runner_wake.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"export LOCK_FILE=\"{lock_file}\"\n"
        f"export WINDOW_LAYOUT_FILE=\"{layout_file}\"\n"
        f"export DISPLAY=\":99\"\n"
        f"detect_display() {{ echo \":99\"; }}\n"
        f"xset() {{ :; }}\n"
        f"are_monitors_configured() {{ return 0; }}\n"
        f"restore_window_layout() {{ :; }}\n"
        f"eval \"$(sed -n '/^wake_and_restore()/,/^}}/p' '{script_path}')\"\n"
        f"wake_and_restore \"test_wake\"\n",
        encoding="utf-8",
    )
    runner_wake.chmod(0o755)
    res_wake = subprocess.run([str(runner_wake)], capture_output=True, text=True)
    assert res_wake.returncode == 0
    assert lock_file.exists()
    assert (tmp_path / "test_wake.lock.flock").exists()

    # Verify negative cases: unhealthy monitors do not create or overwrite snapshot
    unhealthy_file = tmp_path / "unhealthy.json"
    runner_unhealthy = tmp_path / "run_test_unhealthy.sh"
    runner_unhealthy.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"export PATH=\"{bin_dir}:$PATH\"\n"
        f"export WINDOW_LAYOUT_FILE=\"{unhealthy_file}\"\n"
        f"export DISPLAY=\":99\"\n"
        f"detect_display() {{ echo \":99\"; }}\n"
        f"are_monitors_configured() {{ return 1; }}\n"
        f"eval \"$(sed -n '/^save_window_layout()/,/^}}/p' '{script_path}')\"\n"
        f"save_window_layout\n",
        encoding="utf-8",
    )
    runner_unhealthy.chmod(0o755)
    res_unhealthy = subprocess.run([str(runner_unhealthy)], capture_output=True, text=True)
    assert res_unhealthy.returncode == 0
    assert not unhealthy_file.exists()

    # Verify existing snapshot is unchanged if monitors become unhealthy
    unhealthy_file.write_text("[\"preserved\"]", encoding="utf-8")
    res_unhealthy2 = subprocess.run([str(runner_unhealthy)], capture_output=True, text=True)
    assert res_unhealthy2.returncode == 0
    assert unhealthy_file.read_text(encoding="utf-8") == "[\"preserved\"]"

    # Verify negative cases: missing layout file or corrupt JSON returns without issuing xdotool commands
    xdotool_log.unlink(missing_ok=True)
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{invalid json", encoding="utf-8")

    runner_restore_corrupt = tmp_path / "run_test_corrupt.sh"
    runner_restore_corrupt.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"export PATH=\"{bin_dir}:$PATH\"\n"
        f"export WINDOW_LAYOUT_FILE=\"{corrupt_file}\"\n"
        f"export DISPLAY=\":99\"\n"
        f"detect_display() {{ echo \":99\"; }}\n"
        f"eval \"$(sed -n '/^restore_window_layout()/,/^}}/p' '{script_path}')\"\n"
        f"restore_window_layout\n"
        f"export WINDOW_LAYOUT_FILE=\"{tmp_path / 'nonexistent.json'}\"\n"
        f"restore_window_layout\n",
        encoding="utf-8",
    )
    runner_restore_corrupt.chmod(0o755)
    res_corrupt = subprocess.run([str(runner_restore_corrupt)], capture_output=True, text=True)
    assert res_corrupt.returncode == 0
    assert not xdotool_log.exists()

    # Verify restore_window_layout checks move/size command exit codes and logs failure
    fail_xdotool_bin = tmp_path / "fail_xdotool_bin"
    fail_xdotool_bin.mkdir()
    fake_xdotool_fail = fail_xdotool_bin / "xdotool"
    fake_xdotool_fail.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = 'windowmove' ]; then\n"
        "    echo \"Simulated move failure\" >&2\n"
        "    exit 1\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_xdotool_fail.chmod(0o755)

    valid_layout_file = tmp_path / "valid_restore.json"
    valid_layout_file.write_text('[{"id": "0x123", "name": "Test", "x": 10, "y": 20, "w": 300, "h": 400}]', encoding="utf-8")

    runner_fail_restore = tmp_path / "run_fail_restore.sh"
    runner_fail_restore.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"export PATH=\"{fail_xdotool_bin}:$PATH\"\n"
        f"export WINDOW_LAYOUT_FILE=\"{valid_layout_file}\"\n"
        f"export DISPLAY=\":99\"\n"
        f"detect_display() {{ echo \":99\"; }}\n"
        f"eval \"$(sed -n '/^restore_window_layout()/,/^}}/p' '{script_path}')\"\n"
        f"restore_window_layout\n",
        encoding="utf-8",
    )
    runner_fail_restore.chmod(0o755)
    res_fail_restore = subprocess.run([str(runner_fail_restore)], capture_output=True, text=True)
    assert res_fail_restore.returncode == 1
    assert "Failed to restore window 0x123 (Test): Simulated move failure" in res_fail_restore.stderr

    # Verify save-lock timeout causes restore_window_layout to skip restoration with warning
    timeout_layout = tmp_path / "timeout_layout.json"
    timeout_lock = tmp_path / "timeout_layout.json.lock"
    timeout_layout.write_text('[{"id": "0x111", "name": "Old", "x": 1, "y": 1, "w": 100, "h": 100}]', encoding="utf-8")
    timeout_lock.touch()

    # Pre-acquire save lock from separate process and hold it past 3s timeout
    timeout_ready = tmp_path / "timeout_ready"
    runner_timeout = tmp_path / "run_timeout_restore.sh"
    runner_timeout.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"export PATH=\"{fail_xdotool_bin}:$PATH\"\n"
        f"export WINDOW_LAYOUT_FILE=\"{timeout_layout}\"\n"
        f"export DISPLAY=\":99\"\n"
        f"detect_display() {{ echo \":99\"; }}\n"
        f"( exec 201>\"{timeout_lock}\"; flock 201; touch \"{timeout_ready}\"; sleep 5 ) &\n"
        f"BG_PID=$!\n"
        f"trap 'kill $BG_PID 2>/dev/null || true' EXIT\n"
        f"for i in $(seq 1 50); do [ -f \"{timeout_ready}\" ] && break; sleep 0.02; done\n"
        f"if [ ! -f \"{timeout_ready}\" ]; then echo 'Timeout waiting for background lock' >&2; exit 2; fi\n"
        f"set +e\n"
        f"eval \"$(sed -n '/^restore_window_layout()/,/^}}/p' '{script_path}')\"\n"
        f"restore_window_layout\n",
        encoding="utf-8",
    )
    runner_timeout.chmod(0o755)
    res_timeout = subprocess.run([str(runner_timeout)], capture_output=True, text=True)
    assert res_timeout.returncode == 1
    assert "Timed out waiting for save lock" in res_timeout.stderr

    # Verify restore_window_layout coordinates with active save lock
    coord_layout = tmp_path / "coord_layout.json"
    coord_lock = tmp_path / "coord_layout.json.lock"
    coord_layout.write_text('[{"id": "0x999", "name": "Old", "x": 1, "y": 1, "w": 100, "h": 100}]', encoding="utf-8")
    coord_log = tmp_path / "coord.log"

    coord_bin = tmp_path / "coord_bin"
    coord_bin.mkdir()
    (coord_bin / "xdotool").write_text(
        f"#!/bin/sh\necho \"$*\" >> '{coord_log}'\n",
        encoding="utf-8",
    )
    (coord_bin / "xdotool").chmod(0o755)

    # In background, hold flock on coord_lock while updating the file
    ready_file = tmp_path / "bg_ready"
    bg_script = tmp_path / "run_bg_save.sh"
    bg_script.write_text(
        f"#!/usr/bin/env bash\n"
        f"exec 201>\"{coord_lock}\"\n"
        f"flock 201\n"
        f"touch \"{ready_file}\"\n"
        f"sleep 0.4\n"
        f"echo '[{{\"id\": \"0x888\", \"name\": \"Updated\", \"x\": 5, \"y\": 5, \"w\": 500, \"h\": 500}}]' > \"{coord_layout}\"\n"
        f"flock -u 201\n",
        encoding="utf-8",
    )
    bg_script.chmod(0o755)

    runner_coord = tmp_path / "run_coord.sh"
    runner_coord.write_text(
        f"#!/usr/bin/env bash\n"
        f"set -e\n"
        f"export PATH=\"{coord_bin}:$PATH\"\n"
        f"export WINDOW_LAYOUT_FILE=\"{coord_layout}\"\n"
        f"export DISPLAY=\":99\"\n"
        f"detect_display() {{ echo \":99\"; }}\n"
        f"\"{bg_script}\" &\n"
        f"for i in $(seq 1 50); do [ -f \"{ready_file}\" ] && break; sleep 0.02; done\n"
        f"eval \"$(sed -n '/^restore_window_layout()/,/^}}/p' '{script_path}')\"\n"
        f"restore_window_layout\n",
        encoding="utf-8",
    )
    runner_coord.chmod(0o755)
    res_coord = subprocess.run([str(runner_coord)], capture_output=True, text=True)
    assert res_coord.returncode == 0
    assert coord_log.exists()
    # It must have restored the updated window (0x888), having waited for the bg save
    assert "0x888" in coord_log.read_text(encoding="utf-8")

    # Verify Debian package dependencies include tools required for window layout
    assert "x11-utils" in DebianSetup._DEBIAN_DEB_DEPS
    assert "xdotool" in DebianSetup._DEBIAN_DEB_DEPS




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

    # 1. Initial creation of directory symlinks
    setup.setup_agent_skills(path_local_perm_conf=str(conf_dir))

    dest_gemini = tmp_path / "home" / ".gemini" / "antigravity" / "skills" / "test-skill"
    dest_gemini_cli = tmp_path / "home" / ".gemini" / "antigravity-cli" / "skills" / "test-skill"
    dest_claude = tmp_path / "home" / ".claude" / "skills" / "test-skill"
    assert dest_gemini.is_symlink()
    assert dest_gemini_cli.is_symlink()
    assert dest_claude.is_symlink()
    assert dest_gemini.resolve() == skills_dir.resolve()
    assert dest_gemini_cli.resolve() == skills_dir.resolve()
    assert dest_claude.resolve() == skills_dir.resolve()

    # 2. Idempotent re-run leaves existing symlinks unchanged
    mtime_before = dest_gemini.lstat().st_mtime_ns
    setup.setup_agent_skills(path_local_perm_conf=str(conf_dir))
    assert dest_gemini.is_symlink()
    assert dest_gemini.lstat().st_mtime_ns == mtime_before

    # 3. Preserves unrelated existing non-symlink destination
    unrelated_skill = conf_dir / "skills" / "custom-skill"
    unrelated_skill.mkdir(parents=True)
    (unrelated_skill / "SKILL.md").write_text("---\nname: custom-skill\n---\n", encoding="utf-8")

    existing_custom_dir = tmp_path / "home" / ".claude" / "skills" / "custom-skill"
    existing_custom_dir.mkdir(parents=True)
    custom_marker = existing_custom_dir / "local_file.txt"
    custom_marker.write_text("user content", encoding="utf-8")

    setup.setup_agent_skills(path_local_perm_conf=str(conf_dir))
    assert not existing_custom_dir.is_symlink()
    assert custom_marker.exists()
    assert custom_marker.read_text(encoding="utf-8") == "user content"


def test_setup_agent_remote_control(tmp_path, monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")
    setup = DebianSetup(args_in=args)
    home_dir = tmp_path / "home"
    setup._user_home_dir = str(home_dir)

    # Pre-create bashrc and VS Code User dir
    bashrc_file = home_dir / ".bashrc"
    home_dir.mkdir(parents=True)
    bashrc_file.write_text("# existing bashrc\n", encoding="utf-8")

    vscode_user_dir = home_dir / ".config" / "Code" / "User"
    vscode_user_dir.mkdir(parents=True)
    vscode_settings = vscode_user_dir / "settings.json"
    vscode_settings.write_text("{\n  \"editor.fontSize\": 14\n}\n", encoding="utf-8")

    executed_cmds = []
    def fake_subproc(cmd, does_sudo=False, logger=None):
        executed_cmds.append(cmd)
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)
    monkeypatch.setattr(shutil, "which", lambda cmd: "/custom path with spaces/bin/agy" if cmd == "agy" else None)

    setup.setup_agent_remote_control()

    # 1. Claude Code settings.json
    path_claude_settings = home_dir / ".claude" / "settings.json"
    assert path_claude_settings.exists()
    data = json.loads(path_claude_settings.read_text(encoding="utf-8"))
    assert data.get("remoteControlAtStartup") is True

    # 2. Antigravity remote-control command safely quoted
    assert any("'/custom path with spaces/bin/agy' remote-control start" in cmd for cmd in executed_cmds)

    # 3. Antigravity CLI alias in .bashrc and executable wrapper
    assert 'alias agy-rc="agy --remote-control"' in bashrc_file.read_text(encoding="utf-8")
    agy_rc_bin = home_dir / ".local" / "bin" / "agy-rc"
    assert agy_rc_bin.exists()
    assert os.access(str(agy_rc_bin), os.X_OK)

    # Verify migration of legacy alias agy="agy --remote-control"
    bashrc_file.write_text('alias agy="agy --remote-control"\n', encoding="utf-8")
    setup.setup_agent_remote_control()
    assert 'alias agy-rc="agy --remote-control"' in bashrc_file.read_text(encoding="utf-8")
    assert 'alias agy="agy --remote-control"' not in bashrc_file.read_text(encoding="utf-8")

    # Verify migration preserves existing agy-rc alias when legacy alias is present
    bashrc_file.write_text('alias agy-rc="custom_command"\nalias agy="agy --remote-control"\n', encoding="utf-8")
    setup.setup_agent_remote_control()
    bashrc_lines = [l for l in bashrc_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert 'alias agy-rc="custom_command"' in bashrc_lines
    assert 'alias agy="agy --remote-control"' not in bashrc_lines
    assert 'alias agy-rc="agy --remote-control"' not in bashrc_lines
    assert len([l for l in bashrc_lines if l.startswith("alias agy-rc=")]) == 1

    # Verify setup does not append a duplicate when an agy-rc alias already exists
    setup.setup_agent_remote_control()
    bashrc_lines_after = [l for l in bashrc_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len([l for l in bashrc_lines_after if l.startswith("alias agy-rc=")]) == 1

    # Verify existing symlink at agy-rc is preserved without truncating target
    target_custom = home_dir / "custom_script.sh"
    target_custom.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")
    agy_rc_bin.unlink()
    agy_rc_bin.symlink_to(target_custom)
    setup.setup_agent_remote_control()
    assert agy_rc_bin.is_symlink()
    assert target_custom.read_text(encoding="utf-8") == "#!/bin/sh\necho custom\n"

    # 4. Antigravity extension serverArgs in VS Code settings.json
    data_vscode = json.loads(vscode_settings.read_text(encoding="utf-8"))
    assert "--remote-control" in data_vscode.get("antigravity.serverArgs", [])

    # 5. Verify malformed Claude settings.json is preserved and not overwritten
    path_claude_settings.write_text("{malformed json content: [", encoding="utf-8")
    setup.setup_claude_code_remote_control()
    assert path_claude_settings.read_text(encoding="utf-8") == "{malformed json content: ["
    assert len(setup._list_runtime_issues) > 0

    # 6. Verify independent sub methods can be invoked directly
    path_claude_settings.unlink()
    setup.setup_claude_code_remote_control()
    assert path_claude_settings.exists()

    setup.setup_antigravity_cli_remote_control()
    setup.setup_vscode_antigravity_remote_control()

    # 7. Verify non-executable existing wrapper restores execute permissions and updates to current header
    agy_rc_bin.unlink()
    agy_rc_bin.write_text("#!/bin/sh\nexec agy --remote-control \"$@\"\n", encoding="utf-8")
    os.chmod(str(agy_rc_bin), 0o644)
    assert not os.access(str(agy_rc_bin), os.X_OK)
    setup.setup_antigravity_cli_remote_control()
    assert os.access(str(agy_rc_bin), os.X_OK)
    assert "exec agy --remote-control" in agy_rc_bin.read_text(encoding="utf-8")

    # Verify existing current wrapper is preserved without rewriting
    os.chmod(str(agy_rc_bin), 0o644)
    setup.setup_antigravity_cli_remote_control()
    assert os.access(str(agy_rc_bin), os.X_OK)
    assert agy_rc_bin.read_text(encoding="utf-8") == "#!/bin/sh\n# Generated by hut_10sqft for Antigravity remote-control\nexec agy --remote-control \"$@\"\n"

    # 8. Verify existing custom regular file at agy-rc is preserved and not overwritten
    agy_rc_bin.write_text("#!/bin/bash\necho my-custom-tool\n", encoding="utf-8")
    setup.setup_antigravity_cli_remote_control()
    assert agy_rc_bin.read_text(encoding="utf-8") == "#!/bin/bash\necho my-custom-tool\n"

    # 9. Verify unreadable existing file is preserved and not overwritten
    os.chmod(str(agy_rc_bin), 0o000)
    setup.setup_antigravity_cli_remote_control()
    os.chmod(str(agy_rc_bin), 0o644)
    assert agy_rc_bin.read_text(encoding="utf-8") == "#!/bin/bash\necho my-custom-tool\n"

    # 10. Verify non-UTF-8 binary existing file is preserved without raising runtime issue
    agy_rc_bin.write_bytes(b"\x7fELF\x02\x01\x01\x00\xff\xfe\xfd")
    initial_issues_count = len(setup._list_runtime_issues)
    setup.setup_antigravity_cli_remote_control()
    assert agy_rc_bin.read_bytes() == b"\x7fELF\x02\x01\x01\x00\xff\xfe\xfd"
    assert len(setup._list_runtime_issues) == initial_issues_count


def test_suco_auto_detect_hostname(monkeypatch):
    monkeypatch.setattr(socket, "gethostname", lambda: "mocked-host-130s")
    assert CompInitSetup.auto_detect_hostname() == "mocked-host-130s"


def test_suco_auto_detect_os(monkeypatch):
    monkeypatch.setattr(OsUtil, "get_os_type", lambda logger=None: ("Linux", "Ubuntu"))
    os_type, os_distro = CompInitSetup.auto_detect_os()
    assert os_type == "Linux"
    assert os_distro == "Ubuntu"


def test_suco_cli_args_auto_detection(monkeypatch):
    monkeypatch.setattr(socket, "gethostname", lambda: "mocked-auto-host")
    monkeypatch.setattr(OsUtil, "get_os_type", lambda logger=None: ("Linux", "Ubuntu"))

    setup = CompInitSetup()

    # 1. When --hostname and --os_distro are omitted, _cli_args returns empty strings
    args = setup._cli_args([])
    assert args.hostname == ""
    assert args.os_distro == ""

    # 2. When passed explicitly, CLI args take precedence
    args_explicit = setup._cli_args(["--hostname", "explicit-host", "--os_distro", "Debian"])
    assert args_explicit.hostname == "explicit-host"
    assert args_explicit.os_distro == "Debian"


def test_suco_run_auto_detection(monkeypatch):
    monkeypatch.setattr(socket, "gethostname", lambda: "mocked-auto-host")
    monkeypatch.setattr(OsUtil, "get_os_type", lambda logger=None: ("Linux", "Ubuntu"))

    setup = CompInitSetup()
    captured_builder = []

    class FakeOsBuilder:
        _OS_TYPE = "Ubuntu"
        def __init__(self, args_in=None):
            self.args_in = args_in
            captured_builder.append(self)

        def run(self, host_cfg, conf_repo_remote="", conf_base_path=""):
            return True

        def listup_runtime_issues(self):
            pass

    monkeypatch.setattr("hut_10sqft.suco_main.UbuntuOsSetup", FakeOsBuilder)

    assert setup.run(args_list=[]) is True
    assert len(captured_builder) == 1
    assert captured_builder[0].args_in.hostname == "mocked-auto-host"
    assert captured_builder[0].args_in.os_distro == "Ubuntu"
    assert captured_builder[0].args_in.os_type == "Linux"


def test_suco_run_auto_detect_chromeos(monkeypatch):
    monkeypatch.setattr(socket, "gethostname", lambda: CompInitSetupConfig.HOSTNAME_BRYA)
    monkeypatch.setattr(OsUtil, "get_os_type", lambda logger=None: ("Linux", "Debian"))

    setup = CompInitSetup()
    captured_builder = []

    class FakeChromeOsBuilder:
        _OS_TYPE = ChromeOsSetup._OS_TYPE
        def __init__(self, args_in=None):
            self.args_in = args_in
            captured_builder.append(self)

        def run(self, host_cfg, conf_repo_remote="", conf_base_path=""):
            return True

        def listup_runtime_issues(self):
            pass

    monkeypatch.setattr("hut_10sqft.suco_main.ChromeOsSetup", FakeChromeOsBuilder)

    assert setup.run(args_list=[]) is True
    assert len(captured_builder) == 1
    assert captured_builder[0].args_in.os_distro == ChromeOsSetup._OS_TYPE


def test_suco_run_auto_detect_macos(monkeypatch):
    from hut_10sqft.comp_mac_os import MacOsSetup

    monkeypatch.setattr(socket, "gethostname", lambda: CompInitSetupConfig.HOSTNAME_MAC1)
    monkeypatch.setattr(OsUtil, "get_os_type", lambda logger=None: ("MacOS", "None"))

    setup = CompInitSetup()
    assert setup.run(args_list=[]) is True


def test_suco_installer_cli_args():
    installer = SucoInstaller()
    args_default = installer.cli_args_install_suco(args_list=[])
    assert args_default.build_colcon is False
    assert args_default.pip_install is False

    args_custom = installer.cli_args_install_suco(args_list=["--build_colcon", "--pip_install"])
    assert args_custom.build_colcon is True
    assert args_custom.pip_install is True


def test_suco_installer_main_clone(tmp_path, monkeypatch):
    installer = SucoInstaller()
    base_conf = tmp_path / "config"
    commands_run = []

    def fake_subprocess_run(cmd, cwd=None, **kwargs):
        commands_run.append({"cmd": cmd, "cwd": cwd})
        return subprocess.CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    dest_repo = str(base_conf / CompInitSetupConfig.REPO_PERMANENT_CONFIG)
    installer.main(args_list=["--path_base_conf", str(base_conf), "--git_branch", "develop"])

    assert len(commands_run) == 1
    assert commands_run[0]["cmd"] == ["git", "clone", CompInitSetupConfig.URL_HUT, "-b", "develop", dest_repo]
    assert commands_run[0]["cwd"] is None


def test_suco_installer_main_pull_and_pip(tmp_path, monkeypatch):
    installer = SucoInstaller()
    base_conf = tmp_path / "config"
    dest_repo = base_conf / CompInitSetupConfig.REPO_PERMANENT_CONFIG
    git_dir = dest_repo / ".git"
    git_dir.mkdir(parents=True)

    commands_run = []

    def fake_subprocess_run(cmd, cwd=None, **kwargs):
        commands_run.append({"cmd": cmd, "cwd": cwd})
        return subprocess.CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    installer.main(args_list=["--path_base_conf", str(base_conf), "--pip_install", "--pip_break_syspkg"])

    assert len(commands_run) == 2
    assert commands_run[0]["cmd"] == ["git", "pull"]
    assert commands_run[0]["cwd"] == str(dest_repo)
    assert commands_run[1]["cmd"] == ["pip3", "install", "-e", str(dest_repo), "--break-system-packages"]


def test_suco_installer_pip_oserror_fallback(tmp_path, monkeypatch):
    from hut_10sqft.suco_installer import main as installer_main

    base_conf = tmp_path / "config"
    dest_repo = base_conf / CompInitSetupConfig.REPO_PERMANENT_CONFIG
    git_dir = dest_repo / ".git"
    git_dir.mkdir(parents=True)

    def fake_subprocess_run(cmd, cwd=None, **kwargs):
        if cmd[0] == "pip3":
            raise FileNotFoundError("pip3 not found")
        return subprocess.CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)
    monkeypatch.setattr("sys.argv", ["suco_installer", "--path_base_conf", str(base_conf), "--pip_install"])

    # Should not raise FileNotFoundError / OSError, should catch and finish cleanly
    installer_main()


def test_ubuntu_snap_pkgs_excludes_docker():
    """Verify that docker is removed from snap packages in UbuntuOsSetup."""
    assert "docker" not in UbuntuOsSetup._PKGS_SNAP
    assert UbuntuOsSetup._PKGS_SNAP == ["yt-dlp"]


def test_setup_docker_skip(monkeypatch):
    """Verify that setup_docker returns immediately when skip is True."""
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    cmds_run = []
    monkeypatch.setattr(OsUtil, "subproc_bash", lambda cmd, **kwargs: (cmds_run.append(cmd), ("", "", 0))[1])
    setup.setup_docker(userid_os="test-user", skip=True)
    assert len(cmds_run) == 0


def test_setup_docker_already_completed(monkeypatch):
    """Verify that setup_docker returns early if docker and docker-ce package are already setup."""
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    monkeypatch.setattr(setup, "_is_docker_setup", lambda: 0)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)
    monkeypatch.setattr(OsUtil, "subproc_bash", lambda cmd, **kwargs: ("Status: install ok installed", "", 0))

    called_apt = []
    monkeypatch.setattr(OsUtil, "apt_install", lambda pkgs, logger=None: called_apt.append(pkgs))

    setup.setup_docker(userid_os="test-user", skip=False)
    assert len(called_apt) == 0


def test_setup_docker_retained_config_does_not_skip(monkeypatch):
    """Verify that setup_docker proceeds if docker-ce has only retained config files."""
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    monkeypatch.setattr(setup, "_is_docker_setup", lambda: 0)
    monkeypatch.setattr(setup, "apt_update", lambda force=False: None)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)

    called_apt = []
    monkeypatch.setattr(OsUtil, "apt_install", lambda pkgs, logger=None: called_apt.append(pkgs))

    def fake_subproc(cmd, does_sudo=False, non_interactive=False, logger=None, print_stdout_err=False):
        if "dpkg -s docker-ce" in cmd:
            return "Status: deinstall ok config-files", "", 0
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)

    setup.setup_docker(userid_os="test-user", skip=False)
    assert len(called_apt) > 0
    assert setup._DEBS_DOCKER in called_apt


def test_setup_docker_proceeds_when_ce_package_missing(monkeypatch):
    """Verify that setup_docker proceeds with CE installation if docker command exists but docker-ce package is not installed."""
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    monkeypatch.setattr(setup, "_is_docker_setup", lambda: 0)
    monkeypatch.setattr(setup, "apt_update", lambda force=False: None)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)

    called_apt = []
    monkeypatch.setattr(OsUtil, "apt_install", lambda pkgs, logger=None: called_apt.append(pkgs))

    def fake_subproc(cmd, does_sudo=False, non_interactive=False, logger=None, print_stdout_err=False):
        if "dpkg -s docker-ce" in cmd:
            return "", "package docker-ce is not installed", 1
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)

    setup.setup_docker(userid_os="test-user", skip=False)
    assert len(called_apt) > 0
    assert setup._DEBS_DOCKER in called_apt


def test_setup_docker_installs_docker_ce_apt(monkeypatch):
    """Verify modern Docker CE repository and packages are installed."""
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    def fake_is_docker_setup():
        raise RuntimeWarning("Docker setup is not done yet")

    monkeypatch.setattr(setup, "_is_docker_setup", fake_is_docker_setup)
    monkeypatch.setattr(setup, "apt_update", lambda force=False: None)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)

    called_apt = []
    cmds_run = []

    monkeypatch.setattr(OsUtil, "apt_install", lambda pkgs, logger=None: called_apt.append(pkgs))
    def fake_subproc(cmd, does_sudo=False, non_interactive=False, logger=None, print_stdout_err=False):
        cmds_run.append(cmd)
        if "dpkg -s docker.io" in cmd:
            return "Status: install ok installed", "", 0
        return "", "", 0
    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)

    setup.setup_docker(userid_os="test-user", skip=False)

    assert called_apt[0] == ["ca-certificates", "curl"]
    assert called_apt[1] == ["docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"]

    assert any("apt remove -y docker.io" in c for c in cmds_run)
    assert any("https://download.docker.com/linux/ubuntu/gpg" in c for c in cmds_run)
    assert any("/etc/apt/keyrings/docker.asc" in c for c in cmds_run)
    assert any("https://download.docker.com/linux/ubuntu" in c for c in cmds_run)
    assert any("groupadd -f docker" in c for c in cmds_run)
    assert any("usermod -aG docker test-user" in c for c in cmds_run)
    assert any("systemctl enable --now docker" in c for c in cmds_run)


def test_setup_docker_conflict_removal_failure_stops_setup(monkeypatch):
    """Verify that a failure in removing installed conflicting packages raises RuntimeError and stops setup."""
    import pytest
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    def fake_is_docker_setup():
        raise RuntimeWarning("Docker setup is not done yet")

    monkeypatch.setattr(setup, "_is_docker_setup", fake_is_docker_setup)
    monkeypatch.setattr(setup, "apt_update", lambda force=False: None)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)
    monkeypatch.setattr(OsUtil, "apt_install", lambda pkgs, logger=None: None)

    def fake_subproc(cmd, does_sudo=False, non_interactive=False, logger=None, print_stdout_err=False):
        if "dpkg -s docker.io" in cmd:
            return "Status: install ok installed", "", 0
        if "apt remove -y docker.io" in cmd:
            return "", "dpkg was interrupted", 100
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)

    with pytest.raises(RuntimeError) as exc_info:
        setup.setup_docker(userid_os="test-user", skip=False)

    assert "Failed to remove conflicting Docker packages (docker.io) with exit code 100" in str(exc_info.value)
    assert any("dpkg was interrupted" in str(issue) for issue in setup._list_runtime_issues)


def test_setup_docker_apt_update_failure(monkeypatch):
    """Verify that subprocess.CalledProcessError from apt_update raises RuntimeError and records runtime issue."""
    import subprocess
    import pytest
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    def fake_is_docker_setup():
        raise RuntimeWarning("Docker setup is not done yet")

    monkeypatch.setattr(setup, "_is_docker_setup", fake_is_docker_setup)
    def fake_apt_update(force=False):
        raise subprocess.CalledProcessError(returncode=100, cmd="apt update", stderr="Failed to fetch repository")
    monkeypatch.setattr(setup, "apt_update", fake_apt_update)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)
    monkeypatch.setattr(OsUtil, "apt_install", lambda pkgs, logger=None: None)
    monkeypatch.setattr(OsUtil, "subproc_bash", lambda cmd, **kwargs: ("", "", 0))

    with pytest.raises(RuntimeError) as exc_info:
        setup.setup_docker(userid_os="test-user", skip=False)

    assert "Failed to update package index for Docker CE: Failed to fetch repository" in str(exc_info.value)
    assert any("Failed to fetch repository" in str(issue) for issue in setup._list_runtime_issues)


def test_setup_docker_apt_install_failure(monkeypatch):
    """Verify that RuntimeWarning from OsUtil.apt_install raises RuntimeError and records runtime issue."""
    import pytest
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    def fake_apt_update(force=False):
        pass

    monkeypatch.setattr(setup, "apt_update", fake_apt_update)
    monkeypatch.setattr(setup, "_is_docker_setup", lambda: 0)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)
    monkeypatch.setattr(OsUtil, "subproc_bash", lambda cmd, **kwargs: ("", "", 0))

    def fake_apt_install(pkgs, logger=None):
        if "docker-ce" in pkgs:
            raise RuntimeWarning("The following pkgs didn't get installed:\n - docker-ce")

    monkeypatch.setattr(OsUtil, "apt_install", fake_apt_install)

    with pytest.raises(RuntimeError) as exc_info:
        setup.setup_docker(userid_os="test-user", skip=False)

    assert "Failed to install Docker CE packages" in str(exc_info.value)
    assert any("Failed to install Docker CE packages" in str(issue) for issue in setup._list_runtime_issues)


def test_setup_docker_prereq_install_failure(monkeypatch):
    """Verify that RuntimeWarning from installing prerequisites raises RuntimeError and records runtime issue."""
    import pytest
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    monkeypatch.setattr(setup, "_is_docker_setup", lambda: 0)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)
    monkeypatch.setattr(OsUtil, "subproc_bash", lambda cmd, **kwargs: ("", "", 0))

    def fake_apt_install(pkgs, logger=None):
        if setup._DEBS_DOCKER_PREREQ == pkgs:
            raise RuntimeWarning("The following pkgs didn't get installed:\n - ca-certificates")

    monkeypatch.setattr(OsUtil, "apt_install", fake_apt_install)

    with pytest.raises(RuntimeError) as exc_info:
        setup.setup_docker(userid_os="test-user", skip=False)

    assert "Failed to install Docker prerequisites" in str(exc_info.value)
    assert any("Failed to install Docker prerequisites" in str(issue) for issue in setup._list_runtime_issues)


def test_setup_docker_key_download_failure(monkeypatch):
    """Verify that failure downloading Docker GPG key raises RuntimeError and records runtime issue."""
    import pytest
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    monkeypatch.setattr(setup, "_is_docker_setup", lambda: 0)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)
    monkeypatch.setattr(OsUtil, "apt_install", lambda pkgs, logger=None: None)

    def fake_subproc(cmd, **kwargs):
        if "curl" in cmd and "gpg" in cmd:
            return "", "curl: (6) Could not resolve host: download.docker.com", 6
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)

    with pytest.raises(RuntimeError) as exc_info:
        setup.setup_docker(userid_os="test-user", skip=False)

    assert "Failed to download Docker GPG key" in str(exc_info.value)
    assert any("Failed to download Docker GPG key" in str(issue) for issue in setup._list_runtime_issues)


def test_setup_docker_repo_write_failure(monkeypatch):
    """Verify that failure writing docker.list raises RuntimeError and records runtime issue."""
    import pytest
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    monkeypatch.setattr(setup, "_is_docker_setup", lambda: 0)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)
    monkeypatch.setattr(OsUtil, "apt_install", lambda pkgs, logger=None: None)

    def fake_subproc(cmd, **kwargs):
        if "docker.list" in cmd:
            return "", "Permission denied", 1
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)

    with pytest.raises(RuntimeError) as exc_info:
        setup.setup_docker(userid_os="test-user", skip=False)

    assert "Failed to write Docker repository configuration" in str(exc_info.value)
    assert any("Failed to write Docker repository configuration" in str(issue) for issue in setup._list_runtime_issues)


def test_setup_docker_usermod_failure(monkeypatch):
    """Verify that failure adding user to docker group raises RuntimeError and records runtime issue."""
    import pytest
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    monkeypatch.setattr(setup, "_is_docker_setup", lambda: 0)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)
    monkeypatch.setattr(OsUtil, "apt_install", lambda pkgs, logger=None: None)
    monkeypatch.setattr(setup, "apt_update", lambda force=False: None)

    def fake_subproc(cmd, **kwargs):
        if "usermod" in cmd:
            return "", "usermod: user 'test-user' does not exist", 6
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)

    with pytest.raises(RuntimeError) as exc_info:
        setup.setup_docker(userid_os="test-user", skip=False)

    assert "Failed to add user 'test-user' to 'docker' group" in str(exc_info.value)
    assert any("Failed to add user 'test-user' to 'docker' group" in str(issue) for issue in setup._list_runtime_issues)


def test_setup_docker_removes_snap_docker(monkeypatch):
    """Verify conflicting snap docker is removed if present."""
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    monkeypatch.setattr(setup, "_is_docker_setup", lambda: 0)
    monkeypatch.setattr(OsUtil, "which", lambda name: "/usr/bin/snap" if name == "snap" else None)

    cmds_run = []
    def fake_subproc(cmd, does_sudo=False, non_interactive=False, logger=None, print_stdout_err=False):
        cmds_run.append(cmd)
        if cmd == "snap list docker":
            return "Name Version Rev Tracking Publisher Notes\ndocker 27.2.0 2932 latest/stable canonical** -", "", 0
        if "dpkg -s docker-ce" in cmd:
            return "Status: install ok installed", "", 0
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)
    setup.setup_docker(userid_os="test-user", skip=False)

    assert any("snap remove docker" in c for c in cmds_run)


def test_setup_docker_removes_snap_docker_failure(monkeypatch):
    """Verify failure to remove conflicting snap docker raises RuntimeError, records runtime issue, and stops setup before _is_docker_setup."""
    import pytest

    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    is_docker_setup_called = []
    def fake_is_docker_setup():
        is_docker_setup_called.append(True)
        return 0

    monkeypatch.setattr(setup, "_is_docker_setup", fake_is_docker_setup)
    monkeypatch.setattr(OsUtil, "which", lambda name: "/usr/bin/snap" if name == "snap" else None)

    def fake_subproc(cmd, does_sudo=False, non_interactive=False, logger=None, print_stdout_err=False):
        if cmd == "snap list docker":
            return "docker 27.2.0 2932 latest/stable canonical** -", "", 0
        if "snap remove docker" in cmd:
            return "", "error: cannot remove docker: snap has running services", 1
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)

    with pytest.raises(RuntimeError) as exc_info:
        setup.setup_docker(userid_os="test-user", skip=False)

    assert "Failed to remove conflicting docker snap package (exit code 1)" in str(exc_info.value)
    assert any("cannot remove docker" in str(issue) for issue in setup._list_runtime_issues)
    assert len(is_docker_setup_called) == 0


def test_setup_docker_installs_docker_ce_apt_debian(monkeypatch):
    """Verify modern Docker CE repository and packages are installed on Debian."""
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "debian"

    def fake_is_docker_setup():
        raise RuntimeWarning("Docker setup is not done yet")

    monkeypatch.setattr(setup, "_is_docker_setup", fake_is_docker_setup)
    monkeypatch.setattr(setup, "apt_update", lambda force=False: None)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)

    called_apt = []
    cmds_run = []

    monkeypatch.setattr(OsUtil, "apt_install", lambda pkgs, logger=None: called_apt.append(pkgs))
    def fake_subproc(cmd, does_sudo=False, non_interactive=False, logger=None, print_stdout_err=False):
        cmds_run.append(cmd)
        return "", "", 0
    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)

    setup.setup_docker(userid_os="test-user", skip=False)

    assert any("https://download.docker.com/linux/debian/gpg" in c for c in cmds_run)
    assert any("https://download.docker.com/linux/debian" in c for c in cmds_run)


def test_setup_docker_verification_failure(monkeypatch):
    """Verify that a nonzero exit from 'docker run hello-world' raises an error and records a runtime issue."""
    import pytest

    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    def fake_is_docker_setup():
        raise RuntimeWarning("Docker setup is not done yet")

    monkeypatch.setattr(setup, "_is_docker_setup", fake_is_docker_setup)
    monkeypatch.setattr(setup, "apt_update", lambda force=False: None)
    monkeypatch.setattr(OsUtil, "which", lambda name: None)
    monkeypatch.setattr(OsUtil, "apt_install", lambda pkgs, logger=None: None)

    def fake_subproc(cmd, does_sudo=False, non_interactive=False, logger=None, print_stdout_err=False):
        if "docker run --rm hello-world" in cmd:
            return "", "Cannot connect to the Docker daemon", 1
        return "", "", 0

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)

    with pytest.raises(RuntimeError) as exc_info:
        setup.setup_docker(userid_os="test-user", skip=False)

    assert "exit code 1" in str(exc_info.value)
    assert "Cannot connect to the Docker daemon" in str(exc_info.value)
    assert len(setup._list_runtime_issues) > 0
    assert any("exit code 1" in str(issue) for issue in setup._list_runtime_issues)


def test_setup_docker_invalid_userid(monkeypatch):
    """Verify that an invalid userid_os raises ValueError before executing any system commands."""
    import pytest

    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=False, user_id="test-user")
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"

    commands_run = []
    monkeypatch.setattr(OsUtil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(OsUtil, "subproc_bash", lambda cmd, **kwargs: (commands_run.append(cmd) or ("", "", 0)))

    with pytest.raises(ValueError) as exc_info:
        setup.setup_docker(userid_os="invalid user; rm -rf /", skip=False)
    assert "Invalid username" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        setup.setup_docker(userid_os="alice\n", skip=False)
    assert "Invalid username" in str(exc_info.value)
    assert len(commands_run) == 0


def test_shell_capable_os_setup_catches_docker_runtime_error(monkeypatch):
    """Verify ShellCapableOsSetup.run records RuntimeError from setup_docker without duplicate entries or aborting setup."""
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    args = CompInitSetup()._cli_args([])
    args.hostname = "test-host"
    args.skip_setup_docker = False
    args.user_id = "test-user"
    args.skip_dropbox = True
    setup = DebianSetup(args_in=args)
    setup._os_name = "ubuntu"
    monkeypatch.setattr(setup, "clone", lambda *args, **kwargs: None)
    err = RuntimeError("Docker verification failed")
    setup.add_runtime_issue(err)
    monkeypatch.setattr(setup, "setup_docker", lambda *args, **kwargs: (_ for _ in ()).throw(err))
    monkeypatch.setattr(setup, "update_hostname", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "setup_rosdep_and_run", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "nonrosdep_deps", lambda *args, **kwargs: ([], []))
    monkeypatch.setattr(setup, "install_deps_adhoc", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "swap_caps_ctrl", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "setup_terminal_configs", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "setup_ssh", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "setup_git_config", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "setup_agent_skills", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "setup_antigravity_cli", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "setup_agent_remote_control", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "create_data_dir", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "generate_symlinks", lambda *args, **kwargs: [])
    monkeypatch.setattr(setup, "common_symlinks", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "setup_configs", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "setup_vscode", lambda *args, **kwargs: None)
    monkeypatch.setattr(setup, "setup_swapfile", lambda *args, **kwargs: False)

    host_cfg = HostConf("test-host", "bashrc", "emacs", "rsa", "pub")
    setup.run(host_cfg, conf_repo_remote="https://github.com/kinu-garage/hut_10sqft.git", conf_base_path="/tmp")
    issues = [issue for issue in setup._list_runtime_issues if "Docker verification failed" in str(issue)]
    assert len(issues) == 1


def test_os_util_whereis_docker_none(monkeypatch):
    """Verify whereis_docker returns 'none' when docker is not installed."""
    monkeypatch.setattr(OsUtil, "which", lambda name: None)
    assert OsUtil.whereis_docker() == "none"


def test_os_util_whereis_docker_snap(monkeypatch):
    """Verify whereis_docker returns 'snap' when docker is installed via snap."""
    def fake_which(name):
        if name == "docker":
            return "/snap/bin/docker"
        if name == "snap":
            return "/usr/bin/snap"
        return None

    monkeypatch.setattr(OsUtil, "which", fake_which)
    monkeypatch.setattr(OsUtil, "subproc_bash", lambda cmd, **kwargs: ("docker 27.2.0", "", 0))
    assert OsUtil.whereis_docker() == "snap"


def test_os_util_whereis_docker_snap_var_lib(monkeypatch):
    """Verify whereis_docker returns 'snap' when docker executable is under /var/lib/snapd/snap/bin."""
    monkeypatch.setattr(OsUtil, "which", lambda name: "/var/lib/snapd/snap/bin/docker" if name == "docker" else None)
    monkeypatch.setattr(os.path, "realpath", lambda path: path)
    assert OsUtil.whereis_docker() == "snap"


def test_os_util_whereis_docker_snap_symlink_snapd(monkeypatch):
    """Verify whereis_docker returns 'snap' when docker executable resolves to a snapd-owned binary."""
    monkeypatch.setattr(OsUtil, "which", lambda name: "/usr/bin/docker" if name == "docker" else None)
    monkeypatch.setattr(os.path, "realpath", lambda path: "/usr/bin/snap")

    def fake_subproc(cmd, **kwargs):
        if "dpkg -S" in cmd:
            return "snapd: /usr/bin/snap", "", 0
        return "", "", 1

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)
    assert OsUtil.whereis_docker() == "snap"


def test_os_util_whereis_docker_apt_ce(monkeypatch):
    """Verify whereis_docker returns 'apt (docker-ce)' when docker is owned by docker-ce-cli and docker-ce is installed."""
    monkeypatch.setattr(OsUtil, "which", lambda name: "/usr/bin/" + name if name == "docker" else None)
    monkeypatch.setattr(os.path, "realpath", lambda path: path)

    def fake_subproc(cmd, **kwargs):
        if "dpkg -S" in cmd:
            return "docker-ce-cli: /usr/bin/docker", "", 0
        if "dpkg -s docker-ce" in cmd:
            return "Package: docker-ce\nStatus: install ok installed", "", 0
        return "", "", 1

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)
    assert OsUtil.whereis_docker() == "apt (docker-ce)"


def test_os_util_whereis_docker_apt_io(monkeypatch):
    """Verify whereis_docker returns 'apt (docker.io)' when docker is owned by docker.io and docker.io is installed."""
    monkeypatch.setattr(OsUtil, "which", lambda name: "/usr/bin/" + name if name == "docker" else None)
    monkeypatch.setattr(os.path, "realpath", lambda path: path)

    def fake_subproc(cmd, **kwargs):
        if "dpkg -S" in cmd:
            return "docker.io: /usr/bin/docker", "", 0
        if "dpkg -s docker.io" in cmd:
            return "Package: docker.io\nStatus: install ok installed", "", 0
        return "", "", 1

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)
    assert OsUtil.whereis_docker() == "apt (docker.io)"


def test_os_util_whereis_docker_other_unowned_binary(monkeypatch):
    """Verify whereis_docker returns 'other: /usr/local/bin/docker' when the binary is not owned by dpkg."""
    monkeypatch.setattr(OsUtil, "which", lambda name: "/usr/local/bin/docker" if name == "docker" else None)
    monkeypatch.setattr(os.path, "realpath", lambda path: path)

    def fake_subproc(cmd, **kwargs):
        # Even if docker-ce happens to be installed on the system, the active binary in /usr/local/bin is unowned
        if "dpkg -s docker-ce" in cmd:
            return "Package: docker-ce\nStatus: install ok installed", "", 0
        if "dpkg -S" in cmd:
            return "dpkg-query: no path found matching pattern /usr/local/bin/docker", "", 1
        return "", "", 1

    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc)
    assert OsUtil.whereis_docker() == "other: /usr/local/bin/docker"


def test_os_util_whereis_docker_brew(monkeypatch):
    """Verify whereis_docker returns 'brew' when installed via Homebrew."""
    monkeypatch.setattr(OsUtil, "which", lambda name: "/opt/homebrew/bin/docker" if name == "docker" else None)
    monkeypatch.setattr(os.path, "realpath", lambda path: path)
    monkeypatch.setattr(OsUtil, "subproc_bash", lambda cmd, **kwargs: ("", "", 1))
    assert OsUtil.whereis_docker() == "brew"


def test_os_util_whereis_docker_desktop(monkeypatch):
    """Verify whereis_docker returns 'docker-desktop' when resolving to Docker.app."""
    monkeypatch.setattr(OsUtil, "which", lambda name: "/usr/local/bin/docker" if name == "docker" else None)
    monkeypatch.setattr(os.path, "realpath", lambda path: "/Applications/Docker.app/Contents/Resources/bin/docker")
    monkeypatch.setattr(OsUtil, "subproc_bash", lambda cmd, **kwargs: ("", "", 1))
    assert OsUtil.whereis_docker() == "docker-desktop"


def test_suco_run_whereis_docker(capsys, monkeypatch):
    """Verify 'suco whereis_docker' prints the result to stdout and returns True."""
    monkeypatch.setattr(OsUtil, "whereis_docker", lambda logger=None: "apt (docker-ce)")
    comp_setup = CompInitSetup()
    res = comp_setup.run(["whereis_docker"])
    assert res is True
    captured = capsys.readouterr()
    assert "apt (docker-ce)" in captured.out


def _write_swap_fixtures(tmp_path, swaps_lines, mem_available_kb, fstab_text):
    path_swaps = tmp_path / "swaps"
    path_swaps.write_text("Filename\tType\tSize\tUsed\tPriority\n" + "".join(swaps_lines))
    path_meminfo = tmp_path / "meminfo"
    path_meminfo.write_text(f"MemTotal:       32556336 kB\nMemAvailable:   {mem_available_kb} kB\n")
    path_fstab = tmp_path / "fstab"
    path_fstab.write_text(fstab_text)
    return str(path_swaps), str(path_meminfo), str(path_fstab)


def test_setup_swapfile_resizes_and_persists(tmp_path, monkeypatch):
    path_swapfile = str(tmp_path / "swapfile")
    with open(path_swapfile, "wb") as f:
        f.truncate(2 * 1024 * 1024 * 1024)
    path_swaps, path_meminfo, path_fstab = _write_swap_fixtures(
        tmp_path, [f"{path_swapfile} file 2097148 2095924 -2\n"], 5663964, "# empty\n")

    executed_cmds = []
    def fake_subproc_bash(cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False):
        executed_cmds.append((cmd, does_sudo))
        if cmd.startswith("stat -f"):
            return "ext2/ext3", "", 0
        if cmd.startswith("swapon"):
            with open(path_swaps, "w") as f:
                f.write(f"Filename\tType\tSize\tUsed\tPriority\n{path_swapfile} file 16777212 0 -2\n")
        if "tee -a" in cmd:
            # The fstab target is under tmp_path, so the real command runs without sudo.
            subprocess.run(["/bin/sh", "-c", cmd], check=True)
        return "", "", 0
    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc_bash)
    monkeypatch.setattr(shutil, "disk_usage", lambda path: argparse.Namespace(free=100 * 1024 ** 3))

    assert OsUtil.setup_swapfile(16, path_swapfile, path_swaps, path_meminfo, path_fstab) is True
    cmds = [c for c, _ in executed_cmds if not c.startswith("stat -f")]
    assert [c.split()[0] for c in cmds] == ["swapoff", "rm", "fallocate", "chmod", "mkswap", "swapon", "printf"]
    assert "fallocate -l 16G" in cmds[2]
    assert all(sudo for c, sudo in executed_cmds if not c.startswith("stat -f"))

    # Re-running is a no-op once the swapfile is sized and persisted.
    executed_cmds.clear()
    assert OsUtil.setup_swapfile(16, path_swapfile, path_swaps, path_meminfo, path_fstab) is False
    assert executed_cmds == []


def test_setup_swapfile_path_with_whitespace_and_quote(tmp_path, monkeypatch):
    dir_swap = tmp_path / "my swap's dir"
    dir_swap.mkdir()
    path_swapfile = str(dir_swap / "swap\tfile")
    path_encoded = OsUtil.encode_fstab_field(path_swapfile)
    assert " " not in path_encoded and "\t" not in path_encoded
    assert OsUtil.decode_fstab_field(path_encoded) == path_swapfile
    path_swaps, path_meminfo, path_fstab = _write_swap_fixtures(tmp_path, [], 5663964, "# empty\n")

    def fake_subproc_bash(cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False):
        if cmd.startswith("stat -f"):
            return "ext2/ext3", "", 0
        if cmd.startswith("swapon"):
            # The kernel escapes whitespace in /proc/swaps the same way as fstab.
            with open(path_swaps, "w") as f:
                f.write(f"Filename\tType\tSize\tUsed\tPriority\n{path_encoded} file 16777212 0 -2\n")
        if "tee -a" in cmd:
            subprocess.run(["/bin/sh", "-c", cmd], check=True)
        return "", "", 0
    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc_bash)
    monkeypatch.setattr(shutil, "disk_usage", lambda path: argparse.Namespace(free=100 * 1024 ** 3))

    assert OsUtil.setup_swapfile(16, path_swapfile, path_swaps, path_meminfo, path_fstab) is True
    with open(path_fstab) as f:
        entries = [line.split() for line in f if not line.startswith("#")]
    assert entries == [[path_encoded, "none", "swap", "sw", "0", "0"]]

    # Both /proc/swaps and fstab are matched after decoding, so a re-run is a no-op and adds no duplicate.
    assert OsUtil.setup_swapfile(16, path_swapfile, path_swaps, path_meminfo, path_fstab) is False
    with open(path_fstab) as f:
        assert sum(1 for line in f if not line.startswith("#")) == 1


@pytest.mark.parametrize("fstab_text,expected", [
    ("UUID=abc / ext4 defaults 0 1", "UUID=abc / ext4 defaults 0 1\n{entry}\n"),     # no trailing newline
    ("UUID=abc / ext4 defaults 0 1\n", "UUID=abc / ext4 defaults 0 1\n{entry}\n"),   # trailing newline
    ("", "{entry}\n"),                                                               # empty
    (None, "{entry}\n"),                                                             # missing
])
def test_setup_swapfile_fstab_entry_is_its_own_line(tmp_path, monkeypatch, fstab_text, expected):
    path_swapfile = str(tmp_path / "swapfile")
    path_swaps, path_meminfo, path_fstab = _write_swap_fixtures(
        tmp_path, [f"{path_swapfile} file 16777212 0 -2\n"], 5663964, "")
    if fstab_text is None:
        os.remove(path_fstab)
    else:
        with open(path_fstab, "w") as f:
            f.write(fstab_text)

    def fake_subproc_bash(cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False):
        assert cmd.startswith("printf "), cmd
        subprocess.run(["/bin/sh", "-c", cmd], check=True)
        return "", "", 0
    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc_bash)

    # Already active at the requested size, so only the fstab entry is ensured. A re-run adds nothing.
    for _ in range(2):
        assert OsUtil.setup_swapfile(16, path_swapfile, path_swaps, path_meminfo, path_fstab) is False
    with open(path_fstab) as f:
        assert f.read() == expected.format(entry=f"{path_swapfile} none swap sw 0 0")


def test_setup_swapfile_refuses_when_ram_cannot_absorb_swap(tmp_path, monkeypatch):
    path_swapfile = str(tmp_path / "swapfile")
    open(path_swapfile, "wb").close()
    path_swaps, path_meminfo, path_fstab = _write_swap_fixtures(
        tmp_path, [f"{path_swapfile} file 2097148 2095924 -2\n"], 1000000, f"{path_swapfile} none swap sw 0 0\n")

    executed_cmds = []
    def fake_subproc_bash(cmd, does_sudo=False, print_stdout_err=False, logger=None, non_interactive=False):
        executed_cmds.append(cmd)
        return "ext2/ext3", "", 0
    monkeypatch.setattr(OsUtil, "subproc_bash", fake_subproc_bash)
    monkeypatch.setattr(shutil, "disk_usage", lambda path: argparse.Namespace(free=100 * 1024 ** 3))

    with pytest.raises(RuntimeWarning, match="Retry when the system is less loaded"):
        OsUtil.setup_swapfile(16, path_swapfile, path_swaps, path_meminfo, path_fstab)
    assert not any(c.startswith("swapoff") for c in executed_cmds)

    with pytest.raises(ValueError):
        OsUtil.setup_swapfile(0, path_swapfile, path_swaps, path_meminfo, path_fstab)


def test_setup_swapfile_skipped_per_os(monkeypatch):
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    called = []
    monkeypatch.setattr(OsUtil, "setup_swapfile", lambda *a, **kw: called.append(a) or True)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")

    assert DebianSetup(args_in=args).setup_swapfile(skip=True) is False
    assert ChromeOsSetup(args_in=args).setup_swapfile() is False
    assert called == []
    assert DebianSetup(args_in=args).setup_swapfile(size_gb=16) is True
    assert called[0][0] == 16


@pytest.mark.parametrize("err", [
    RuntimeWarning("not enough disk space"),
    RuntimeError("'mkswap /swapfile' failed"),
    FileNotFoundError(2, "No such file or directory", "/proc/swaps"),
    PermissionError(13, "Permission denied", "/etc/fstab"),
])
def test_debian_run_records_swapfile_errors(monkeypatch, err):
    from hut_10sqft.abst_comp_setup import ShellCapableOsSetup
    monkeypatch.setattr(DebianSetup, "_setup_git", lambda self: None)
    monkeypatch.setattr(ShellCapableOsSetup, "run", lambda self, *a, **kw: None)
    def raise_err(*a, **kw):
        raise err
    monkeypatch.setattr(OsUtil, "setup_swapfile", raise_err)
    args = argparse.Namespace(hostname="test-host", skip_setup_docker=True, user_id="test-user")
    setup = DebianSetup(args_in=args)

    setup.run(HostConf("test-host", "bashrc", "emacs", "rsa", "pub"), conf_repo_remote="")
    assert err in setup._list_runtime_issues


def test_suco_setup_swap_subcommand(monkeypatch):
    called = []
    monkeypatch.setattr(OsUtil, "setup_swapfile", lambda size_gb, path_swapfile="/swapfile", logger=None: called.append((size_gb, path_swapfile)) or True)
    monkeypatch.setattr(socket, "gethostname", lambda: "mocked-auto-host")
    monkeypatch.setattr(os.path, "exists", lambda p: False if p in ("/dev/.cros_milestone", "/mnt/chromeos") else os.path.lexists(p))
    monkeypatch.setattr(OsUtil, "get_os_type", lambda logger=None: (OsUtil.TYPE_OS_LINUX, UbuntuOsSetup._OS_TYPE))
    assert CompInitSetup().run(args_list=["setup_swap", "--swap_size_gb", "8"]) is True
    assert called == [(8, DebianSetup.PATH_SWAPFILE)]


@pytest.mark.parametrize("subcommand", ["setup", "setup_swap"])
def test_suco_swap_size_gb_must_be_positive(subcommand, capsys):
    for bad in ("0", "-5", "abc"):
        with pytest.raises(SystemExit) as exc:
            CompInitSetup()._cli_args([subcommand, "--swap_size_gb", bad])
        assert exc.value.code == 2
        assert "--swap_size_gb" in capsys.readouterr().err
    assert CompInitSetup()._cli_args([subcommand, "--swap_size_gb", "8"]).swap_size_gb == 8
    assert CompInitSetup()._cli_args([subcommand]).swap_size_gb == DebianSetup.SIZE_SWAPFILE_GB_DEFAULT


def test_suco_setup_swap_stops_when_os_detection_fails(monkeypatch):
    called = []
    monkeypatch.setattr(OsUtil, "setup_swapfile", lambda *a, **kw: called.append(a) or True)
    monkeypatch.setattr(socket, "gethostname", lambda: "mocked-auto-host")
    def fail_get_os_type(logger=None):
        raise OSError("cannot read /etc/os-release")
    monkeypatch.setattr(OsUtil, "get_os_type", fail_get_os_type)
    with pytest.raises(OSError, match="cannot read /etc/os-release"):
        CompInitSetup().setup_swap(16, DebianSetup.PATH_SWAPFILE)
    assert called == []


def test_suco_run_os_detection_failure(monkeypatch):
    monkeypatch.setattr(socket, "gethostname", lambda: "mocked-auto-host")
    def fail_get_os_type(logger=None):
        raise OSError("cannot read /etc/os-release")
    monkeypatch.setattr(OsUtil, "get_os_type", fail_get_os_type)

    # No usable fallback: the original detection error surfaces, not a NotImplementedError for an empty distro.
    with pytest.raises(OSError, match="cannot read /etc/os-release"):
        CompInitSetup().run(args_list=["setup"])

    # A supported os_distro given by the user is enough to move on to building the setup.
    captured_builder = []
    def fake_run(self, host_cfg, conf_repo_remote="", conf_base_path=""):
        captured_builder.append(self)
    monkeypatch.setattr(MacOsSetup, "run", fake_run)
    assert CompInitSetup().run(args_list=["setup", "--os_distro", MacOsSetup._OS_TYPE]) is True
    assert isinstance(captured_builder[0], MacOsSetup)


@pytest.mark.parametrize("hostname,os_type,os_distro", [
    (CompInitSetupConfig.HOSTNAME_BRYA, OsUtil.TYPE_OS_LINUX, DebianSetup._OS_TYPE),            # ChromeOS Crostini
    (CompInitSetupConfig.HOSTNAME_IL80D4KK, OsUtil.TYPE_OS_LINUX, UbuntuOsSetup._OS_TYPE),     # WSL2
    ("mocked-mac-host", MacOsSetup._OS_TYPE, "None"),
])
def test_suco_setup_swap_skipped_on_unsupported_hosts(monkeypatch, hostname, os_type, os_distro):
    called = []
    monkeypatch.setattr(OsUtil, "setup_swapfile", lambda *a, **kw: called.append(a) or True)
    monkeypatch.setattr(socket, "gethostname", lambda: hostname)
    monkeypatch.setattr(OsUtil, "get_os_type", lambda logger=None: (os_type, os_distro))
    assert CompInitSetup().setup_swap(16, DebianSetup.PATH_SWAPFILE) is False
    assert called == []
