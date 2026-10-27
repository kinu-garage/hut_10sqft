#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage

import argparse
import os
import shlex
import shutil

from hut_10sqft.abst_comp_setup import ShellCapableOsSetup
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
        path_user_home = getattr(self, "_user_home_dir", os.path.expanduser("~"))
        for dir in dirs_tobe_removed:
            try:
                shutil.rmtree(os.path.join(path_user_home, dir))
            except (FileNotFoundError, PermissionError, OSError) as e:
                self._logger.warning("File/Dir '{}' could not be deleted ({}). Moving on.".format(dir, e))
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

    def is_host_p16s(self, host_config: HostConf = None) -> bool:
        """
        @summary: Check if the target host is p16s.
        """
        hostname = ""
        if host_config and host_config.hostname:
            hostname = host_config.hostname
        elif getattr(self, "_args_in", None) and getattr(self._args_in, "hostname", None):
            hostname = self._args_in.hostname
        return hostname == CompInitSetupConfig.HOSTNAME_P16S or hostname.startswith("130s-p16s")

    def setup_egpu(
            self,
            path_xorg_conf: str = "",
            path_modprobe_conf: str = "",
            path_prime_run: str = "",
            path_udev_rules: str = "",
            path_gdm_conf: str = "",
            path_nvidia_sleep_custom: str = "",
            path_suspend_override: str = "",
            path_resume_override: str = "",
            path_hibernate_override: str = "",
            path_apt_hook: str = "",
            path_nvidia_sleep_sh: str = "/usr/bin/nvidia-sleep.sh"):
        """
        @summary: Set up eGPU configurations by installing Xorg, modprobe, udev, GDM,
          prime-run, systemd sleep overrides, and apt hook configurations to system folders,
          disabling chvt in nvidia-sleep.sh, updating initramfs, reloading udev rules,
          and reloading systemd daemon.
        @param path_xorg_conf: Path to 10-nvidia.conf for Xorg (/etc/X11/xorg.conf.d/10-nvidia.conf).
        @param path_modprobe_conf: Path to nvidia-runtimepm.conf (/etc/modprobe.d/nvidia-runtimepm.conf).
        @param path_prime_run: Path to prime-run launcher script (/usr/local/bin/prime-run).
        @param path_udev_rules: Path to udev rule (/etc/udev/rules.d/99-disable-internal-gpu.rules).
        @param path_gdm_conf: Path to custom.conf for GDM (/etc/gdm3/custom.conf).
        @param path_nvidia_sleep_custom: Path to custom sleep script (/usr/local/bin/nvidia-sleep-custom.sh).
        @param path_suspend_override: Path to systemd suspend override (/etc/systemd/system/nvidia-suspend.service.d/override.conf).
        @param path_resume_override: Path to systemd resume override (/etc/systemd/system/nvidia-resume.service.d/override.conf).
        @param path_hibernate_override: Path to systemd hibernate override (/etc/systemd/system/nvidia-hibernate.service.d/override.conf).
        @param path_apt_hook: Path to apt hook (/etc/apt/apt.conf.d/99-nvidia-sleep-no-chvt).
        @param path_nvidia_sleep_sh: Path to nvidia-sleep.sh script to patch (/usr/bin/nvidia-sleep.sh).
        @see: https://github.com/kinu-garage/hut_10sqft/issues/1120
        @see: https://github.com/kinu-garage/hut_10sqft/issues/1317
        """
        configs = [
            (path_xorg_conf, "/etc/X11/xorg.conf.d/10-nvidia.conf", "644"),
            (path_modprobe_conf, "/etc/modprobe.d/nvidia-runtimepm.conf", "644"),
            (path_prime_run, "/usr/local/bin/prime-run", "755"),
            (path_udev_rules, "/etc/udev/rules.d/99-disable-internal-gpu.rules", "644"),
            (path_gdm_conf, "/etc/gdm3/custom.conf", "644"),
            (path_apt_hook, "/etc/apt/apt.conf.d/99-nvidia-sleep-no-chvt", "644"),
        ]

        sleep_overrides = [
            (path_suspend_override, "/etc/systemd/system/nvidia-suspend.service.d/override.conf", "644"),
            (path_resume_override, "/etc/systemd/system/nvidia-resume.service.d/override.conf", "644"),
            (path_hibernate_override, "/etc/systemd/system/nvidia-hibernate.service.d/override.conf", "644"),
        ]

        # Overrides invoke nvidia-sleep-custom.sh; require the script source to exist before installing any override.
        if any(bool(src) for src, _, _ in sleep_overrides):
            if not path_nvidia_sleep_custom or not os.path.exists(path_nvidia_sleep_custom):
                msg = (
                    f"Sleep-file set is incomplete: custom sleep script source '{path_nvidia_sleep_custom}' "
                    "not found. Skipping installation of sleep script and systemd overrides."
                )
                self._logger.warning(msg)
                self.add_runtime_issue(RuntimeError(msg))
            else:
                configs.append((path_nvidia_sleep_custom, "/usr/local/bin/nvidia-sleep-custom.sh", "755"))
                configs.extend(sleep_overrides)
        elif path_nvidia_sleep_custom:
            configs.append((path_nvidia_sleep_custom, "/usr/local/bin/nvidia-sleep-custom.sh", "755"))

        for src, dest, mode in configs:
            if not src:
                continue
            try:
                if os.path.exists(src):
                    self._install_system_file(src, dest, mode=mode)
                else:
                    self._logger.warning(f"Config source file not found: '{src}'")
            except Exception as e:
                self._logger.warning(f"Failed to install '{src}' to '{dest}': {str(e)}")
                self.add_runtime_issue(e)

        try:
            self._patch_nvidia_sleep_script(path_nvidia_sleep_sh)
        except Exception as e:
            self._logger.warning(f"Patching nvidia-sleep.sh failed: {str(e)}")
            self.add_runtime_issue(e)

        try:
            self._update_initramfs()
        except Exception as e:
            self._logger.warning(f"Updating initramfs failed: {str(e)}")
            self.add_runtime_issue(e)

        try:
            self._reload_udev_rules()
        except Exception as e:
            self._logger.warning(f"Reloading udev rules failed: {str(e)}")
            self.add_runtime_issue(e)

        try:
            self._systemctl_daemon_reload()
        except Exception as e:
            self._logger.warning(f"Reloading systemd daemon failed: {str(e)}")
            self.add_runtime_issue(e)

    def _patch_nvidia_sleep_script(self, path_target: str = "/usr/bin/nvidia-sleep.sh"):
        """
        @summary: Disable chvt calls in nvidia-sleep.sh that cause Xorg EnterVT crashes on eGPU resume.
        @param path_target: Path to nvidia-sleep.sh script to patch.
        @see: https://github.com/kinu-garage/hut_10sqft/issues/1317
        """
        if not path_target or not os.path.exists(path_target):
            return
        quoted_target = shlex.quote(path_target)
        cmd = (
            f"if grep -q '^[[:space:]]*chvt' {quoted_target}; then "
            f"sed -i -E 's/^([[:space:]]*)(chvt[[:space:]]+.*)$/\\1# \\2 # disabled for eGPU by hut_10sqft/' {quoted_target}; "
            f"fi"
        )
        self._logger.info(f"Patching chvt calls in '{path_target}': '{cmd}'")
        output, error, return_code = OsUtil.subproc_bash(cmd, does_sudo=True, logger=self._logger)
        if return_code != 0:
            raise RuntimeError(f"Failed to patch '{path_target}'.\n\tOutput: {output}\n\tError: {error}")

    def setup_wake_monitors_service(self, path_service_src: str = ""):
        """
        @summary: Set up and enable the wake-all-monitors systemd user service on p16s.
        @param path_service_src: Path to wake-all-monitors.service source file.
        """
        if not path_service_src:
            return
        if not os.path.exists(path_service_src):
            self._logger.warning(f"Wake monitors service file not found: '{path_service_src}'")
            return

        path_user_home = getattr(self, "_user_home_dir", os.path.expanduser("~"))
        path_systemd_user_dir = os.path.join(path_user_home, ".config", "systemd", "user")
        os.makedirs(path_systemd_user_dir, exist_ok=True)
        path_service_dest = os.path.join(path_systemd_user_dir, "wake-all-monitors.service")

        conf_service = ConfigDispatch(
            path_source=path_service_src,
            path_dest=path_service_dest,
            is_symlink=True)
        self.setup_file(conf_service, overwrite=True)

        cmd_enable = "systemctl --user daemon-reload && systemctl --user enable --now wake-all-monitors.service"
        output, error, retcode = OsUtil.subproc_bash(cmd_enable, does_sudo=False, logger=self._logger)
        if retcode != 0:
            msg = f"Failed to enable wake-all-monitors.service.\n\tOutput: {output}\n\tError: {error}"
            self._logger.warning(msg)
            self.add_runtime_issue(RuntimeError(msg))

    def setup_dropbox_swap_watchdog(self, path_service_src: str = "", path_timer_src: str = ""):
        """
        @summary: Set up and enable the dropbox-swap-watchdog systemd user service and timer.
        @param path_service_src: Path to dropbox-swap-watchdog.service source file.
        @param path_timer_src: Path to dropbox-swap-watchdog.timer source file.
        """
        if not path_service_src or not path_timer_src:
            return
        if not os.path.exists(path_service_src):
            self._logger.warning(f"Dropbox swap watchdog service file not found: '{path_service_src}'")
            return
        if not os.path.exists(path_timer_src):
            self._logger.warning(f"Dropbox swap watchdog timer file not found: '{path_timer_src}'")
            return

        path_user_home = getattr(self, "_user_home_dir", os.path.expanduser("~"))
        path_systemd_user_dir = os.path.join(path_user_home, ".config", "systemd", "user")
        os.makedirs(path_systemd_user_dir, exist_ok=True)

        for src, unit_name in [
            (path_service_src, "dropbox-swap-watchdog.service"),
            (path_timer_src, "dropbox-swap-watchdog.timer"),
        ]:
            conf_unit = ConfigDispatch(
                path_source=src,
                path_dest=os.path.join(path_systemd_user_dir, unit_name),
                is_symlink=True)
            self.setup_file(conf_unit, overwrite=True)

        cmd_enable = "systemctl --user daemon-reload && systemctl --user enable --now dropbox-swap-watchdog.timer"
        output, error, retcode = OsUtil.subproc_bash(cmd_enable, does_sudo=False, logger=self._logger)
        if retcode != 0:
            msg = f"Failed to enable dropbox-swap-watchdog.timer.\n\tOutput: {output}\n\tError: {error}"
            self._logger.warning(msg)
            self.add_runtime_issue(RuntimeError(msg))

    def setup_configs(
            self,
            host_config: HostConf,
            abs_path_confdir: str=ShellCapableOsSetup._PATH_DEFAULT_CONFIG_CONFDIR,
            abs_path_private_confdir: str=ShellCapableOsSetup._PATH_DEFAULT_PERMANENT_CONF_REPO):
        super().setup_configs(host_config, abs_path_confdir=abs_path_confdir, abs_path_private_confdir=abs_path_private_confdir)
        if not getattr(self._args_in, "skip_dropbox", False):
            path_dropbox_service = os.path.join(abs_path_confdir, "systemd", "user", "dropbox-swap-watchdog.service")
            if not os.path.exists(path_dropbox_service):
                path_dropbox_service_sub = os.path.join(
                    abs_path_confdir, "hut_10sqft", "config", "systemd", "user", "dropbox-swap-watchdog.service")
                if os.path.exists(path_dropbox_service_sub):
                    path_dropbox_service = path_dropbox_service_sub

            path_dropbox_timer = os.path.join(abs_path_confdir, "systemd", "user", "dropbox-swap-watchdog.timer")
            if not os.path.exists(path_dropbox_timer):
                path_dropbox_timer_sub = os.path.join(
                    abs_path_confdir, "hut_10sqft", "config", "systemd", "user", "dropbox-swap-watchdog.timer")
                if os.path.exists(path_dropbox_timer_sub):
                    path_dropbox_timer = path_dropbox_timer_sub

            self.setup_dropbox_swap_watchdog(
                path_service_src=path_dropbox_service,
                path_timer_src=path_dropbox_timer)

        if self.is_host_p16s(host_config):
            dir_struct = os.path.join(abs_path_confdir, "dir_struct")
            if not os.path.exists(dir_struct):
                dir_struct_sub = os.path.join(abs_path_confdir, "hut_10sqft", "config", "dir_struct")
                if os.path.exists(dir_struct_sub):
                    dir_struct = dir_struct_sub

            path_xorg_conf = os.path.join(dir_struct, "etc", "X11", "xorg.conf.d", "10-nvidia.conf")
            path_modprobe_conf = os.path.join(dir_struct, "etc", "modprobe.d", "nvidia-runtimepm.conf")
            path_prime_run = os.path.join(dir_struct, "usr", "local", "bin", "prime-run")
            path_udev_rules = os.path.join(dir_struct, "etc", "udev", "rules.d", "99-disable-internal-gpu.rules")
            path_gdm_conf = os.path.join(dir_struct, "etc", "gdm3", "custom.conf")
            path_nvidia_sleep_custom = os.path.join(dir_struct, "usr", "local", "bin", "nvidia-sleep-custom.sh")
            path_suspend_override = os.path.join(dir_struct, "etc", "systemd", "system", "nvidia-suspend.service.d", "override.conf")
            path_resume_override = os.path.join(dir_struct, "etc", "systemd", "system", "nvidia-resume.service.d", "override.conf")
            path_hibernate_override = os.path.join(dir_struct, "etc", "systemd", "system", "nvidia-hibernate.service.d", "override.conf")
            path_apt_hook = os.path.join(dir_struct, "etc", "apt", "apt.conf.d", "99-nvidia-sleep-no-chvt")

            self.setup_egpu(
                path_xorg_conf=path_xorg_conf,
                path_modprobe_conf=path_modprobe_conf,
                path_prime_run=path_prime_run,
                path_udev_rules=path_udev_rules,
                path_gdm_conf=path_gdm_conf,
                path_nvidia_sleep_custom=path_nvidia_sleep_custom,
                path_suspend_override=path_suspend_override,
                path_resume_override=path_resume_override,
                path_hibernate_override=path_hibernate_override,
                path_apt_hook=path_apt_hook)

            path_wake_service = os.path.join(abs_path_confdir, "systemd", "user", "wake-all-monitors.service")
            if not os.path.exists(path_wake_service):
                path_wake_service_sub = os.path.join(
                    abs_path_confdir, "hut_10sqft", "config", "systemd", "user", "wake-all-monitors.service")
                if os.path.exists(path_wake_service_sub):
                    path_wake_service = path_wake_service_sub

            self.setup_wake_monitors_service(path_service_src=path_wake_service)

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
