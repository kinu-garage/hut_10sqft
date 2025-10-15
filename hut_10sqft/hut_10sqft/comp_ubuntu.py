#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage

import argparse
import os
import shutil

from hut_10sqft.config_dispatch import ConfigDispatch
from hut_10sqft.comp_debian import DebianSetup
from hut_10sqft_lib.os_util import OsUtil


class UbuntuOsSetup (DebianSetup):
    _OS_TYPE = OsUtil.TYPE_LINUX_DISTRO_UBUNTU
    _UBUNTU_DEB_DEPS = [
        "gnome-screenshots",        
        "googleearth-package",
        "gtk-recordmydesktop",
        "ibus-el",
        "indicator-multiload",
        "peek",
        "python-software-properties",  # From http://askubuntu.com/a/55960/24203 primarilly for Oracle Java for Eclipse
        "ptex-bin",
        "sysinfo",        
    ]    
    _EXTERNAL_STORAGE_KUDU1 = "Evo840SSD"
    _PKGS_SNAP = ["docker", "yt-dlp"]  # TODO Needs a better way specify this list of pkgs.

    def __init__(self, os_name=_OS_TYPE, args_in: argparse.Namespace=None):
        super().__init__(os_name, args_in)
        self.ubuntu_desktop_cleanup()

    def install_deps_adhoc(self, deb_pkgs=[], pip_pkgs=[], allow_pip_break=False, snap_pkgs: list[str]=_PKGS_SNAP):
        if not deb_pkgs:
            deb_pkgs = self._DEBIAN_DEB_DEPS + self._UBUNTU_DEB_DEPS
        self._install_deps_adhoc_debian(deb_pkgs, pip_pkgs, allow_pip_break)

        # Take care of `snap` packages
        snap_pkgs_failed = []
        for snap_pkg in snap_pkgs:
            try:
                self.setup_snap_pkgs(snap_pkg)
            except RuntimeError as e:
                snap_pkgs_failed.append(snap_pkg)
        if snap_pkgs_failed:
            self.add_runtime_issue(f"The following `snap` pkgs failed to install: {snap_pkgs_failed}.")

    def ubuntu_desktop_cleanup(self):
        dirs_tobe_removed = ["Documents", "Music", "Pictures", "Public", "Templates", "Videos"]
        self._logger.warning("Deleting Ubuntu's default directories: {}".format(dirs_tobe_removed))
        for dir in dirs_tobe_removed:
            try:
                shutil.rmtree(dir)
            except FileNotFoundError as e:
                self._logger.warning("File/Dir '{}' does not exist. Moving on without deleting it.".format(dir))
                self.add_runtime_issue(e)

    def generate_symlinks(self, rootpath_symlinks, path_user_home):
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
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "pg", "myDevelopment", "git_repo"),
                path_dest=os.path.join(rootpath_symlinks, "git_repos"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "GoogleDrive", "Career"),
                path_dest=os.path.join(rootpath_symlinks, "Career"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "GoogleDrive", "Current"),
                path_dest=os.path.join(rootpath_symlinks, "Current"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "Career", "engineering", "ARIAC"),
                path_dest=os.path.join(rootpath_symlinks, "ARIAC"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "Career", "MOOC"),
                path_dest=os.path.join(rootpath_symlinks, "MOOC"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "Career", "academicDoc"),
                path_dest=os.path.join(rootpath_symlinks, "academicDoc"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "git_repos", "ROS", "cws_base"),
                path_dest=os.path.join(rootpath_symlinks, "ROS"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "30y-130s", "schools_children", "GJLS"),
                path_dest=os.path.join(rootpath_symlinks, "GJLS"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "git_repos", "ROS", "cws_utakata"),
                path_dest=os.path.join(rootpath_symlinks, "cws_utakata"),
                is_symlink=True),
            ConfigDispatch(
                path_source=(os.path.sep + os.path.join("media", self._os_user_id, self._EXTERNAL_STORAGE_KUDU1)),
                path_dest=os.path.join(rootpath_symlinks, self._EXTERNAL_STORAGE_KUDU1),
                necessary=False,
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "My Mac (tork-mac1)"),
                path_dest=os.path.join(rootpath_symlinks, "dbox_mac1"),
                is_symlink=True),
            ]
        return pairs_symlinks

    def set_ros_apt_source(self, 
                           path_aptsrc_file="/etc/apt/sources.list.d/ros2.list",
                           path_os_release = "/etc/os-release",
                           key_os_code = "VERSION_CODENAME="):
        _URL_ROS2_UBUNTU_INSTALL_DEP = "https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html"
        self._logger.warning(f"At some point after ROS2 Foxy, the apt source setting for ROS2 on Ubuntu has changed. Follow manually the instruction at {_URL_ROS2_UBUNTU_INSTALL_DEP}. "
                             f"If the ROS2 setup is not done, then the future steps that depend on ROS2 apt source setting might fail.")

    def _set_ros_apt_source(self, 
                           path_aptsrc_file="/etc/apt/sources.list.d/ros2.list",
                           path_os_release = "/etc/os-release",
                           key_os_code = "VERSION_CODENAME="):
        """
        @deprecated: This method uses `ros2.list` in apt source, which seems to be outdated in ROS2 newer than Foxy.
        @summary Create
        @param key_os_code: Likely must end with '=', at least so as of Ubuntu 22.04.
        @exception IOError: When an error happens while writing to 'path_aptsrc_file'
        """
        _URL_ROS2_UBUNTU_INSTALL_DEP = "https://docs.ros.org/en/foxy/Installation/Ubuntu-Install-Debians.html#install-ros-2-packages"
        _CMD_ROS2_UBUNTU_INSTALL_DEP = 'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null'
        _os_codename = ""
        # Get OS codename        
        with open(path_os_release, "r") as file_os_code:
            str_file = file_os_code.readlines()
            for line in str_file:
                self._logger.info(f"line= {line}")
                if line.startswith(key_os_code):
                    # E.g. From a string 'VERSION_CODENAME=jammy', the following line extracts and put 'jammy' in '_os_codename'.
                    _os_codename = line[line.index(key_os_code) + len(key_os_code):]
                    # Cleaning e.g. remove line feed at the end.
                    _os_codename = _os_codename.strip()
                    break
        if not _os_codename:
            raise RuntimeError(f"OS code name not found in the file '{path_os_release}'")
        res_oscode, err, retcode = OsUtil.subproc_bash("dpkg --print-architecture")

        try:
            with open(path_aptsrc_file, "w") as file_apt_src:
                file_apt_src.write(
                    f"deb [arch={res_oscode} signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu {_os_codename} main")
        except IOError as e:
            raise e
        except PermissionError as e:
            raise RuntimeError(f"Permission error while writing to '{path_aptsrc_file}'. "
                               f"If the file is NOT yet present there, make an empty file by `sudo touch {path_aptsrc_file}`, then"
                               f"follow the instruction at {_URL_ROS2_UBUNTU_INSTALL_DEP} (the distro is Focal, which is EoL but after that ROS seems to have switched the apt setting on Ubuntu, "
                               f"which needs to be reviewed first before adjusting to it). Error: {str(e)}")

    def setup_ros_installer_src(self):
        self.set_ros_apt_source()
        cmd_obtain_apt_key_rosdep = f"wget http://packages.ros.org/ros.key"
        cmd_set_apt_key_rosdep = f"apt-key add ros.key"
        OsUtil.subproc_bash(cmd_obtain_apt_key_rosdep)
        OsUtil.subproc_bash(cmd_set_apt_key_rosdep, does_sudo=True)
        self.apt_update()

    def setup_rosdep_and_run(self, path_ws, pkg_rosdep="python3-rosdep", init_rosdep=False):
        self.exec_rosdep_update(path_ws, pkg_rosdep, init_rosdep)

    def setup_snap_pkgs(self, snap_pkg: str):
        """
        @summary: Install specific `snap` packages that are not available via apt and other package managers.
        """
        cmd = f"snap install {snap_pkg}"
        output, error, bash_return_code = OsUtil.subproc_bash(cmd, does_sudo=True)
        if bash_return_code != 0:
            raise RuntimeError(f"Failed to install snap package '{snap_pkg}'.\n\tOutput: {output}\n\tError: {error}")
        self._logger.info(f"Successfully installed snap package '{snap_pkg}'.\n\tOutput: {output}\n\tError: {error}")
