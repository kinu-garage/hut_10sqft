#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage

import argparse
import os
import subprocess

from hut_10sqft.host_config import HostConf
from hut_10sqft.config_dispatch import ConfigDispatch
from hut_10sqft.abst_comp_setup import ShellCapableOsSetup
from hut_10sqft_lib.os_util import OsUtil
from hut_10sqft.suco_installer import CompInitSetupConfig

class DebianSetup(ShellCapableOsSetup):
    _APTPKG_ROSDEP2 = "python3-rosdep2"
    _DEB_CAPS_CTRL_UTIL = "gnome-tweaks"
    _DEBS_MOZC = ["emacs-mozc", "emacs-mozc-bin", "ibus-mozc", "mozc-utils-gui", "mozc-server"]
    #_DEBS_VIRTUALBOX = ["virtualbox-guest-additions-iso", "virtualbox-qt"]
    _DEBS_VIRTUALBOX = []  # Keep this blank before https://github.com/kinu-garage/hut_10sqft/issues/1401

    _DEBIAN_DEB_DEPS = [
                "aptitude",
                "colorized-logs",
                "dconf-editor",
                "evince",
                "flameshot",
                _DEB_CAPS_CTRL_UTIL,  # Primarily for swapping Caps and Ctrl keys
                "gitk",
                "ibus",
                "kazam",              # https://github.com/kinu-garage/hut_10sqft/issues/1006 etc.
                "libavahi-compat-libdnssd1",
                "libreoffice-draw",   # https://github.com/kinu-garage/hut_10sqft/issues/1357
                "locate",
                "lvm2",               # https://github.com/kinu-garage/hut_10sqft/issues/1341
                "mpv",                # https://github.com/kinu-garage/hut_10sqft/issues/1261
                "pdftk-java",
                "psensor",
                #"python3-rosdep",  # Without ROS' apt source, apt would install python3-rosdep2, which is NOT the officially maintained pkg. See https://discourse.ros.org/t/upstream-packages-increasingly-becoming-a-problem/10902/25
                "ptex-base",
                "smartmontools",      # https://github.com/kinu-garage/hut_10sqft/issues/871#issuecomment-2616691942, https://github.com/kinu-garage/hut_10sqft/issues/1135#issuecomment-2898229006, https://github.com/kinu-garage/hut_10sqft/issues/1341#issuecomment-3559791999
                "synaptic",
                "xbindkeys",
                "xsel",     # https://github.com/kinu-garage/hut_10sqft/issues/1077
                "vulkan-tools",       #https://github.com/kinu-garage/hut_10sqft/issues/1317#issuecomment-3531300663
                "whois",
                ] + _DEBS_MOZC + _DEBS_VIRTUALBOX
    _OS_TYPE = OsUtil.TYPE_LINUX_DISTRO_DEBIAN
    _PIP_PKGS = ["pipx"]

    def __init__(self, os_name=_OS_TYPE, args_in: argparse.Namespace=None, default_userid=CompInitSetupConfig.VAL_USERID_DEFAULT):
        # This variable might be accessed in `super().__init__` so
        # defined prior to the call. Might not be a good practice though.
        self._apt_updated = False

        super().__init__(os_name, args_in, default_userid=default_userid)

    @property
    def apt_updated(self):
        return self._apt_updated

    @apt_updated.setter
    def apt_updated(self, value):
        self._apt_updated = value

    def setup_vscode(self, path_installer: str) -> str:
        """
        @return: Path to the 'code' executable, None if installation was unsuccessful.
        @see https://code.visualstudio.com/blogs/2020/12/03/chromebook-get-started
        @raise ReferenceError: if setting up failed.
        """
        if not path_installer:
            raise ValueError(f"'path_installer' is empty.")

        self.install_deps_adhoc("gnome-keyring")
        cmd_install = f"dpkg -i {path_installer}"
        OsUtil.subproc_bash(cmd_install, does_sudo=True)

        # Returning the verification result
        return OsUtil.which("code")

    def setup_terminal_configs(self, abspath_local_perm_conf: str):
        _CONFFILE_NAME_SHORTCUT = "terminal_shortcuts.dconf"
        _abspath_conf_dir = os.path.join(abspath_local_perm_conf, "dconf")
        _conf_abspath = os.path.join(_abspath_conf_dir, _CONFFILE_NAME_SHORTCUT)
        _cmd = f"dconf load /org/gnome/terminal/ < {_conf_abspath}"
        OsUtil.subproc_bash(_cmd, does_sudo=False, print_stdout_err=True, logger=self._logger)

        _MSG_NOTE_TERMINAL_CONF_VISUAL_NOT_DONE = (f"""Configs of the visual of the Terminal needs to be done manually """
                                                   """ either using (recommended) Terminal's GUI on 'Preference' or using `dconf` and the premade config files,"""
                                                   f""" which you can find in '{_abspath_conf_dir}'. See https://github.com/kinu-garage/hut_10sqft/issues/174#issuecomment-3003542573""")
        self._logger.warning(_MSG_NOTE_TERMINAL_CONF_VISUAL_NOT_DONE)
        self.add_runtime_issue(_MSG_NOTE_TERMINAL_CONF_VISUAL_NOT_DONE)

    def setup_ros_installer_src(self):
        self._logger.warning(f"On '{self._OS_TYPE}' no prebuilt ROS installer pkgs are available so skipping.")

    def exec_rosdep_update(self, path_ws, pkg_rosdep=_APTPKG_ROSDEP2, init_rosdep=False):
        """
        @summary: As of 202505 this method is only targetting Debian/Ubuntu OSes.
        @param init_rosdep: If `True`, then `rosdep init` also executes.
        """
        self.setup_ros_installer_src()
        self.install_deps_adhoc(deb_pkgs=[pkg_rosdep])

        if init_rosdep:
            OsUtil.setup_rosdep()
        os.chdir(path_ws)
        self._logger.info(f"Changed directory to '{path_ws}' to run 'rosdep install' against the manifest that defines dependencies")
        output, error, bash_return_code = OsUtil.subproc_bash("rosdep install --from-paths . --ignore-src -r -y --verbose")
        if bash_return_code != 0:
            self.add_runtime_issue(f"'rosdep install' failed.\n\tOutput: {output}\n\tError: {error}")
        else:
            self.add_runtime_issue(f"'rosdep install' succeeded.\n\tOutput: {output}\n\tError: {error}")
        
    def setup_rosdep_and_run(self, path_ws, pkg_rosdep=_APTPKG_ROSDEP2, init_rosdep=False):
        """
        @note: For Debian OS, no official prebuilt rosdep installer via apt is available,
          but a community version 'python3-rosdep2' maintained by a long-term community member (Jochen S.) is avaialble
          so using it for now. But for Ubuntu 'python3-rosdep' (without 2 at the end) is the official and should be used.
        """
        self.setup_ros_installer_src()
        # Install deb dependencies that cannot be installed in the batch
        # installation step that is planned later in this sequence.
        self.install_deps_adhoc(deb_pkgs=["python3-pip", pkg_rosdep], pip_pkgs=self._PIP_PKGS)

        self.exec_rosdep_update(path_ws, pkg_rosdep, init_rosdep)

    def nonrosdep_deps(self) -> tuple[list[str], list[str]]:
        """@override"""
        return self._DEBIAN_DEB_DEPS, self._PIP_PKGS

    def _install_deps_adhoc_debian(self, deb_pkgs=[], pip_pkgs=[], allow_pip_break=False):
        OsUtil.apt_install(deb_pkgs, self._logger)
        self._logger.info(f"pip_pkgs: {pip_pkgs}")
        OsUtil.install_pip_adhoc(pip_pkgs, allow_break=allow_pip_break)
        # TODO self.add_runtime_issue(f"'rosdep install' failed.\n\tOutput: {output}\n\tError: {error}")

    def install_deps_adhoc(self, deb_pkgs, pip_pkgs="", allow_pip_break=False, snap_pkgs: list[str]=[]):
        """
        @summary: Install the packages that cannot be installed by batch using
            'rosdep install'. Example is 'python3-rosdep' itself.
        @param deb_pkgs: [str] intended but if a str without being in a list format nor whitespace,
            then it should be accepted as well, as it'll be internally converted to a list.
        @param pip_pkgs: Same applies as 'deb_pkgs'.
        @param allow_break: If True, `pip` runs with '--break-system-packages' option.
        """
        self.apt_update()
        self._install_deps_adhoc_debian(deb_pkgs, pip_pkgs, allow_pip_break)

    def create_data_dir(self, dirs_tobe_made):
        self._logger.info("Making directories historically been in use: {}".format(dirs_tobe_made))
        for dir in dirs_tobe_made:
            try:
                os.mkdir(dir)
            except FileExistsError as e:
                self._logger.warning("{}\nIgnore and moving on for now.".format(str(e)))
                self.add_runtime_issue(e)

    def git_clone_impl(self, repo_to_clone, dir_cloned_at, branch=""):
        _option = ""
        if branch:
            _option = "-b" + " " + branch
        OsUtil.subproc_bash(f"git clone {repo_to_clone} {dir_cloned_at} {_option}", does_sudo=False, print_stdout_err=True)

    def setup_ssh(self, skip=False, path_local_conf_repo=""):
        """
        @raise RuntimeException: When ssh server not confirmed to be running.
        """
        self._logger.info(f"On {OsUtil.TYPE_OS_LINUX} type of OS, where 'rosdep install' should function (?), \
                          SSH server should be enabled when a set of relevant pkgs get installed via 'rosdep'.")
        if skip:
            self._logger.warning(f"User chose to skip ssh setup.")
            return

        # Verify ssh server is up and running.
        try:
            OsUtil.is_ssh_server()
        except Exception as e:
            raise e

    def setup_oracle_java(self):
        self._logger.warning("""The following should be done manually, mainly due to license operation that is hard to automate, in order to set up Oracle Java that is required by Eclipse:

    # Refs:
    # - http://askubuntu.com/a/651045/24203
    # - http://superuser.com/a/939651/106974
    ## sudo add-apt-repository ppa:webupd8team/java
    ## apt update && apt-get install -y oracle-java8-installer
    ## sudo apt install oracle-java8-set-default
""")

    def run(self, host_config, conf_repo_remote, conf_base_path=""):
        super().run(host_config, conf_repo_remote, conf_base_path)
        self.setup_oracle_java()

    def apt_update(self):
        if self.apt_updated:
            self._logger.warning("'apt update' was already done before. Skipping")
            return
        cmd = f"apt update"
        _out, _err, retcode = OsUtil.subproc_bash(cmd, does_sudo=True)
        if retcode != 0:
            raise subprocess.CalledProcessError(
                returncode = retcode,
                cmd = cmd,
                stderr = _err)
        self.apt_updated = True

    def setup_docker(self, userid_os, skip=False):
        try:
            if skip or self._is_docker_setup():
                self._logger.info(f"Looks like Docker setup is already completed.")
                return
        except RuntimeWarning as e:
            self._logger.warning(f"Issue found in setting up Docker but continuing to do so. Source of the error: {str(e)}")
            self.add_runtime_issue(e)
        if not self._exec_docker:
            self.add_runtime_issue("Not all necessary executables is found. Aborting setting up Docker.")
            return

        OsUtil.subproc_bash("groupadd docker", does_sudo=True)
        OsUtil.subproc_bash("usermod -aG docker {}".format(userid_os), does_sudo=True)

        # From https://docs.docker.com/engine/installation/linux/ubuntulinux/
        OsUtil.subproc_bash(f"apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D", does_sudo=True)
        OsUtil.subproc_bash(f'echo "deb https://apt.dockerproject.org/repo ubuntu-`lsb_release -sc` main" > /etc/apt/sources.list.d/docker.list', does_sudo=True)
        self.apt_update()
        OsUtil.subproc_bash(f"apt purge lxc-docker", does_sudo=True)
        OsUtil.subproc_bash(f"apt-cache policy docker-engine")
        OsUtil.subproc_bash(f"apt install linux-image-extra-$(uname -r)", does_sudo=True)
        # Workaround found at http://stackoverflow.com/questions/22957939/how-to-answer-an-apt-get-configuration-change-prompt-on-travis-ci-in-this-case
        OsUtil.subproc_bash(f'apt -q -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confnew" install docker-engine',
                            does_sudo=True, non_interactive=True)
        OsUtil.subproc_bash(f"service docker start", does_sudo=True)
        OsUtil.subproc_bash(f"unset $DEBIAN_FRONTEND")
        OsUtil.subproc_bash(f'docker run hello-world && echo "docker seems to be installed successfully." || (echo "Something went wrong with docker installation."; RESULT=1', does_sudo=True)
    
    def _setup_git(self):
        self.install_deps_adhoc(deb_pkgs=["python3-git"])
        # If git had not been installed yet prior to the one line above,
        # then its executable hadn't been available either.
        self._which_git = OsUtil.which("git")

    def setup_configs(
            self,
            host_config: HostConf,
            abs_path_confdir: str=ShellCapableOsSetup._PATH_DEFAULT_CONFIG_CONFDIR,
            abs_path_private_confdir: str=ShellCapableOsSetup._PATH_DEFAULT_PERMANENT_CONF_REPO):
        pairs_conf_autostart = [
            ConfigDispatch(
                path_source=os.path.join(abs_path_confdir, "gnome-system-monitor.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".gconf/apps"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(abs_path_confdir, "indicator-multiload.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".config", "autostart"),
                is_symlink=True),
            ]
        for conf in pairs_conf_autostart:
            self.setup_file(conf)

        pairs_conf_bash = [
            ConfigDispatch(
                path_source=os.path.join(abs_path_confdir, "bash", host_config.bash_cfg),
                path_dest=os.path.join(self._user_home_dir, ".bashrc"),
                is_symlink=True),
            ]
        for c in pairs_conf_bash:
            self.setup_file(c, overwrite=True)

        pairs_conf_tools = [
            ConfigDispatch(
                path_source=os.path.join(abs_path_confdir, "gnome-system-monitor.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".gconf/apps"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(abs_path_confdir, "indicator-multiload.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".gconf/apps"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(abs_path_confdir, "tmux_default.conf"),
                path_dest=os.path.join(self._user_home_dir, ".tmux.conf"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(abs_path_confdir, "emacs", host_config.emacs_cfg),
                path_dest=os.path.join(self._user_home_dir, ".emacs"),
                is_symlink=True),
            ConfigDispatch(
                path_source=os.path.join(abs_path_confdir, "dot_xbindkeysrc"),
                path_dest=os.path.join(self._user_home_dir, ".xbindkeysrc"),
                is_symlink=True),
            ]
        for c in pairs_conf_tools:
            self.setup_file(c)

    def verify_deb_installed(self, deb_pkg_name: str):
        """
        @summary: Verifies if `deb_pkg_name` package is installed.
        @exception RuntimeError: If `deb_pkg_name` package is not installed.
        """
        cmd = f"apt-cache policy {deb_pkg_name}"
        output, error, bash_return_code = OsUtil.subproc_bash(cmd, does_sudo=True)
        if bash_return_code != 0:
            raise RuntimeError(f"Package '{deb_pkg_name}' is not installed.")
        self._logger.info(f"Package '{deb_pkg_name}' seems already installed. \n\tCMD executed: {cmd}\n\tOutput: {output}")

    def swap_caps_ctrl(self):
        """
        @summary: Installs S/Ws that are needed to swap Caps Lock and Ctrl keys, BUT configuring it needs to be done manually.
        """
        self.verify_deb_installed(self._DEB_CAPS_CTRL_UTIL)
        _URL_INSTRUCTION_CAPS_CTRL = "https://github.com/kinu-garage/hut_10sqft/issues/1230#issuecomment-2994825273"
        self._logger.info(f"Following {_URL_INSTRUCTION_CAPS_CTRL}, setup manually the swap of Caps Lock and Ctrl keys.")
