#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage

import argparse
try:
    import git
except ModuleNotFoundError as e:
    print(f"This module isn't available at the moment but will be installed later.\n{str(e)}")
import importlib
import logging
import os
import pathlib
import pwd
import shutil
from typing import List

from hut_10sqft.config_dispatch import ConfigDispatch
from hut_10sqft.host_config import HostConf
from hut_10sqft_lib.os_util import OsUtil
from hut_10sqft.suco_installer import CompInitSetupConfig


class AbstCompSetupFactory():
    """
    @description: Applyig Abstract Factory pattern.
    """
    _DIR_DROXBOX_CONTAINER = "data"  # This is beyond programming, something that sticks with 130s' computer usage for decades.
    VAL_USERID_DEFAULT = "host_set_by_suco"

    def __init__(self, os_name="", args_in: argparse.Namespace=None, default_userid=VAL_USERID_DEFAULT):
        """
        @description: Some behaviors:
          - If args_in.user_id is not set, `set_user_id` will be called to set it.
        """
        self._os = os_name
        self._args_in = args_in

        self.init_logger(logger_name=__name__)
        self._list_runtime_issues = []

        if not getattr(args_in, f"{CompInitSetupConfig.ARG_USER_ID}", None):
            self.set_user_id(args_in, default_user_id=default_userid)

        if not getattr(args_in, "hostname", None):
            args_in.hostname = os.uname()[1]
            self._logger.warning(f"If 'hostname' is not passed, get the host name from the OS.: {args_in.hostname}")

        # Create a conf folder under ~/.
        self._path_base_conf = os.path.join(pathlib.Path.home(), ".config")
        if not os.path.exists(self._path_base_conf):
            os.makedirs(self._path_base_conf)

    @property
    def list_runtime_issues(self):
        return self._list_runtime_issues

    @property
    def path_base_conf(self):
        return self._path_base_conf

    @path_base_conf.setter
    def path_base_conf(self, value):
        self._path_base_conf = value

    def set_user_id(self, args_in: argparse.Namespace, default_user_id=VAL_USERID_DEFAULT):
        if not getattr(args_in, f"{CompInitSetupConfig.ARG_USER_ID}", None):
            try:
                args_in.user_id = pwd.getpwuid(os.getuid()).pw_name or default_user_id
            except Exception:
                args_in.user_id = default_user_id
            self._logger.warning(f"'{CompInitSetupConfig.ARG_USER_ID}' is not passed, set by SUCO = {args_in.user_id}.")
        else:
            self._logger.info(f"'{CompInitSetupConfig.ARG_USER_ID}' is passed as '{args_in.user_id}.")
        
    def add_runtime_issue(self, value):
        """
        @param value: Although the type of this not strictly enforced, recommended to be Exption type.
        """
        self._list_runtime_issues.append(value)

    def listup_runtime_issues(self):
        if not self.list_runtime_issues:
            self._logger.info("No runtime issues recorded:")
            return

        self._logger.info("Runtime issues captured:")
        _issue_count = 1
        for issue in self.list_runtime_issues:
            self._logger.warning(f"\tIssue #{_issue_count}: {str(issue)}")
            _issue_count += 1

    def init_logger(self, logger_name, logger_level=logging.DEBUG):
        self._logger = logging.getLogger(logger_name)
        log_handler = logging.StreamHandler()
        self._logger.setLevel(logger_level)
        self._logger.addHandler(log_handler)

    def setup_ros_installer_src(self):
        raise NotImplementedError()

    def setup_git_config(self, path_local_perm_conf):
        raise NotImplementedError()

    def setup_dropbox(self):
        raise NotImplementedError()

    def swap_caps_ctrl(self):
        raise NotImplementedError()

    def update_hostname(self, hostname):
        raise NotImplementedError("Updating hostname feature is not yet implemented.")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(os_name={self._os_name})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(os_name={self._os_name})"

    def run(self, host_config: HostConf, conf_repo_remote, conf_base_path=""):
        raise NotImplementedError()

    def generate_symlinks(self, rootpath_symlinks, path_user_home=""):
        raise NotImplementedError()


