#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage

import argparse
import os

from hut_10sqft_lib.os_util import OsUtil
from hut_10sqft.comp_debian import DebianSetup
from hut_10sqft.config_dispatch import ConfigDispatch
from hut_10sqft.suco_installer import CompInitSetupConfig

class ChromeOsSetup(DebianSetup):
    _DIRNAME_GDRIVE = "GoogleDrive"
    _DIRNAME_LOCAL_DIR = "MyFiles"
    _DIRNAME_LOCAL_DOWNLOADS = "Downloads"
    _HINT_ENABLE_MOUNT_GENERIC = "Likely any of '{}' path is not yet mounted on the Linux container. To mount,\n" \
        "1. Open 'File app' on the host ChromeOS.\n" \
        "2. on the left pane (list of directories) expand {}." \
        "3. On any top-level folder you'd like to mount on to your Linux container, right-click then choose 'Manage Linux Sharing' then the app should show a confirmation msg.\n" \
        "4. Verify on terminal on a Linux container that the directory is found by running 'ls -l /mnt/chromeos/{}'.\n"
    _HINT_ENABLE_MOUNT_GDRIVE = _HINT_ENABLE_MOUNT_GENERIC.format(_DIRNAME_GDRIVE, _DIRNAME_GDRIVE, _DIRNAME_GDRIVE)
    _HINT_ENABLE_MOUNT_LOCAL_DOWNLOADS = _HINT_ENABLE_MOUNT_GENERIC.format(_DIRNAME_LOCAL_DOWNLOADS, _DIRNAME_LOCAL_DOWNLOADS, os.path.join(_DIRNAME_LOCAL_DIR, _DIRNAME_LOCAL_DOWNLOADS))
    _OS_TYPE = OsUtil.TYPE_OS_CHROMEOS

    def __init__(self, os_name=_OS_TYPE, args_in: argparse.Namespace=None, default_userid=CompInitSetupConfig.VAL_USERID_GOOG):
        super().__init__(os_name, args_in, default_userid=default_userid)

    def setup_dropbox(self):
        self._logger.warning(
            f"Skipping Dropbox setup on {self._OS_TYPE}, as it runs on the Chrome OS host without allowing to mount the directory onto Linux mode.")

    def generate_symlinks(self, rootpath_symlinks: str, path_user_home=""):
        """
        @param rootpath_symlinks: Path to the directory that is designed to host the list of symlinks e.g. '~/link'.
        """
        pairs_symlinks = [
            ConfigDispatch(
                path_source=os.path.join(os.path.sep, "mnt" ,"chromeos", self._DIRNAME_GDRIVE, "MyDrive"),
                path_dest=os.path.join(rootpath_symlinks, self._DIRNAME_GDRIVE), is_symlink=True, necessary=True, hint_enable=self._HINT_ENABLE_MOUNT_GDRIVE),
            ConfigDispatch(
                path_source=os.path.join(rootpath_symlinks, self._DIRNAME_GDRIVE, "30y-130s"),
                path_dest=os.path.join(rootpath_symlinks, "30y-130s"), is_symlink=True, necessary=True, hint_enable=self._HINT_ENABLE_MOUNT_GDRIVE),
            ConfigDispatch(
                path_source=os.path.join(rootpath_symlinks, self._DIRNAME_GDRIVE, "Current"),
                path_dest=os.path.join(rootpath_symlinks, "Current"), is_symlink=True, necessary=True, hint_enable=self._HINT_ENABLE_MOUNT_GDRIVE),
            ConfigDispatch(
                path_source=os.path.join(rootpath_symlinks, self._DIRNAME_GDRIVE, "Career", "academicDoc"),
                path_dest=os.path.join(rootpath_symlinks, "academicDoc"), is_symlink=True, necessary=True, hint_enable=self._HINT_ENABLE_MOUNT_GDRIVE),
            ConfigDispatch(
                path_source=os.path.join(rootpath_symlinks, self._DIRNAME_GDRIVE, "Career", "MOOC"),
                path_dest=os.path.join(rootpath_symlinks, "MOOC"), is_symlink=True, necessary=True, hint_enable=self._HINT_ENABLE_MOUNT_GDRIVE),
            ConfigDispatch(
                path_source=os.path.join(os.path.sep, "mnt" ,"chromeos", self._DIRNAME_LOCAL_DIR, self._DIRNAME_LOCAL_DOWNLOADS),
                path_dest=os.path.join(rootpath_symlinks, "chrome-host_downloads"), is_symlink=True, necessary=True, hint_enable=self._HINT_ENABLE_MOUNT_LOCAL_DOWNLOADS),
            ]
        self._logger.debug(f"pairs_symlinks: type: {type(pairs_symlinks)}, content: {pairs_symlinks}")
        return pairs_symlinks
