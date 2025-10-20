#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage

import argparse
import logging
import os
import pathlib
from typing import List


class CompInitSetupConfig():
    """
    @summary A data class that just holds configuration parameters, intended to be used by BOTH CompInitSetup and SucoInstaller,
        meaning this Python module to be imported by suco_main.py
    """
    HOSTNAME_BRYA = "130s-brya"
    HOSTNAME_C13_MORPH = "130s-C13-Morph"
    HOSTNAME_MAC1 = "130s-mac1"
    HOSTNAME_OPFYDE_RPI5 = "opfyde-rpi5"
    HOSTNAME_P16S = "130s-p16s-2"
    HOSTNAME_ZORK16 = "130s-zork16"

    PATH_SYMLINKS_DIR = "link"  # e.g. ~/link
    FOLDER_CONF_PERM_REPO = "config"
    # Name of the local repo that stores the config and will have to be
    # available for the entire life time of the OS. 
    REPO_PERMANENT_CONFIG = "hut_10sqft"
    BRANCH_DEFAULT_CONF_REPO = "develop"
    LOGGER_NAME_CISC = "CompInitSetup-logger"
    # Un-expanded version of this looks like '~/.config'
    PATH_FOLDER_CONF = os.path.join(pathlib.Path.home(), "." + FOLDER_CONF_PERM_REPO)
    # Un-expanded version of this looks like 'hut_10sqft/config'
    PATH_DEFAULT_CONFIG_CONFDIR = os.path.join(REPO_PERMANENT_CONFIG, FOLDER_CONF_PERM_REPO)
    # Un-expanded version of this looks like '~/.config/hut_10sqft'
    PATH_DEFAULT_PERMANENT_CONF_REPO = os.path.join(PATH_FOLDER_CONF, REPO_PERMANENT_CONFIG)
    PATH_TEMP_COLCON_WS = os.path.join(pathlib.Path.home(), ".local", "share", "tmp_colconws_suco")  # `~/.local/share/tmp_colconws_suco`
    PATH_COLCON_SRC = "src"  # Constant for colcon workspace
    URL_HUT = f"https://github.com/kinu-garage/{REPO_PERMANENT_CONFIG}.git"

    MSG_CONSOLE_TOOL_INTRO = "This tool 'SUCO' is for setting up a Linux-based personal computer. \
     It does the following: 1) Installs dependency (which must be defined in package.xml). \
     2) Create symlinks to config files, which are provided in hut_10sqft local git repo \
     i.e. (Having hut_10sqft somewhere on the host is required)."
    MSG_ARG_BASE_CONF_PATH = f"Path of the folder where the conf repo will be cloned into. \
        Default: {PATH_FOLDER_CONF}. Modifying this is NOT recommended, and behavior with \
        the modified path is not planned to be tested as of 2024/08."  # Default is `~/.config` as of 2025/10


