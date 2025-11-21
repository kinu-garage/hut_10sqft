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
from hut_10sqft.abst_comp_setup import ShellCapableOsSetup
from hut_10sqft.suco_installer import CompInitSetupConfig, SucoInstaller


class CompInitSetup():
    """
    @summary TBD
    """
    # Messages for stdout
    _MSG_PATH_PERMCONF_REPO = f"Path to the FINAL location of '{ShellCapableOsSetup._REPO_PERMANENT_CONFIG}' local repo. \
        If not passed then the path will be the default {ShellCapableOsSetup._PATH_DEFAULT_PERMANENT_CONF_REPO}, \
        which is for {DebianSetup._OS_TYPE}."
    _MSG_PATH_CONF_DIR = f"""Path to the the config folder within the '{ShellCapableOsSetup._REPO_PERMANENT_CONFIG}' repo.
 If not passed then the path will be the default {ShellCapableOsSetup._PATH_DEFAULT_CONFIG_CONFDIR}."""
    _MSG_PATH_CONF_DIR = f"""Path to the the config folder within the '{ShellCapableOsSetup._REPO_PERMANENT_CONFIG}' repo.
 If not passed then the path will be the default {ShellCapableOsSetup._PATH_DEFAULT_CONFIG_CONFDIR}."""
    _MSG_PATH_PRIVATE_CONF_DIR = f"Path to the the folder of private configs within the Dropbox dir. \
        If not passed then the path will be the default {ShellCapableOsSetup._PATH_DEFAULT_PRIVATE_CONFDIR}."
    _MSG_ARG_PATH_COMMON_SYMLINKS = f"""Path to the folder that contains symlinks.
 If not passed then the path will be the default {CompInitSetupConfig.PATH_SYMLINKS_DIR}."""    
    _MSG_ARG_USERID = """User ID on the OS that will be mainly used. While this
is optional, it is recommened to specify. If nothing passed, then the tool
treats the user ID tha is used to execute this tool as the main user."""
    _MSG_REMOVE_TMP_COLCONWS = f"If specified, remove the temporary colcon workspace after SUCO is executed. \
      If SUCO installation was done by 'suco_installer', there should be a temporary colcon workspace at e.g. \
      '{CompInitSetupConfig.PATH_TEMP_COLCON_WS}'."
    _URL_CONFREPO = f"https://github.com/kinu-garage/{ShellCapableOsSetup._REPO_PERMANENT_CONFIG}.git"
    _PATH_VSCODE_INSTALLER = pathlib.Path("~/link/GoogleDrive/lifeinfra/computer/installer/vscode/code_1.103.2-1755709794_amd64.deb").expanduser()

    def __init__(self):
        self._logger = logging.getLogger(CompInitSetupConfig.LOGGER_NAME_CISC)
        log_handler = logging.StreamHandler()
        self._logger.setLevel(logging.DEBUG)  # Needs changed
        self._logger.addHandler(log_handler)

    def _cli_args(self):
        """
        @rtype: argparse.Namespace
        """
        parser = SucoInstaller.init_cli_args_suco()
        # Optional but close to required args
        parser.add_argument("--hostname", required=True, help="Specify in case you need to modify the host name.")
        parser.add_argument("--msg_endroll", help="Specify the message string that will be printed at the end in case of need.")
        parser.add_argument("--os_distro", required=True, help=f"Type of OS distro. Options: {ChromeOsSetup._OS_TYPE} | {DebianSetup._OS_TYPE} | {UbuntuOsSetup._OS_TYPE}")
        parser.add_argument("--os_type", required=False, help=f"Type of OS. Options: {OsUtil.TYPE_OS_LINUX} | {MacOsSetup._OS_TYPE}")
        parser.add_argument("--path_local_conf_repo", help=self._MSG_PATH_PERMCONF_REPO, default=CompInitSetupConfig.PATH_DEFAULT_PERMANENT_CONF_REPO)
        parser.add_argument("--conf_repo_version", required=False, help="Git version of the repo e.g. 'develop'", default="develop")
        parser.add_argument("--path_conf_dir", help=self._MSG_PATH_CONF_DIR, default=CompInitSetupConfig.PATH_DEFAULT_CONFIG_CONFDIR)
        parser.add_argument("--path_conf_private_dir", help=self._MSG_PATH_PRIVATE_CONF_DIR, default=ShellCapableOsSetup._PATH_DEFAULT_PRIVATE_CONFDIR)        
        parser.add_argument("--path_symlinks_dir", required=False, help=self._MSG_ARG_PATH_COMMON_SYMLINKS, default=CompInitSetupConfig.PATH_SYMLINKS_DIR)
        parser.add_argument(f"--{CompInitSetupConfig.ARG_USER_ID}", required=False, help=self._MSG_ARG_USERID, default="")
        parser.add_argument("--skip_setup_docker", required=False, help="Skip setup for docker", action="store_true")
        parser.add_argument("--skip_ssh", required=False, help="Skip setup for ssh server", action="store_true")
        parser.add_argument("--path_vscode_installer", required=False, help="Absolute path to the installer of VSCode.", default=self._PATH_VSCODE_INSTALLER)
        parser.add_argument("--remove_tmpws", required=False, help=self._MSG_REMOVE_TMP_COLCONWS, action="store_true")

        args = parser.parse_args()
        self._logger.info("args: {}".format(args))

        return args

    def remove_colconws(self, path_colconws: str) -> bool:
        """
        @summary: Remove a (temporary) colcon workspace that was used for building-installing SUCO itself.
        @param path_colconws str: Path to the (temporary) colcon workspace.
        @return bool: `True` if removal was successful or the path does not exist.
        @raise RuntimeError: When `path_colconws` is empty.
        @raise RuntimeWarning: When a path at `path_colconws` does not exist.
        """
        if not path_colconws:
            raise RuntimeError(f"Variable 'path_colconws' must not be empty.")
        elif not os.path.exists(path_colconws):
            raise RuntimeWarning(f"Temporary colcon workspace '{path_colconws}' does not exist. Nothing to remove.")
        self._logger.info(f"Removing the (temporary) colcon workspace at '{path_colconws}'.")
        OsUtil.remove_tree(path_colconws)
        return True

    def run(self) -> bool:
        """
        @return bool: `True` if reaches the end of the method, if it doesn't reach the end nothing returns.
          This is primarily for testing purpose.
        """
        _args = self._cli_args()
        # Builder pattern
        _os_builder = None
        _user_id = ""
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
        if _args.hostname == CompInitSetupConfig.HOSTNAME_P16S:
            _host_cfg = HostConf(_args.hostname, "bashrc_130s-p16s", "emacs_130s-p16s.el", "id_rsa_130s-p16s", "id_rsa_130s-p16s.pub")
        elif _args.hostname == CompInitSetupConfig.HOSTNAME_BRYA:
            _host_cfg = _host_cfg_brya            
        elif _args.hostname == (CompInitSetupConfig.HOSTNAME_C13_MORPH or CompInitSetupConfig.HOSTNAME_ZORK16 or CompInitSetupConfig.HOSTNAME_OPFYDE_RPI5):
            _host_cfg = HostConf(_args.hostname, "130s-brya.bash", "130s-zork16.el", "id_rsa_130s-c13-morph", "id_rsa_130s-c13-morph.pub")
        else:
            self._logger.warning(f"'{_args.hostname=}' not matching any host. Using default config set (that of '130s-brya').")
            _host_cfg = _host_cfg_brya
            _host_cfg.hostname = _args.hostname

        # Ref. "_MSG_ARG_BASE_CONF_PATH"
        _conf_base_path = OsUtil.tilde_to_expand(_args.path_base_conf) if _args.path_base_conf else ""
            
        _os_builder.run(_host_cfg,
                        conf_repo_remote=self._URL_CONFREPO,
                        conf_base_path=_conf_base_path)

        if _args.remove_tmpws:
            try:
                self.remove_colconws(_args.path_temp_colconws)
            except (RuntimeWarning, RuntimeError) as rw:
                _os_builder.add_runtime_issue(str(rw))

        _msg_endroll = _args.msg_endroll if _args.msg_endroll else "Setup finished."
        self._logger.info(_msg_endroll)
        _os_builder.listup_runtime_issues()
        return True


def main():
    comp_setup = CompInitSetup()
    comp_setup.run()


if __name__ == '__main__':
    main()
