#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage

import argparse
import logging
import os
import pathlib
import pwd
from typing import List

from hut_10sqft.host_config import HostConf
from hut_10sqft_lib.os_util import OsUtil
from hut_10sqft.comp_chrome_os import ChromeOsSetup
from hut_10sqft.comp_debian import DebianSetup
from hut_10sqft.comp_ubuntu import UbuntuOsSetup
from hut_10sqft.comp_mac_os import MacOsSetup


class CompInitSetup():
    """
    @summary TBD
    """
    HOSTNAME_BRYA = "130s-brya"
    HOSTNAME_C13_MORPH = "130s-C13-Morph"
    HOSTNAME_MAC1 = "130s-mac1"
    HOSTNAME_OPFYDE_RPI5 = "opfyde-rpi5"
    HOSTNAME_P16S = "130s-p16s-2"
    HOSTNAME_ZORK16 = "130s-zork16"

    _LOGGER_NAME = "CompInitSetup-logger"
    # Name of the local repo that stores the config and will have to be
    # available for the entire life time of the OS. 
    _REPO_PERMANENT_CONFIG = "hut_10sqft"
    _FOLDER_CONF_PERM_REPO = "config"
    _PATH_FOLDER_CONF = os.path.join(pathlib.Path.home(), "." + _FOLDER_CONF_PERM_REPO)
    # Un-expanded version of this looks like '~/.config/hut_10sqft'
    _PATH_DEFAULT_PERMANENT_CONF_REPO = os.path.join(_PATH_FOLDER_CONF, _REPO_PERMANENT_CONFIG)
    # Un-expanded version of this looks like 'hut_10sqft/config'
    _PATH_DEFAULT_CONFIG_CONFDIR = os.path.join(_REPO_PERMANENT_CONFIG, _FOLDER_CONF_PERM_REPO)
    _PATH_SYMLINKS_DIR = "link"  # e.g. ~/link
    # Messages for stdout
    _MSG_CONSOLE_TOOL_INTRO = """This tool is for setting up a Linux-based personal computer.
     It does the following: 1) Installs dependency (which must be defined in package.xml). 
     2) Create symlinks to config files, which are provided in hut_10sqft local git
       repo i.e. (Having Khut_10sqft somewhere on the host is required)."""
    _MSG_PATH_PERMCONF_REPO = f"""Path to the FINAL location of '{_REPO_PERMANENT_CONFIG}' local repo.
 If not passed then the path will be the default {_PATH_DEFAULT_PERMANENT_CONF_REPO}, 
which is for {DebianSetup._OS_TYPE}."""
    _MSG_PATH_CONF_DIR = f"""Path to the the config folder within the '{_REPO_PERMANENT_CONFIG}' repo.
 If not passed then the path will be the default {_PATH_DEFAULT_CONFIG_CONFDIR}."""
    _MSG_ARG_PATH_COMMON_SYMLINKS = f"""Path to the folder that contains symlinks.
 If not passed then the path will be the default {_PATH_SYMLINKS_DIR}."""    
    _MSG_ARG_USERID = """User ID on the OS that will be mainly used. While this
is optional, it is recommened to specify. If nothing passed, then the tool
treats the user ID tha is used to execute this tool as the main user."""
    _MSG_ARG_BASE_CONF_PATH = """Path where the conf repo will be cloned into.
 Modifying it is an advanced/bold move, and behavior with the modified path is not planned to be tested as of 2024/08."""
    _URL_CONFREPO = f"https://github.com/kinu-garage/{_REPO_PERMANENT_CONFIG}.git"
    _PATH_VSCODE_INSTALLER = pathlib.Path("~/link/GoogleDrive/lifeinfra/computer/installer/vscode/code_1.103.2-1755709794_amd64.deb").expanduser()

    def __init__(self):
        self._logger = logging.getLogger(self._LOGGER_NAME)
        log_handler = logging.StreamHandler()
        self._logger.setLevel(logging.DEBUG)  # Needs changed
        self._logger.addHandler(log_handler)

    def _cli_args(self):
        """
        @rtype: argparse.Namespace
        """
        parser = argparse.ArgumentParser(description=self._MSG_CONSOLE_TOOL_INTRO)
        # Optional but close to required args
        parser.add_argument("--hostname", required=True, help="Specify in case you need to modify the host name.")
        parser.add_argument("--msg_endroll", help="Specify the message string that will be printed at the end in case of need.")
        parser.add_argument("--os_distro", required=True, help=f"Type of OS distro. Options: {ChromeOsSetup._OS_TYPE} | {DebianSetup._OS_TYPE} | {UbuntuOsSetup._OS_TYPE}")
        parser.add_argument("--os_type", required=False, help=f"Type of OS. Options: {OsUtil.TYPE_OS_LINUX} | {MacOsSetup._OS_TYPE}")
        parser.add_argument("--path_base_conf", required=False, help=self._MSG_ARG_BASE_CONF_PATH, default=self._PATH_FOLDER_CONF)
        parser.add_argument("--path_local_conf_repo",
                            help=self._MSG_PATH_PERMCONF_REPO,
                            default=self._PATH_DEFAULT_PERMANENT_CONF_REPO)
        parser.add_argument("--conf_repo_version", required=False, help="Git version of the repo e.g. 'develop'", default="develop")
        parser.add_argument("--path_conf_dir",
                            help=self._MSG_PATH_CONF_DIR,
                            default=self._PATH_DEFAULT_CONFIG_CONFDIR)
        parser.add_argument("--path_symlinks_dir", required=False, help=self._MSG_ARG_PATH_COMMON_SYMLINKS, default=self._PATH_SYMLINKS_DIR)
        parser.add_argument("--user_id", required=False, help=self._MSG_ARG_USERID, default="")
        parser.add_argument("--skip_setup_docker", required=False, help="Skip setup for docker", action="store_true", default=True)
        parser.add_argument("--path_vscode_installer", required=False, help="Absolute path to the installer of VSCode.", default=self._PATH_VSCODE_INSTALLER)

        args = parser.parse_args()
        self._logger.info("args: {}".format(args))

        self._logger.info("If 'user_id' is not passed, get the user id of the current process.")
        if not args.user_id:
            args.user_id = pwd.getpwuid(os.getuid())[0]

        if not args.hostname:
            args.hostname = os.uname()[1]
            self._logger.warn(f"If 'hostname' is not passed, get the host name from the OS.: {args.hostname}")

        return args

    def run(self):
        _args = self._cli_args()
        # Builder pattern
        _os_builder = None
        if _args.os_distro == ChromeOsSetup._OS_TYPE:
            _os_builder = ChromeOsSetup(args_in=_args)
        elif _args.os_distro == DebianSetup._OS_TYPE:
            _os_builder = DebianSetup(args_in=_args)
        elif _args.os_distro == UbuntuOsSetup._OS_TYPE:
            _os_builder = UbuntuOsSetup(args_in=_args)
        elif _args.os_distro == MacOsSetup._OS_TYPE:
            _os_builder = MacOsSetup(args_in=_args)
        else:
            raise NotImplementedError(f"Chosen OS '{_args.os}' is either not implemented or invalid.")

        # Env vars per host: Bash, Emacs
        _host_cfg = None
        BASH_CONFIG_NAME =  ""
        EMACS_CONFIG_NAME = ""
        _host_cfg_brya = HostConf(_args.hostname, "130s-brya.bash", "emacs_130s-brya.el", "id_rsa_130s-brya", "id_rsa_130s-brya.pub")
        if _args.hostname == self.HOSTNAME_P16S:
            _host_cfg = HostConf(_args.hostname, "bashrc_130s-p16s", "emacs_130s-p16s.el", "id_rsa_130s-p16s", "id_rsa_130s-p16s.pub")
        elif _args.hostname == self.HOSTNAME_BRYA:
            _host_cfg = _host_cfg_brya            
        elif _args.hostname == (self.HOSTNAME_C13_MORPH or self.HOSTNAME_ZORK16 or self.HOSTNAME_OPFYDE_RPI5):
            _host_cfg = HostConf(_args.hostname, "130s-brya.bash", "130s-zork16.el", "id_rsa_130s-c13-morph", "id_rsa_130s-c13-morph.pub")
        else:
            self._logger.warning(f"'{_args.hostname=}' not matching any host. Using default config set (that of '130s-brya').")
            _host_cfg = _host_cfg_brya
            _host_cfg.hostname = _args.hostname

        # Ref. "_MSG_ARG_BASE_CONF_PATH"
        _conf_base_path = OsUtil.tilde_to_expand(_args.path_base_conf) if _args.path_base_conf else ""
            
        _os_builder.run(_args,
                        _host_cfg,
                        conf_repo_remote=self._URL_CONFREPO,
                        conf_base_path=_conf_base_path)

        _msg_endroll = _args.msg_endroll if _args.msg_endroll else "Setup finished."
        self._logger.info(_msg_endroll)
        _os_builder.listup_runtime_issues()


def main():
    comp_setup = CompInitSetup()
    comp_setup.run()


if __name__ == '__main__':
    main()