class SucoInstaller():
    """
    @summary: Installing SUCO (that sets up OS) itself. Intended to be downloaded a single executable file without
      any custom dependencies except Python standard libraries.
    """
    _MSG_CONSOLE_TOOL_INTRO = ""
    _MSG_ARG_PATH_COLCONWS = f"Path to the temporary Colcon workspace for building and installing SUCO itself. \
        If not passed then the path will be the default '{CompInitSetupConfig.PATH_TEMP_COLCON_WS}'."
    _MSG_PIP_BREAK_SYSPKG = "If specified, install packages by pip even if the package is already installed by \
        the system package manager (e.g., apt). This may break the system packages."

    def __init__(self):
        self._logger = logging.getLogger(CompInitSetupConfig.LOGGER_NAME_CISC)
        log_handler = logging.StreamHandler()
        self._logger.setLevel(logging.DEBUG)  # Needs changed
        self._logger.addHandler(log_handler)

    @staticmethod
    def init_cli_args_suco() -> argparse.Namespace:
        """
        @summary: Create args obj that can be shared among multiple SUCO usecases,
          e.g. install-suco, setting up by executing suco.        
        """
        parser = argparse.ArgumentParser(description=CompInitSetupConfig.MSG_CONSOLE_TOOL_INTRO)
        parser.add_argument("--path_base_conf", required=False, help=CompInitSetupConfig.MSG_ARG_BASE_CONF_PATH, default=CompInitSetupConfig.PATH_FOLDER_CONF)
        parser.add_argument("--path_temp_colconws", required=False, help=SucoInstaller._MSG_ARG_PATH_COLCONWS, default=CompInitSetupConfig.PATH_TEMP_COLCON_WS)
        parser.add_argument("--pip_break_syspkg", required=False, help=SucoInstaller._MSG_PIP_BREAK_SYSPKG, action="store_true")
        parser.add_argument("--git_branch", required=False, help="Branch of SUCO repo", default=CompInitSetupConfig.BRANCH_DEFAULT_CONF_REPO)
        return parser

    def cli_args_install_suco(self, parser: argparse.Namespace) -> argparse.Namespace:
        """
        @summary: Create args obj for installing SUCO itself.        
        """
        if not parser:
            parser = SucoInstaller.init_cli_args_suco()

        args = parser.parse_args()
        self._logger.info("args: {}".format(args))
        return args

    def install_colcon(self, break_syspkg: bool=False) -> None:
        opt_break_pip = "--break-system-packages" if break_syspkg else ""
        cmd_install_colcon = f"pip3 install colcon-common-extensions {opt_break_pip}"
        self._logger.info(f"Installing colcon by executing: {cmd_install_colcon}")
        ret = os.system(cmd_install_colcon)
        if ret != 0:
            self._logger.error(f"Failed to install colcon.")
            return

    def source_colconws(self, cmd_sourcing_ws: str) -> None:
        self._logger.info(f"Sourcing the colcon workspace setting by executing: {cmd_sourcing_ws}")
        ret = os.system(cmd_sourcing_ws)
        if ret != 0:
            self._logger.error(f"Failed to source the colcon workspace setting.")
            return

    def main(self):
        """
        @summary: Install, or at least clone, and make SUCO ready to be executed locally, which includes:
            1) Clone `hut_10sqft` repo from GitHub into the folder `~/.local/share/tmp_colconws_suco/src`.
              If the folder already exists, try to update the git repo.
            2) Build and install packages in the temporary Colcon workspace
              (as of 2025/10, the pkgs to be built-installed are `hut_10sqft` and `hut_10sqft_lib`).

            After these, user can continue, source the olcon workspace setting, execute SUCO from the colcon workspace.
        @note: This creates 2 different locations of `hut_10sqft` local repo, each of which serves
          for different purposes as follows:
            - ~/.config/hut_10sqft: Permanent location of the config repo that the applications on the OS refers to.
            - ~/.local/share/tmp_colconws_suco/src/hut_10sqft: Temporary location of the config repo
              that is used for building and installing SUCO itself. This may be deleted after SUCO is executed.
        """
        args = self.cli_args_install_suco(None)

        # 1) Clone `hut_10sqft` repo from GitHub into the folder `~/.local/share/tmp_colconws_suco/src`.
        #    If the folder already exists, try to update the git repo.
        os.makedirs(args.path_temp_colconws, exist_ok=True)
        path_srcdir = os.path.join(args.path_temp_colconws, CompInitSetupConfig.PATH_COLCON_SRC)
        os.makedirs(path_srcdir, exist_ok=True)
        path_hut = os.path.join(path_srcdir, CompInitSetupConfig.REPO_PERMANENT_CONFIG)
        if not os.path.exists(path_hut):
            branch_option = f"-b {args.git_branch}" if args.git_branch else ""
            cmd_clone = f"git clone {CompInitSetupConfig.URL_HUT} {branch_option} {path_hut}"
            self._logger.info(f"Cloning '{CompInitSetupConfig.URL_HUT}' repo into '{path_hut}' by executing: {cmd_clone}")
            ret = os.system(cmd_clone)
            if ret != 0:
                self._logger.error(f"Failed to clone '{CompInitSetupConfig.REPO_PERMANENT_CONFIG}' repo.")
                return
        else:
            self._logger.info(f"'{CompInitSetupConfig.REPO_PERMANENT_CONFIG}' repo already exists at '{path_hut}'. Try to update it.")
            cmd_pull = f"cd {path_hut} && git pull"
            ret = os.system(cmd_pull)
            if ret != 0:
                self._logger.error(f"Failed to update '{CompInitSetupConfig.REPO_PERMANENT_CONFIG}' repo.")
                return

        # Install colcon from pip if not yet installed.
        self.install_colcon(args.pip_break_syspkg)

        # 2) Build and install packages in the temporary Colcon workspace
        #   (as of 2025/10, the pkgs to be built-installed are `hut_10sqft` and `hut_10sqft_lib`).
        cmd_build = f"cd {args.path_temp_colconws} && colcon build --symlink-install"
        self._logger.info(f"Building and installing SUCO itself by executing: {cmd_build}")
        ret = os.system(cmd_build)
        if ret != 0:
            self._logger.error(f"Failed to build and install SUCO itself.")
            return

        # 3) Source the colcon workspace setting.
        cmd_sourcing_ws = f"source {os.path.join(args.path_temp_colconws, 'install', 'setup.bash')}"
        #self.source_colconws(cmd_sourcing_ws)
        self._logger.info(f"""SUCO installation is complete. You can now source the colcon workspace setting by:\n\t{cmd_sourcing_ws}""")


if __name__ == '__main__':
    si = SucoInstaller()
    si.main()
