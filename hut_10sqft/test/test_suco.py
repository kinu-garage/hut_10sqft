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
import logging
import os
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
        assert len(pairs) == 13
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