class ShellCapableOsSetup(AbstCompSetupFactory):
    """
    @summary: Operating system that is capable of bash, zsh or any *sh shell that meets this tool's requirement.
    """
    # Name of the local repo that stores the config and will have to be
    # available for the entire life time of the OS. 
    _REPO_PERMANENT_CONFIG = "hut_10sqft"
    _FOLDER_CONF_PERM_REPO = "config"
    _PATH_FOLDER_CONF = os.path.join(pathlib.Path.home(), "." + _FOLDER_CONF_PERM_REPO)
    # Un-expanded version of this looks like '~/.config/hut_10sqft'
    _PATH_DEFAULT_PERMANENT_CONF_REPO = os.path.join(_PATH_FOLDER_CONF, _REPO_PERMANENT_CONFIG)
    # Un-expanded version of this looks like 'hut_10sqft/config'
    _PATH_DEFAULT_CONFIG_CONFDIR = os.path.join(_REPO_PERMANENT_CONFIG, _FOLDER_CONF_PERM_REPO)
    _PATH_DEFAULT_PRIVATE_CONFDIR = os.path.join(pathlib.Path.home(), "data", "Dropbox", "app")  # This has been used on all shell-enabled OSes so far but it'll be nice if user can designate.
    _PATH_SYMLINKS_DIR = "link"  # e.g. ~/link
    
    def __init__(self, os_name="", args_in: argparse.Namespace=None, default_userid=AbstCompSetupFactory.VAL_USERID_DEFAULT):
        super().__init__(os_name, args_in)

        # Python security https://docs.python.org/3.10/library/subprocess.html#popen-constructor
        # for those executables that are (hopefully) available on any shell independent from the type of OS.

        # TODO This member var, purpose of which particularly, is fairly undefined.
        # Better way to manage un/found execs is wanted.
        self._exec_docker = self.docker_available(self._args_in)
        self._setup_git()

    def docker_available(self, args_in: argparse.Namespace) -> str:
        """
        @deprecated: `get_paths_execs` is planned to be deprecated throughout the entire package
            as `subprocess` should be able to resolve just like the shell environment does, as long as
            the values of `PATH` env var is properly passed.
        """
        self._logger.warning(f"'get_paths_execs' in ShellCapableOsSetup: '{args_in.skip_setup_docker=}'")
        _which_docker = ""
        if not args_in.skip_setup_docker:
            # Only when 'skip_setup_docker' is True.
            self._which_docker = OsUtil.which("docker")
            self._logger.info(f"Path to 'docker' executable: {self._which_docker}")
            _which_docker = OsUtil.which("docker")
            self._logger.info(f"Path to 'docker' executable: {_which_docker}")
        return _which_docker
    
    def _setup_git(self):
        """
        @description:
            Upon implementation, 'self._which_git' must be filled in with the concrete path of the executable of 'git'.
        """
        raise NotImplementedError()

    def setup_vscode(self, path_installer: str):
        raise NotImplementedError()

    def swap_file(self, src_file: str, dest_file: str, suffix_backup=".org"):
        """
        @description: Swap 'dest_file' with 'src_file', which can be a symlink. Backup of 'dest_file' will be made alongside the swapped file.
        @param src_file: Absolute path of the source file.
        @param dest_file: Absolute path of the destination file.
        """
        raise NotImplementedError()

    def setup_file(self, file_dispatch: ConfigDispatch, overwrite=False):
        try:
            OsUtil.copy_a_file(
                file_dispatch.path_source, file_dispatch.path_dest, is_symlink=file_dispatch.is_symlink, overwrite=overwrite)
        except FileExistsError as e:
            self._logger.warning("Target already exists. Moving on. \n{}".format(str(e)))
        except FileNotFoundError as e:
            raise

    def setup_terminal_configs(self, abspath_local_perm_conf: str):
        raise NotImplementedError("Terminal config setup needs to be implemented in the derived class.")

    def setup_git_config(self, path_local_perm_conf):
        path_user_home = pathlib.Path.home()

        conf_gitconf = ConfigDispatch(
            path_source=os.path.join(path_local_perm_conf, "dot_gitconfig"),
            path_dest=os.path.join(path_user_home, ".gitconfig",),
            is_symlink=True)
        conf_gitignore = ConfigDispatch(
            path_source=os.path.join(path_local_perm_conf, "dot_gitignore_global"),
            path_dest=os.path.join(path_user_home, ".gitignore_global"),
            is_symlink=True)
        self.setup_file(conf_gitconf)
        self.setup_file(conf_gitignore)

    def _is_dropbox_setup(self):
        output, error, bash_return_code = OsUtil.subproc_bash("dropbox")
        return output, error, bash_return_code 

    def setup_dropbox(self, skip_install=False):
        """
        @raise RuntimeWarning: When Dropbox setup needs to be done manually.
        @raise RuntimeError: When Dropbox installation seems to have failed.
        """
        o, e, bash_return_code = self._is_dropbox_setup()
        if bash_return_code == 0:
           raise RuntimeWarning("Skipping Dropbox setup as it's already set up.")
        if skip_install:
           raise RuntimeWarning("Skipping Dropbox setup as the user requested to do so.")
        FILENAME_DEB_DROPBOX = "dropbox_2022.12.05_amd64.deb"
        url_deb = f"https://linux.dropbox.com/packages/ubuntu/{FILENAME_DEB_DROPBOX}"
        OsUtil.subproc_bash(f"wget {url_deb} -O /tmp/{FILENAME_DEB_DROPBOX}")
        cmd_install = f"dpkg -i /tmp/{FILENAME_DEB_DROPBOX}"
        OsUtil.subproc_bash(cmd_install, does_sudo=True)

        o, e, bash_return_code = self._is_dropbox_setup()
        if bash_return_code != 0:
            raise RuntimeError(f"Dropbox installation seems to have failed. Error: {e}")

        raise RuntimeWarning("Dropbox: Installation is done. Its setup needs to be done manually.")

    def clone(self, repo_to_clone: str, dir_cloned_at: str, branch=""):
        """
        @return: Absolute path of the successfully cloned local repo.
        @raise ValueError when some input is null
        """
        if not dir_cloned_at:
            raise ValueError(f"Var 'dir_cloned_at' cannot be null.")
        
        _abs_path_local = os.path.join(dir_cloned_at, OsUtil.get_repo_basename_from_url(repo_to_clone))
        if os.path.exists(_abs_path_local):
            self._logger.warning(f"Skppig to git clone '{repo_to_clone}' as a local path '{_abs_path_local}' already exists." \
                                 f"NOTE: This can result in the code of '{repo_to_clone}' may not get updated since the first time it was cloned" \
                                 f"      To avoid that, you may want to manually delete '{_abs_path_local}'")
            return _abs_path_local

        self._logger.info(f"Cloning '{repo_to_clone}' into a local dir: '{dir_cloned_at}' so the abs local path will be '{_abs_path_local}.")
        self.git_clone_impl(repo_to_clone, dir_cloned_at, branch)

        # Verifying if perm conf repo is successfully cloned on the host, by checking to see if the path exists.
        if not os.path.exists(dir_cloned_at):
            raise FileNotFoundError(
                f"At '{dir_cloned_at}', a local repo '{repo_to_clone}' is expected to be present in order to continue.")
        return _abs_path_local

    def _is_docker_setup(self):
        bash_return_code = -1
        _MSG_ERR = "Docker setup is not done yet"
        try:
            output, error, bash_return_code = OsUtil.subproc_bash(f"docker images")
        except AttributeError as e:
            raise RuntimeWarning(f"{_MSG_ERR}. Error occurred while testing docker command: {str(e)}")        
        if bash_return_code == 0:
            self._logger.info("Docker setup skipped as it's already set up.")
        else:
            raise RuntimeWarning(f"{_MSG_ERR}. Status unclear, sorry. {output=} {error=}")
        return bash_return_code

    def _import_git(self):
        """
        @summary: Very adhoc method
          In case `python3-git` module wasn't installed when this program started (so that `import git` failed when this file was read in),
          re-importing Python's `git` module and let Python interpreter recognize the module to be loaded.
          Ref. https://stackoverflow.com/a/19179497/577001
        """
        try:
            importlib.reload(git)
        except NameError as e:
            globals()["git"] = importlib.import_module("git")
            self.add_runtime_issue(e)

    def _git_clone_py(self, repo_to_clone, dir_cloned_at):
        git.Repo.clone_from(repo_to_clone, dir_cloned_at)

    def git_clone_impl(self, repo_to_clone, dir_cloned_at):
        raise NotImplementedError()

    def setup_docker(self, userid_os, skip=False):
        """
        @param skip: Set 'True' when docker is not necessary e.g. running already inside a docker container.
        """
        raise NotImplementedError()

    def generate_symlinks(self, rootpath_symlinks, path_user_home):
        raise NotImplementedError()

    def setup_configs(self, host_config: HostConf, abs_path_confdir: str, abs_path_private_confdir: str):
        raise NotImplementedError()

    def common_symlinks(self, pairs_symlinks: list[ConfigDispatch]):
        for pair in pairs_symlinks:
            self._logger.info(f"ConfigDispatch: {pair}, pairs_symlinks: {pairs_symlinks}")
            try:
                self.setup_file(pair)
            except FileNotFoundError as e:
                _error_msg = f"""Source of symlink '{pair.path_source}' it not (yet) found on the local file system. 
This is most notably ammendable by setting up local client executables of Dropbox and/or Google Drive."""
                if pair.hint_enable:
                    _error_msg += f"\nHint: {pair.hint_enable}"
                self.add_runtime_issue(e)
                self._logger.error(_error_msg)
                if not pair.necessary:
                    continue
                raise e

    def set_os_user_conf(
            self,
            path_local_conf_repo,
            list_conf_files,
            path_user_home_dir,
            path_section_conf_dir):
        """
        @deprecated: Use 'OsUtil.copy_a_file' instead.
        @summary: Setup configuration files under a Linux user's home directory. This method
            should be capable of handling:
            - Copying a file from dir 'a' to 'b'.
            - Creating a config folder, if it does not exist.
            - Creating a symlink if desired, with a custom name if specified.
           Source path | Target path | symlink target (if different from the file/directory name)
        @param path_user_home_dir: E.g. '/home/foo'
        @param path_section_conf_dir: Secton of the path for the config directory under 'path_user_home_dir' E.g. '.config/autostart'
        """
        path_config_dir = os.path.join(path_user_home_dir, path_section_conf_dir)
        if not os.path.exists(path_config_dir):
            os.mkdir(path_config_dir)
        for conf_file in list_conf_files:
            path_file = os.path.join(path_local_conf_repo, conf_file)
            shutil.copyfile(path_file, os.path.join(path_config_dir, conf_file))

    def setup_ros_installer_src(self):
        raise NotImplementedError()

    def setup_rosdep_and_run(self, path_ws, pkg_rosdep="python3-rosdep", init_rosdep=False):
        raise NotImplementedError()

    def install_deps_adhoc(self, deb_pkgs=[], pip_pkgs=[], allow_pip_break=False, snap_pkgs: list[str]=[]):
        """
        @param allow_pip_break: If True, pip runs with '--break-system-packages' option.
        """
        raise NotImplementedError()

    def setup_ssh(self, skip=False, path_local_conf_repo=""):
        """
        @param skip: If True, skip setting up SSH.
        @param path_local_conf_repo: Path to the local configuration repo.
        """
        if skip:
            self._logger.warning("Skipping SSH setup as 'skip' is set to True.")
            return

        # Implement SSH setup logic here
        raise NotImplementedError("SSH setup is not implemented yet.")

    def nonrosdep_deps(self) -> tuple[list[str], list[str]]:
        """
        @return: Tuple of two lists: (list of deb packages, list of pip packages)
        """
        raise NotImplementedError()

    def run(self, host_config: HostConf, conf_repo_remote: str, conf_base_path: str):
        """
        @type host_cfg: HostConf
        @param conf_repo: Absolute path URL of the repo to clone that contains host config.
        @param conf_base_path: Path to a local location conf_repo to be cloned to.
          Default is defined in each OS type class by "_PATH_BASE_CONF" variable.
        """
        self._logger.info("Update the host name as '{}'".format(self._args_in.hostname))

        # Extract repo base name (e.g. 'xyz' from https://github.org/orgorg/xyz.git)
        _repo_basename = OsUtil.get_repo_basename_from_url(conf_repo_remote)
        _abs_path_repo_cloned_into = os.path.join(conf_base_path, _repo_basename)
        _conf_repo_version = self._args_in.conf_repo_version
        self._logger.debug(f"_abs_path_repo_cloned_into: {_abs_path_repo_cloned_into}")
        self.clone(conf_repo_remote, _abs_path_repo_cloned_into, branch=_conf_repo_version)

        if not self._args_in.skip_setup_docker:
            self._logger.warning(f"{self._args_in.skip_setup_docker=}. Setting up Docker with user ID '{self._args_in.user_id}'.")
            try:
                self.setup_docker(userid_os=self._args_in._user_id, skip=self._args_in.skip_setup_docker)
            except AttributeError as e:
                _MSG_E = f"'setup_docker' method is incomplete. Moving on despite the error: {str(e)}"
                self.add_runtime_issue(_MSG_E)

        else:
            self._logger.info(f"Skipping Docker setup as 'skip_setup_docker' is set to True (verify -> {self._args_in.skip_setup_docker}).")

        try:
            self.update_hostname(self._args_in.hostname)
        except NotImplementedError as e:
            self._logger.warning("{}\nIgnore and moving on for now.".format(str(e)))
            self.add_runtime_issue(e)

        self._user_home_dir = pwd.getpwuid(os.getuid()).pw_dir
        self._logger.info(f"""Set home dir of the user at {self._user_home_dir} that will be the main user account on this computer.
            For now the user account that is used to execute this process will be the main account.""")

        # Installation by batch based on the list defined in package.xml.
        self.setup_rosdep_and_run(self._args_in.path_temp_colconws, init_rosdep=True)
        # Install dependency that is not available via rosdep
        _deps, _deps_pip = self.nonrosdep_deps()
        try:
            # TODO In DebianSetup, 'install_deps_adhoc' is already called within 'setup_rosdep_and_run',
            # so this call here might be redundant with no good reason. This needs to be re-think-ed.
            self.install_deps_adhoc(_deps, _deps_pip)
        except RuntimeWarning as e:
            self.add_runtime_issue(e)
        except RuntimeError as e:
            self.add_runtime_issue(e)            

        # This must be implemented for all OSes as the end result is crucial to my computer usage,
        # therefore do NOT catch `NotImplementedError`.
        try:
            self.swap_caps_ctrl()
        except RuntimeError as e:
            self.add_runtime_issue(e)

        _abs_path_confdir = os.path.join(self._args_in.path_local_conf_repo, self._args_in.path_conf_dir)

        self._logger.debug(f"'{_abs_path_confdir=}'")

        self.setup_terminal_configs(_abs_path_confdir)

        try:
            self.setup_ssh(skip=self._args_in.skip_ssh)
        except RuntimeWarning as e:
            self.add_runtime_issue(e)            
        except Exception as e:
            self.add_runtime_issue(e)

        self.setup_git_config(path_local_perm_conf=_abs_path_confdir)

        # Skip Google Chrome specific setting as it might come bundled already on Ubuntu.

        # Skip synergy setting.

        try:
            self.setup_dropbox()
        except RuntimeWarning as e:
            self.add_runtime_issue(e)            
        except Exception as e:
            self.add_runtime_issue(e)

        self.create_data_dir(
            [os.path.join(self._user_home_dir, self._DIR_DROXBOX_CONTAINER),
             os.path.join(self._user_home_dir, self._args_in.path_symlinks_dir)])
        _pairs_symlinks = self.generate_symlinks(
            rootpath_symlinks=os.path.join(self._user_home_dir, self._args_in.path_symlinks_dir),
            path_user_home=self._user_home_dir)
        self.common_symlinks(_pairs_symlinks)

        self.setup_configs(host_config, abs_path_confdir=_abs_path_confdir)

        _msg_endroll = self._args_in.msg_endroll if self._args_in.msg_endroll else "Setup finished."
        self._logger.info(_msg_endroll)

        self.setup_vscode(path_installer=self._args_in.path_vscode_installer)
