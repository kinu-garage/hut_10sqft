#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage

import argparse
import os
import shutil

from hut_10sqft.config_dispatch import ConfigDispatch
from hut_10sqft.comp_debian import DebianSetup
from hut_10sqft.host_config import HostConf
from hut_10sqft_lib.os_util import OsUtil
from hut_10sqft.suco_installer import CompInitSetupConfig


class UbuntuOsSetup (DebianSetup):
    _OS_TYPE = OsUtil.TYPE_LINUX_DISTRO_UBUNTU
    _UBUNTU_DEB_DEPS = [
        "gnome-screenshots",        
        "googleearth-package",
        "gtk-recordmydesktop",
        "ibus-el",
        "indicator-multiload",
        "lvm2",  # For handling external SATA SSD with LVM
        "peek",
        "python-software-properties",  # From http://askubuntu.com/a/55960/24203 primarilly for Oracle Java for Eclipse
        "ptex-bin",
        "sysinfo",        
    ]    
    _EXTERNAL_STORAGE_KUDU1 = "Evo840SSD"
    _PKGS_SNAP = ["docker", "yt-dlp"]  # TODO Needs a better way specify this list of pkgs.

    def __init__(self, os_name=_OS_TYPE, args_in: argparse.Namespace=None, default_userid=CompInitSetupConfig.VAL_USERID_DEFAULT):
        super().__init__(os_name, args_in, default_userid=default_userid)

        self._path_mountpoint = ""
        # TODO This is not very nice design. Set up external SATA SSD first,
        # as in __init__ the path to the mount point will be used to create a symlink to it.
        try:
            self._path_mountpoint = self._setup_sata_ssd()
        except RuntimeError as e:
            self.add_runtime_issue(e)

        self.ubuntu_desktop_cleanup()

        try:
            self._setup_unreal_engine(self._path_mountpoint)
        except RuntimeError as e:
            self.add_runtime_issue(e)

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
                shutil.rmtree(os.path.join(os.path.expanduser('~'), dir))
            except FileNotFoundError as e:
                self._logger.warning("File/Dir '{}' does not exist. Moving on without deleting it.".format(dir))
                self.add_runtime_issue(e)

    def _setup_sata_ssd(self) -> str:
        """
        @see: https://github.com/kinu-garage/hut_10sqft/issues/871, https://github.com/kinu-garage/hut_10sqft/issues/1341
        @summary: Install a necessary package to handle logical volume (, which presumably taking care of mounting too),
          make the mounted directory accessible.
        @note: As of 2025/11, the usecase of this method is specific to the particular device
          named as `self._EXTERNAL_STORAGE_KUDU1` and also mentioned in
          https://github.com/kinu-garage/hut_10sqft/issues/1341. Also, this method needs to be executed
          priot to the main `run` method where an attempt to symlink the directory on the SSD will be made.
        @return: The path to the mount point of the SSD.
        @raise: RuntimeError: When the mount point does not exist even after installing `lvm2` package.
        """
        path_mountpoint = os.path.sep + os.path.join("media", self._args_in.user_id, self._EXTERNAL_STORAGE_KUDU1)
        if not os.path.exists(path_mountpoint):
            raise RuntimeError(f"Mount point '{path_mountpoint}' does not exist even after installing 'lvm2' package.")

        cmd_chown = f"chown -R {self._args_in.user_id}:{self._args_in.user_id} {path_mountpoint}"
        self._logger.warning(f"About to execute: '{cmd_chown}', which makes the mount point accessible \
                             by the user '{self._args_in.user_id}'. This may take a while depending on the number of files.")
        OsUtil.subproc_bash(cmd_chown, does_sudo=True, logger=self._logger)
        cmd_chmod_mountpoint = f"chmod 744 {path_mountpoint}"
        OsUtil.subproc_bash(cmd_chmod_mountpoint, does_sudo=True, logger=self._logger)
       
        return path_mountpoint
        
    def _setup_unreal_engine(self, path_rootdir_ue_storage: str):
        """
        @summary: Make sure the external SSD (named as `self._EXTERNAL_STORAGE_KUDU1` as of 2025/11) is accessible,
          create a symlink to the Unreal Engine executable to /usr/local/bin IFF an executable is found there,
          so that Unreal Engine can be used from there.
        @param path_rootdir_ue_storage: Path to the root directory of the external SSD where UE binary is stored.
        @raise RuntimeError: When a path at `path_rootdir_ue_storage` does not exist.
        """
        if not os.path.exists(path_rootdir_ue_storage):
            raise RuntimeError(f"Mount point for UE binary '{path_rootdir_ue_storage}' does not exist.")

        path_uexe_src = os.path.sep + os.path.join(path_rootdir_ue_storage,
                                                   "pg",
                                                   "unreal-engine",
                                                   "prebuilt_UE",
                                                   "unreal-engine-5.6.1_prebuilt",
                                                   "Engine", "Binaries", "Linux", "UnrealEditor")
        path_uexe_dest = os.path.sep + os.path.join("usr", "local", "bin", "UnrealEditor")
        if os.path.exists(path_uexe_src):
            cmd_ln_uexe = f"ln -sf {path_uexe_src} {path_uexe_dest}"
            OsUtil.subproc_bash(cmd_ln_uexe, does_sudo=True, logger=self._logger)
            self._logger.info(f"Created a symlink to Unreal Engine executable at '{path_uexe_dest}'")
        else:
            raise RuntimeError(f"Unreal Engine executable not found at '{path_uexe_src}'. "
                               f"Make sure the external SSD '{self._EXTERNAL_STORAGE_KUDU1}' is mounted properly.")

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
                path_source=os.path.join(rootpath_symlinks, "30y-130s", "schools_children", "in-japan-school"),
                path_dest=os.path.join(rootpath_symlinks, "japan-schools"), is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, "link", "git_repos", "ROS", "cws_utakata"),
                path_dest=os.path.join(rootpath_symlinks, "cws_utakata"),
                is_symlink=True),
            ConfigDispatch(
                path_source=(os.path.sep + os.path.join("media", self._args_in.user_id, self._EXTERNAL_STORAGE_KUDU1)),
                path_dest=os.path.join(rootpath_symlinks, self._EXTERNAL_STORAGE_KUDU1),
                necessary=False,
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "My Mac (tork-mac1)"),
                path_dest=os.path.join(rootpath_symlinks, "dbox_mac1"),
                is_symlink=True),
            ]
        return pairs_symlinks

    def setup_configs(self, host_config: HostConf, abs_path_confdir: str):
        pairs_conf_bash = [
            ConfigDispatch(
                path_source=os.path.join(abs_path_confdir, "bash", host_config.bash_cfg),
                path_dest=os.path.join(self._user_home_dir, ".bashrc"),
                is_symlink=True),
            ]
        for c in pairs_conf_bash:
            self.setup_file(c, overwrite=True)

        # TODO ssh config, path of which needs to be private.

        pairs_conf_tools = [
            ConfigDispatch(
                path_source=os.path.join(abs_path_confdir, "tmux_default.conf"),
                path_dest=os.path.join(self._user_home_dir, ".tmux.conf"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(abs_path_confdir, "emacs", host_config.emacs_cfg),
                path_dest=os.path.join(self._user_home_dir, ".emacs"),
                is_symlink=True),
            ]
        for c in pairs_conf_tools:
            self.setup_file(c)

    def set_ros_apt_source(self, 
                           path_aptsrc_file="/etc/apt/sources.list.d/ros2.list",
                           path_os_release = "/etc/os-release",
                           key_os_code = "VERSION_CODENAME="):
        """
        @summary: Set up apt source for ROS2 on Ubuntu.
        """
        _URL_DEB_APT_SRC = "https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest"
        _URL_ROS_APT_SRC = "https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest"
        _path_deb = "/tmp/ros2-apt-source.deb"

        # Execute the following bash command set, which is documented in https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html#setup-sources:
 
        OsUtil.apt_install("curl", self._logger)
        _cmd_get_ros_apt_src = f"curl -s {_URL_ROS_APT_SRC}"
        _output_string, error, bash_return_code = OsUtil.subproc_bash(
            _cmd_get_ros_apt_src, does_sudo=False, print_stdout_err=False, logger=self._logger)

        _ros_apt_src_version = None
        for line in _output_string.splitlines():
            if "tag_name" in line:
                _data_string = line
                # Split the string by the colon. The second part will be e.g. "1.1.0"
                _value_with_quotes = _data_string.split(":", 1)[1]
                # Strip the leading/trailing whitespace and quotes
                _ros_apt_src_version = _value_with_quotes.strip().strip('",')
                break

        if not _ros_apt_src_version:
            raise RuntimeError(f"Could not determine ROS apt source version from API response:\n{_output_string}")

        self._logger.info(f"Latest ROS apt source version: '{_ros_apt_src_version}'")

        # $(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})
        _env_vars_os_release = OsUtil.read_conf(path="/etc/os-release")
        _ubu_codename = _env_vars_os_release.get("UBUNTU_CODENAME", "")
        _ver_codename = _env_vars_os_release.get("VERSION_CODENAME", "")
        _os_ver_dist_str = _ubu_codename or _ver_codename

        _URL_DEB_ROS_APT = f"https://github.com/ros-infrastructure/ros-apt-source/releases/download/{_ros_apt_src_version}/ros2-apt-source_{_ros_apt_src_version}.{_os_ver_dist_str}_all.deb"
        self._logger.info(f"'{_URL_DEB_ROS_APT=}', '{_ubu_codename=}', '{_ver_codename=}'")

        _cmd_download_ros_apt_src_pkg = f"curl -L -o {_path_deb} {_URL_DEB_ROS_APT}"
        OsUtil.subproc_bash(_cmd_download_ros_apt_src_pkg, does_sudo=False, print_stdout_err=False, logger=self._logger)
        cmd_install_ros_apt_src_pkg = f"dpkg -i {_path_deb}"
        OsUtil.subproc_bash(cmd_install_ros_apt_src_pkg, does_sudo=True, print_stdout_err=True, logger=self._logger)

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
        # Execute 'apt-source_ros2.sh', which is supposed to function only on Ubuntu, is supposed to be globally installed within hut_10sqft package.
        OsUtil.subproc_bash("apt-source_ros2.sh", does_sudo=False, logger=self._logger)
        OsUtil.subproc_bash(f"apt update", does_sudo=True)
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
