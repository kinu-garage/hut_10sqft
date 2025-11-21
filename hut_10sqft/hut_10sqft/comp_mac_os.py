#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage

import argparse
import os

from hut_10sqft.host_config import HostConf
from hut_10sqft.config_dispatch import ConfigDispatch
from hut_10sqft.abst_comp_setup import AbstCompSetupFactory
from hut_10sqft_lib.os_util import OsUtil
from hut_10sqft.suco_installer import CompInitSetupConfig


class MacOsSetup(AbstCompSetupFactory):
    _OS_TYPE = OsUtil.TYPE_OS_MACOS
    def __init__(self, os_name=_OS_TYPE, args_in: argparse.Namespace=None, default_userid=CompInitSetupConfig.VAL_USERID_DEFAULT):
        super().__init__(os_name, args_in, default_userid=default_userid)

    def install_deps_adhoc(self, deb_pkgs=[], pip_pkgs=[], allow_pip_break=False, snap_pkgs: list[str]=[]):
        raise RuntimeWarning("TBD On MacOS maybe set up brew first, then install the dependencies via brew, pip, etc.")

    def generate_symlinks(self, rootpath_symlinks: str, path_user_home=""):
        pairs_symlinks = [
            ConfigDispatch(  # Many symlinks depend on this symlink.
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "GoogleDrive"),
                path_dest=os.path.join(rootpath_symlinks, "GoogleDrive"),
                is_symlink=True),
            ConfigDispatch(  # Some others depend on this symlink.
                path_source=os.path.join(path_user_home, "link", "GoogleDrive", "30y-130s"),
                path_dest=os.path.join(rootpath_symlinks, "30y-130s"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "GoogleDrive", "Current"),
                path_dest=os.path.join(rootpath_symlinks, "Current"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "GoogleDrive", "Career", "MOOC"),
                path_dest=os.path.join(rootpath_symlinks, "MOOC"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "Career", "academicDoc"),
                path_dest=os.path.join(rootpath_symlinks, "academicDoc"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "30y-130s", "schools_children", "GJLS"),
                path_dest=os.path.join(rootpath_symlinks, "GJLS"),
                is_symlink=True),
            ]
        return pairs_symlinks

    def setup_ssh(self, skip=False, path_local_conf_repo=""):
        _MSG_INSTRUCTION_ENABLE_SSH_SERVER = "On terminal run 'sudo systemsetup -setremotelogin on'. \
            If you get an error that looks like:\n \
            'Turning Remote Login on or off requires Full Disk Access privileges'\n\n \
           then go to Settings > Security & Privacy > Privacy > Full Disk Access; \
           then select Applications > Utilities > Terminal from the file picker². Then execute the command again, \
           it should be in the history so you might just need to press arrow upwards."

        raise RuntimeWarning(f"Enabling SSH server on MacOS might have to be done manually. See https://superuser.com/a/1764825/106974, \
                             or the text copied from there below:\n{_MSG_INSTRUCTION_ENABLE_SSH_SERVER}")

    def setup_vscode(self, path_installer: str):
        raise RuntimeWarning("Skipping as no plan to use this host for the development.")
