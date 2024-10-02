#! /usr/bin/env python3

# Copyright (C) 2023 Kinu Garage
# Licensed under Apache 2

import argparse
try:
    import apt
    import pkg_resources
except ModuleNotFoundError as e:
    print(f"This module isn't available at the moment but will be installed later.\n{str(e)}")
try:
    import git
except ModuleNotFoundError as e:
    print(f"This module isn't available at the moment but will be installed later.\n{str(e)}")
import importlib
import logging
import os
import pathlib
import pwd
import shlex
import shutil
import subprocess
import sys
from datetime import datetime


class HostConf():
    def __init__(self, hostname, bash_cfg, emacs_cfg, sshkey_prv, sshkey_pub):
        self._hostname = hostname
        self._bash_cfg = bash_cfg
        self._emacs_cfg = emacs_cfg
        self._sshkey_prv = sshkey_prv
        self._sshkey_pub = sshkey_pub

    @property
    def hostname(self):
        return self._hostname

    @property
    def bash_cfg(self):
        return self._bash_cfg

    @property
    def emacs_cfg(self):
        return self._emacs_cfg

    @property
    def sshkey_prv(self):
        return self._sshkey_prv

    @property
    def sshkey_pub(self):
        return self._sshkey_pub


class ConfigDispach():
    """Need for the setter of each entry is questionable in the beginning though"""
    def __init__(self, path_source, path_dest=None, is_symlink=False):
        self._path_source = path_source
        self._path_dest = path_dest
        self._is_symlink = is_symlink

    @property
    def path_source(self):
        return self._path_source

    @path_source.setter
    def path_source(self, v):
        self._path_source = v

    @property
    def path_dest(self):
        return self._path_dest

    @path_dest.setter
    def path_dest(self, v):
        self._path_dest = v

    @property
    def is_symlink(self):
        return self._is_symlink

    @is_symlink.setter
    def is_symlink(self, v):
        """Must be absolute path"""
        self._is_symlink = v


class OsUtil:
    """
    @summary: Utility for Operating System handling.
    """
    SUFFIX_BACKUP = ".bk"
    _LOGGER_NAME = "OsUtil-logger"
    def __init__(self, logger=None):
        if logger:
            self._logger = logger
        else:
            self._logger = OsUtil._gen_logger()

    @staticmethod
    def _gen_logger(logger_name=_LOGGER_NAME, log_level=logging.DEBUG):
        logger = logging.getLogger(logger_name)
        log_handler = logging.StreamHandler()        
        logger.setLevel(log_level)
        if not logger.hasHandlers():
            logger.addHandler(log_handler)
        return logger

    @staticmethod
    def setup_rosdep():
        _path_rosdep = shutil.which("rosdep")
        OsUtil.subproc_bash(f"{_path_rosdep} init", does_sudo=True)
        OsUtil.subproc_bash(f"{_path_rosdep} update")
        OsUtil.subproc_bash(f"{shutil.which('apt')} update", does_sudo=True)

    @staticmethod
    def apt_install(deb_pkg_name, logger=None):
        if not logger:
            logger = OsUtil._gen_logger()
        logger.info("Installing by apt: {}".format(deb_pkg_name))
        OsUtil._apt_install_bash(deb_pkg_name, logger)

    @staticmethod
    def _apt_install_bash(deb_pkg_name, logger=None):
        """
        @type deb_pkg_name: [str]
        """
        _path_apt = shutil.which("apt")

        # 'deb_pkg_name' is a list while subprocess takes it literally with square brackets and woudl return an error,
        # so need to expand as a non-list, single string.
        deb_pkg_names_str = " ".join(deb_pkg_name)

        OsUtil.subproc_bash(f"{_path_apt} update", does_sudo=True)
        OsUtil.subproc_bash(f"DEBIAN_FRONTEND=noninteractive {_path_apt} install -y {deb_pkg_names_str}", does_sudo=True)
        # Just to verify, print 'apt-cache policy' output for the 'deb_pkg_names_str'
        OsUtil.subproc_bash(f"{shutil.which('apt-cache')} policy {deb_pkg_names_str}")

    @staticmethod
    def _apt_install_py(deb_pkg_name, logger=None):
        """
        @deprecated: Unsure if this method should be deprecated but it doesn't seem to be used.
        """
        cache = apt.cache.Cache()
        cache.update()
        cache.open()

        pkg = cache[deb_pkg_name]
        if pkg.is_installed:
            logger.info("{pkg_name} already installed".format(pkg_name=deb_pkg_name))
        else:
            pkg.mark_install()

        try:
            cache.commit()
        except SystemError as e:
            logger.error(sys.stderr, "Sorry, package installation failed [{err}]".format(err=str(e)))

    @staticmethod
    def install_pip_adhoc(pip_pkgs=[], logger=None):
        if not logger:
            logger = OsUtil._gen_logger()
        if not pip_pkgs:
            logger.warning(f"No pip pkgs requested to be installed, so skpping. Passed: {pip_pkgs}")
            return
        logger.info(f"List of pip pkgs TO BE installed: {pip_pkgs}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *pip_pkgs])

    @staticmethod
    def copy_prop_file(path_src, path_dest):
        """
        @brief: Python's file copy methods are known to be missing an option
            to copy meta data. This method copies them from a file to another.
        @return: True if copying metadata was successful.
        @raise AssertionError: When either UID / GID / file size / st_dev
            differs b/w src and dest files.
        """
        meta_src = os.stat(path_src)
        os.chown(path_dest, meta_src.st_uid, meta_src.st_gid)

        meta_dest = os.stat(path_dest)
        if (meta_src.st_uid != meta_dest.st_uid) or \
           (meta_src.st_gid != meta_dest.st_gid) or \
           (meta_src.st_dev != meta_dest.st_dev) or \
           (meta_src.st_size != meta_dest.st_size):
            raise AssertionError("Copying meta data failed. Metadata per file:\n\tSrc: {}\n\tDst: {}".format(meta_src, meta_dest))
        else:
            return True

    @staticmethod
    def subproc_bash(
            cmd,
            does_sudo=False,
            print_stdout_err=False,
            logger=None,
            non_interactive=False):
        if not logger:
            logger = OsUtil._gen_logger()  
        if not cmd:
            raise ValueError("Command to execute not passed.")
        
        bash_type = '/bin/sh'
        bash_arg = '-c'
        bash_full_cmd = [bash_type, bash_arg]
        if does_sudo == True:
            bash_full_cmd.insert(0, 'sudo')

        if non_interactive:
            cmd = "DEBIAN_FRONTEND=noninteractive " + cmd
        bash_full_cmd.append(cmd)

        logger.info(f"subprocess: About to execute the cmd: {cmd}")
        _subproc = None
        if print_stdout_err:
            _subproc = subprocess.Popen(bash_full_cmd)
        else:
            while not _subproc:  # TODO Afraid this look could lead an infinite loop.
                try:
                    _subproc = subprocess.Popen(bash_full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except FileNotFoundError as e:
                    del bash_full_cmd[0]
                    logger.warning(f"If 'sudo' is not found on this env, remove that from the command set. New command: {bash_full_cmd}. Retry now.")

        output, error = _subproc.communicate()
        bash_return_code = _subproc.returncode

        if (output or error) is not None:
            try:
                output = output.decode("utf-8").rstrip('\n')
                error = error.decode("utf-8").rstrip('\n')
            except UnicodeDecodeError:
                _ERR_MSG = "Potentially 'UnicodeDecodeError'"
                output = _ERR_MSG
                error = _ERR_MSG
        logger.info(f"output: {output}, error: {error}, bash_return_code: {bash_return_code}")
        return output, error, bash_return_code

    @staticmethod
    def create_parent_dir(path_dest: str, logger=None):
        if not logger:
            logger = OsUtil._gen_logger()         
        path_dir_dest = pathlib.Path(path_dest).parent
        logger.info(f"If the directory of the target for {path_dest} doesn't exist (i.e. {path_dir_dest}), create it.")
        if not os.path.exists(path_dir_dest):
            os.mkdir(path_dir_dest)

    @staticmethod
    def copy_a_file(path_source, path_dest, is_symlink=False, overwrite=False, backup_suffix=".org", logger=None):
        """
        @summary A tool to take the list of conf files, place them at the designated location so that each application can find them.
        @param backup_suffix: Only used when 'overwrite' is True, NOTE if no string is passed, the original dest file will be DELETED.
        @return: True if dest exists after the process.
        @todo Remove dependency on ConfigDispach. This method can be written with just taking str.
        """
        if not logger:
            logger = OsUtil._gen_logger()
        logger.debug("poku.path_dest: {}".format(path_dest))
        # Screening
        if (not overwrite) and pathlib.Path(path_dest).exists():
            raise FileExistsError("'{}' already exists.".format(path_dest))
        if not os.path.exists(path_source):
            raise FileNotFoundError("Source file '{}' not found.".format(path_source))

        # If one direct parent folder for the destination doesn't exist, create one.
        OsUtil.create_parent_dir(path_dest)

        if overwrite:
            if backup_suffix:
                _backup_file_path = os.path.join(path_dest + backup_suffix + "_" + datetime.today().strftime("%Y%m%d-%H%M%S"))
                shutil.copyfile(path_dest, _backup_file_path)
                logger.info(f"File '{path_dest} is backed up at '{_backup_file_path}")
            os.remove(path_dest)
            logger.info(f"File '{path_dest} was deleted without backup per instruction.")

        if is_symlink:
            os.symlink(path_source, path_dest)
            logger.info("Created symlink at {}".format(path_dest))
            return pathlib.Path(path_dest).exists()  # Testing
        else:
            shutil.copyfile(path_source, path_dest)
            logger.info("Moved a file at {}".format(path_dest))
            return pathlib.Path(path_dest).exists()  # Testing

    @staticmethod
    def tilde_to_expand(value_to_scan, logger=None):
        """
        @type value_to_scan: str
        @return: String after tilde-to-absolute path expansion.
        @todo Entire input string is scanned and expanded, which may meet some usecases but other usecases may need something else.
        """
        val_result = value_to_scan
        if not logger:
            logger = OsUtil._gen_logger()
        if (value_to_scan) and (value_to_scan.find("~") != -1):  # When v is not none and contains tilde
            val_result = pathlib.Path(value_to_scan).expanduser()
            logger.info(f"Expanding a path that contains tilde with user ID. BEFORE: '{value_to_scan}', AFTER: {val_result}")
        return val_result

    @staticmethod
    def get_repo_basename_from_url(url: str) -> str:
        """
        @see https://stackoverflow.com/a/55137835/577001
        """
        last_slash_index = url.rfind("/")
        last_suffix_index = url.rfind(".git")
        if last_suffix_index < 0:
            last_suffix_index = len(url)
        if last_slash_index < 0 or last_suffix_index <= last_slash_index:
            raise Exception("Badly formatted url {}".format(url))
        return url[last_slash_index + 1:last_suffix_index]

    @staticmethod
    def which(executable_name: str):
        path = shutil.which(executable_name)
        if not path:
            raise ReferenceError(f"The executable '{executable_name}' not found.")
        return path


class AbstCompSetupFactory():
    """
    @description: Applyig Abstract Factory pattern.
    """
    _DIR_DROXBOX_CONTAINER = "data"  # This is beyond programming, something that sticks with 130s' computer usage for decades.

    def __init__(self, os_name="", args_in: argparse.Namespace=None):
        self._os = os_name
        self.init_logger(logger_name=__name__)
        self._list_runtime_issues = []

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

    def setup_rosdep(self):
        raise NotImplementedError()

    def setup_git_config(self, path_local_perm_conf):
        raise NotImplementedError()

    def setup_dropbox(self):
        raise NotImplementedError()

    def update_hostname(self, hostname):
        raise NotImplementedError("Updating hostname feature is not yet implemented.")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(os_name={self._oos_name})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(os_name={self._oos_name})"

    def run(self, host_config, conf_repo_remote, conf_base_path=""):
        raise NotImplementedError()

    def generate_symlinks(self, rootpath_symlinks, path_user_home=""):
        raise NotImplementedError()


class WindowsSetup(AbstCompSetupFactory):
    def __init__(self, os_name):
        raise NotImplementedError()


class ShellCapableOsSetup(AbstCompSetupFactory):
    """
    @summary: Operating system that is capable of bash, zsh or any *sh shell that meets this tool's requirement.
    """
    def __init__(self, os_name="", args_in: argparse.Namespace=None):
        super().__init__(os_name, args_in)

        self._args_in = args_in
        self._hostname = args_in.hostname
        self._os_user_id = args_in.user_id

        # Python security https://docs.python.org/3.10/library/subprocess.html#popen-constructor
        # for those executables that are (hopefully) available on any shell independent from the type of OS.

        self.get_paths_execs()
        self._setup_git()

    def get_paths_execs(self):
        if not self._args_in.skip_setup_docker:
            # Only when 'skip_setup_docker' is False.
            # self.setup_docker(userid_os=self._os_user_id, skip=args_in.skip_setup_docker)
            self._which_docker = OsUtil.which("docker")

    def _setup_git(self):
        """
        @description:
            Upon implementation, 'self._which_git' must be filled in with the concrete path of the executable of 'git'.
        """
        raise NotImplementedError()

    def swap_file(self, src_file: str, dest_file: str, suffix_backup=".org"):
        """
        @description: Swap 'dest_file' with 'src_file', which can be a symlink. Backup of 'dest_file' will be made alongside the swapped file.
        @param src_file: Absolute path of the source file.
        @param dest_file: Absolute path of the destination file.
        """
        raise NotImplementedError()

    def setup_file(self, file_dispatch: ConfigDispach, overwrite=False):
        try:
            OsUtil.copy_a_file(
                file_dispatch.path_source, file_dispatch.path_dest, is_symlink=file_dispatch.is_symlink, overwrite=overwrite)
        except FileExistsError as e:
            self._logger.warning("Target already exists. Moving on. \n{}".format(str(e)))
        except FileNotFoundError as e:
            self.add_runtime_issue(e)
            self._logger.error(f"Moving on for now despite the error: \n\t{str(e)}")

    def setup_git_config(self, path_local_perm_conf):
        path_user_home = pathlib.Path.home()

        conf_gitconf = ConfigDispach(
            path_source=os.path.join(path_local_perm_conf, "dot_gitconfig"),
            path_dest=os.path.join(path_user_home, ".gitconfig",),
            is_symlink=True)
        conf_gitignore = ConfigDispach(
            path_source=os.path.join(path_local_perm_conf, "dot_gitignore_global"),
            path_dest=os.path.join(path_user_home, ".gitignore_global"),
            is_symlink=True)
        self.setup_file(conf_gitconf)
        self.setup_file(conf_gitignore)

    def setup_dropbox(self):
        output, error, bash_return_code = OsUtil.subproc_bash("dropbox")
        if bash_return_code == 0:
            self._logger.info("Skipping Dropbox setup as it's already set up.")

        FILENAME_DEB_DROPBOX = "dropbox_2022.12.05_amd64.deb"
        url_deb = "https://linux.dropbox.com/packages/ubuntu/{}".format(FILENAME_DEB_DROPBOX)
        os.chdir("/tmp")
        OsUtil.subproc_bash("wget {}".format(url_deb))
        cmd_install = "dpkg -i download?dl=packages%2Fubuntu%2F{}".format(FILENAME_DEB_DROPBOX)
        OsUtil.subproc_bash(cmd_install, does_sudo=True)

    def clone(self, repo_to_clone, dir_cloned_at):
        """
        @raise ValueError when some input is null
        """
        if not dir_cloned_at:
            raise ValueError(f"Var 'dir_cloned_at' cannot be null.")
        
        _abs_path_local = os.path.join(dir_cloned_at, OsUtil.get_repo_basename_from_url(repo_to_clone))
        if os.path.exists(_abs_path_local):
            self._logger.warn(f"Skppig to git clone '{repo_to_clone}' as a local path '{_abs_path_local}' already exists.")

        self._logger.info(f"Cloning '{repo_to_clone}' into a local dir: '{dir_cloned_at}' so the abs local path will be '{_abs_path_local}.")
        self.git_clone_impl(repo_to_clone, dir_cloned_at)

        # Check if perm conf repo is already available on the host.
        if not os.path.exists(dir_cloned_at):
            raise FileNotFoundError(
                f"At '{dir_cloned_at}', a local repo '{repo_to_clone}' is expected to be present in order to continue.")

    def _is_docker_setup(self):
        bash_return_code = -1
        _MSG_ERR = "Docker setup is not done yet"
        try:
            output, error, bash_return_code = OsUtil.subproc_bash(f"{self._which_docker} images")
        except AttributeError as e:
            raise RuntimeWarning(_MSG_ERR)
        if bash_return_code == 0:
            self._logger.info("Docker setup skipped as it's already set up.")
        else:
            raise RuntimeWarning("Docker setup is not done yet")

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

    def setup_configs(self, host_config: HostConf, abs_path_confdir: str):
        raise NotImplementedError()

    def generate_symlinks(self, rootpath_symlinks, path_user_home):
        raise NotImplementedError()

    def common_symlinks(self, pairs_symlinks: list[ConfigDispach]):
        for pair in pairs_symlinks:
            self._logger.info(f"ConfigDispach: {pair}, pairs_symlinks: {pairs_symlinks}")
            try:
                self.setup_file(pair)
            except FileNotFoundError as e:
                self._logger.error(f"""Source of symlink '{pair.path_source}' it not (yet) found on the local file system. 
                                   This is most notably ammendable by setting up local client executables of Dropbox and/or Google Drive. 
                                   Hence skipping for now.""")
                self.add_runtime_issue(e)

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

    def setup_rosdep_and_run(self, path_ws, init_rosdep=False):
        if init_rosdep:
            OsUtil.setup_rosdep()
        os.chdir(path_ws)
        self._logger.info("Changed directory to '{}' to run 'rosdep install' against the manifest that defines dependencies".format(path_ws))
        output, error, bash_return_code = OsUtil.subproc_bash("rosdep install --from-paths . --ignore-src -r -y")
        if bash_return_code != 0:
            self.add_runtime_issue(f"'rosdep install' failed.\n\tOutput: {output}\n\tError: {error}")

    def install_deps_adhoc(self, deb_pkgs=[], pip_pkgs=[]):
        raise NotImplementedError()

    def run(self, args, host_config, conf_repo_remote, conf_base_path):
        """
        @type args: (argparse' output)
        @type host_cfg: HostConf
        @param conf_repo: Absolute path URL of the repo to clone that contains host config.
        @param conf_base_path: Path to a local location conf_repo to be cloned to.
          Default is defined in each OS type class by "_PATH_BASE_CONF" variable.
        """
        self._logger.info("Update the host name as '{}'".format(self._hostname))

        # Extract repo base name (e.g. 'xyz' from https://github.org/orgorg/xyz.git)
        _repo_basename = OsUtil.get_repo_basename_from_url(conf_repo_remote)
        _abs_path_repo_cloned_into = os.path.join(conf_base_path, _repo_basename)
        self._logger.debug(f"_abs_path_repo_cloned_into: {_abs_path_repo_cloned_into}")
        self.clone(conf_repo_remote, _abs_path_repo_cloned_into)

        if self._args_in.skip_setup_docker:
            self.setup_docker(userid_os=self._os_user_id, skip=self._args_in.skip_setup_docker)

        try:
            self.update_hostname(self._hostname)
        except NotImplementedError as e:
            self._logger.warning("{}\nIgnore and moving on for now.".format(str(e)))
            self.add_runtime_issue(e)

        self._logger.info("""Set home dir of the user that will be the main user account on this computer.
            For now the user account that is used to execute this process will be the main account.""")
        self._user_home_dir = pwd.getpwuid(os.getuid()).pw_dir

        # Install deb dependencies that cannot be installed in the batch
        # installation step that is planned later in this sequence.
        self.install_deps_adhoc(deb_pkgs=["python3-pip"], pip_pkgs=["rosdep"])
        OsUtil.setup_rosdep()
        # Installation by batch based on the list defined in package.xml.
        self.setup_rosdep_and_run(args.path_local_conf_repo)

        _abs_path_confdir = os.path.join(args.path_local_conf_repo, args.path_conf_dir)
        self._logger.debug(f"Abs_path_confdir: '{_abs_path_confdir}")
        self.setup_git_config(path_local_perm_conf=_abs_path_confdir)

        # Skip Google Chrome specific setting as it might come bundled already
        # on Ubuntu.

        # Skip synergy setting.

        self.setup_dropbox()

        self.create_data_dir(
            [os.path.join(self._user_home_dir, self._DIR_DROXBOX_CONTAINER),
             os.path.join(self._user_home_dir, args.path_symlinks_dir)])
        _pairs_symlinks = self.generate_symlinks(
            rootpath_symlinks=os.path.join(self._user_home_dir, args.path_symlinks_dir),
            path_user_home=self._user_home_dir)
        self.common_symlinks(_pairs_symlinks)

        self.setup_configs(host_config, abs_path_confdir=_abs_path_confdir)

        _msg_endroll = args.msg_endroll if args.msg_endroll else "Setup finished."
        self._logger.info(_msg_endroll)


class DebianSetup(ShellCapableOsSetup):
    _DEBIAN_DEB_DEPS = [
                "aptitude",
                "colorized-logs",
                "dconf-editor",
                "emacs-mozc", "emacs-mozc-bin",
                "evince",
                "flameshot"
                "gnome-tweaks",
                "googleearth-package",
                "gtk-recordmydesktop",
                "ibus", "ibus-el", "ibus-mozc", 
                "indicator-multiload",
                "libavahi-compat-libdnssd1",
                "mozc-server",
                "pdftk",
                "pidgin",
                "psensor",
                "python-software-properties",  # From http://askubuntu.com/a/55960/24203 primarilly for Oracle Java for Eclipse
                #"python3-rosdep",  # Without ROS' apt source, apt would install python3-rosdep2, which is NOT the officially maintained pkg. See https://discourse.ros.org/t/upstream-packages-increasingly-becoming-a-problem/10902/25
                "ptex-base",
                "ptex-bin",
                "sysinfo",
                "synaptic",
                "xsel",     # https://github.com/kinu-garage/hut_10sqft/issues/1077
                "whois",
                ]
    _OS_TYPE = "Debian"

    def __init__(self, os_name=_OS_TYPE, args_in: argparse.Namespace=None):
        super().__init__(os_name, args_in)
        self._apt_updated = False

        # Python security https://docs.python.org/3.10/library/subprocess.html#popen-constructor
        # for those executables that are likely only available on Debian variants.
        self.get_paths_execs()

    @property
    def apt_updated(self):
        return self._apt_updated

    @apt_updated.setter
    def apt_updated(self, value):
        self._apt_updated = value

    def get_paths_execs(self):
        self._which_apt = shutil.which("apt")
        self._which_aptcache = shutil.which("apt-cache")
        self._which_aptkey = shutil.which("apt-key")
        self._which_echo = shutil.which("echo")
        self._which_service = shutil.which("service")
        self._which_unset = shutil.which("unset")
        
    def install_deps_adhoc(self, deb_pkgs=[], pip_pkgs=[]):
        """
        @summary: Install the packages that cannot be installed by batch using
            'rosdep install'. Example is 'python3-rosdep' itself.
        @param pip_pkgs: Set format. 
        """
        if not deb_pkgs:
            deb_pkgs = self._DEBIAN_DEB_DEPS

        OsUtil.apt_install(deb_pkgs, self._logger)
        self._logger.info(f"pip_pkgs: {pip_pkgs}")
        OsUtil.install_pip_adhoc(pip_pkgs)

    def setup_rosdep(self):
        cmd_set_apt_source_rosdep = f'{self._which_echo} "deb http://packages.ros.org/ros/ubuntu `lsb_release -sc` main" > /etc/apt/sources.list.d/ros-latest.list'
        cmd_obtain_apt_key_rosdep = f"{shutil.which('wget')} http://packages.ros.org/ros.key"
        cmd_set_apt_key_rosdep = f"{self._which_aptkey} add ros.key"
        OsUtil.subproc_bash(cmd_set_apt_source_rosdep, does_sudo=True)
        OsUtil.subproc_bash(cmd_obtain_apt_key_rosdep)
        OsUtil.subproc_bash(cmd_set_apt_key_rosdep, does_sudo=True)

    def create_data_dir(self, dirs_tobe_made):
        self._logger.info("Making directories historically been in use: {}".format(dirs_tobe_made))
        for dir in dirs_tobe_made:
            try:
                os.mkdir(dir)
            except FileExistsError as e:
                self._logger.warning("{}\nIgnore and moving on for now.".format(str(e)))
                self.add_runtime_issue(e)

    def git_clone_impl(self, repo_to_clone, dir_cloned_at):
        OsUtil.subproc_bash(f"{self._which_git} clone {repo_to_clone} {dir_cloned_at}", does_sudo=False, print_stdout_err=True)

    def setup_oracle_java(self):
        self._logger.warning("""The following should be done manually, mainly due to license operation that is hard to automate, in order to set up Oracle Java that is required by Eclipse:

    # Refs:
    # - http://askubuntu.com/a/651045/24203
    # - http://superuser.com/a/939651/106974
    ## sudo add-apt-repository ppa:webupd8team/java
    ## apt update && apt-get install -y oracle-java8-installer
    ## sudo apt install oracle-java8-set-default
""")

    def run(self, args, host_config, conf_repo_remote, conf_base_path=""):
        super().run(args, host_config, conf_repo_remote, conf_base_path)
        self.setup_oracle_java()

    def apt_update(self):
        if self.apt_updated:
            self._logger.warn("'apt update' was already done before. Skipping")
            return
        OsUtil.subproc_bash(f"{self._which_apt} update", does_sudo=True)
        self.apt_updated = True

    def setup_docker(self, userid_os, skip=False):
        try:
            if skip or self._is_docker_setup():
                self._logger.info(f"Looks like Docker setup is already completed.")
                return
        except RuntimeWarning as e:
            self._logger.info(f"Issue found in setting up Docker but continuing docker setup. Source of the error: {str(e)}")
            self.add_runtime_issue(e)

        OsUtil.subproc_bash("groupadd docker", does_sudo=True)
        OsUtil.subproc_bash("usermod -aG docker {}".format(userid_os), does_sudo=True)

        # From https://docs.docker.com/engine/installation/linux/ubuntulinux/
        OsUtil.subproc_bash(f"{self._which_aptkey} adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D", does_sudo=True)
        OsUtil.subproc_bash(f'{self._which_echo} "deb https://apt.dockerproject.org/repo ubuntu-`lsb_release -sc` main" > /etc/apt/sources.list.d/docker.list', does_sudo=True)
        self.apt_update()
        OsUtil.subproc_bash(f"{self._which_apt} purge lxc-docker", does_sudo=True)
        OsUtil.subproc_bash(f"{self._which_aptcache} policy docker-engine")
        OsUtil.subproc_bash(f"{self._which_apt} install linux-image-extra-$(uname -r)", does_sudo=True)
        # Workaround found at http://stackoverflow.com/questions/22957939/how-to-answer-an-apt-get-configuration-change-prompt-on-travis-ci-in-this-case
        OsUtil.subproc_bash(f'{self._which_apt} -q -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confnew" install docker-engine',
                            does_sudo=True, non_interactive=True)
        OsUtil.subproc_bash(f"{self._which_service} docker start", does_sudo=True)
        OsUtil.subproc_bash(f"{self._which_unset} $DEBIAN_FRONTEND")
        OsUtil.subproc_bash(f'{self._which_docker} run hello-world && echo "docker seems to be installed successfully." || (echo "Something went wrong with docker installation."; RESULT=1', does_sudo=True)
    
    def _setup_git(self):
        self.install_deps_adhoc(deb_pkgs=["python3-git"])
        # If git had not been installed yet prior to the one line above,
        # then its executable hadn't been available either.
        self._which_git = shutil.which("git")

    def setup_configs(self, host_config: HostConf, abs_path_confdir: str):
        pairs_conf_autostart = [
            ConfigDispach(
                path_source=os.path.join(abs_path_confdir, "gnome-system-monitor.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".gconf/apps"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(abs_path_confdir, "indicator-multiload.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".config", "autostart"),
                is_symlink=True),
            ]
        for conf in pairs_conf_autostart:
            self.setup_file(conf)

        pairs_conf_bash = [
            ConfigDispach(
                path_source=os.path.join(abs_path_confdir, "bash", host_config.bash_cfg),
                path_dest=os.path.join(self._user_home_dir, ".bashrc"),
                is_symlink=True),
            ]
        for c in pairs_conf_bash:
            self.setup_file(c, overwrite=True)

        pairs_conf_tools = [
            ConfigDispach(
                path_source=os.path.join(abs_path_confdir, "gnome-system-monitor.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".gconf/apps"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(abs_path_confdir, "indicator-multiload.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".gconf/apps"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(abs_path_confdir, "tmux_default.conf"),
                path_dest=os.path.join(self._user_home_dir, ".tmux.conf"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(abs_path_confdir, "emacs", host_config.emacs_cfg),
                path_dest=os.path.join(self._user_home_dir, ".emacs"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(abs_path_confdir, "dot_xbindkeysrc"),
                path_dest=os.path.join(self._user_home_dir, ".xbindkeysrc"),
                is_symlink=True),
            ]
        for c in pairs_conf_tools:
            self.setup_file(c)


class ChromeOsSetup(DebianSetup):
    _OS_TYPE = "ChromeOS"
    def __init__(self, os_name=_OS_TYPE, args_in: argparse.Namespace=None):
        super().__init__(os_name, args_in)

    def setup_dropbox(self):
        self._logger.warn(
            f"Skipping Dropbox setup on {self._OS_TYPE}, as it runs on the Chrome OS host without allowing to mount the directory onto Linux mode.")

    def generate_symlinks(self, rootpath_symlinks, path_user_home=""):
        pairs_symlinks = [
            ConfigDispach(
                path_source=os.path.join(os.path.sep, "mnt" ,"chromeos", "GoogleDrive", "MyDrive"),
                path_dest=os.path.join(rootpath_symlinks, "link", "GoogleDrive"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "link", "GoogleDrive", "30y-130s"),
                path_dest=os.path.join(rootpath_symlinks, "30y-130s"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "link", "GoogleDrive", "Current"),
                path_dest=os.path.join(rootpath_symlinks, "Current"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "link", "GoogleDrive", "Career", "academicDoc"),
                path_dest=os.path.join(rootpath_symlinks, "academicDoc"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "link", "GoogleDrive", "Career", "MOOC"),
                path_dest=os.path.join(rootpath_symlinks, "MOOC"),
                is_symlink=True),
            ]
        self._logger.debug(f"pairs_symlinks: type: {type(pairs_symlinks)}, content: {pairs_symlinks}")
        return pairs_symlinks


class UbuntuOsSetup(DebianSetup):
    _OS_TYPE = "Ubuntu"
    def __init__(self, os_name=_OS_TYPE):
        super().__init__(os_name)
        self.ubuntu_desktop_cleanup()

    def ubuntu_desktop_cleanup(self):
        dirs_tobe_removed = ["Documents", "Music", "Pictures", "Public", "Templates", "Videos"]
        self._logger.warn("Deleting Ubuntu's default directories: {}".format(dirs_tobe_removed))
        for dir in dirs_tobe_removed:
            try:
                shutil.rmtree(dir)
            except FileNotFoundError as e:
                self._logger.warning("File/Dir '{}' does not exist. Moving on without deleting it.".format(dir))
                self.add_runtime_issue(e)

    def generate_symlinks(self, rootpath_symlinks, path_user_home):
        pairs_symlinks = [
            ConfigDispach(
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "GoogleDrive"),
                path_dest=os.path.join(rootpath_symlinks, "GoogleDrive"),
                is_symlink=True),
            ConfigDispach(  # Some others depend on this symlink.
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "GoogleDrive", "30y-130s"),
                path_dest=os.path.join(rootpath_symlinks, "30y-130s"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "pg", "myDevelopment", "git_repo"),
                path_dest=os.path.join(rootpath_symlinks, "git_repos"),
                is_symlink=True),
            ConfigDispach(  # Only backward compatibility
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "pg", "myDevelopment", "git_repo"),
                path_dest=os.path.join(rootpath_symlinks, "github_repos"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "GoogleDrive", "Career", "JobSuchen"),
                path_dest=os.path.join(rootpath_symlinks, "JobSuchen"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "periodic", "2024"),
                path_dest=os.path.join(rootpath_symlinks, "Current"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "GoogleDrive", "Career", "Engineering", "ARIAC"),
                path_dest=os.path.join(rootpath_symlinks, "ARIAC"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "GoogleDrive", "Career", "MOOC"),
                path_dest=os.path.join(rootpath_symlinks, "MOOC"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "Dropbox", "GoogleDrive", "Career", "academicDoc"),
                path_dest=os.path.join(rootpath_symlinks, "academicDoc"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "link", "git_repos", "ROS", "cws_base"),
                path_dest=os.path.join(rootpath_symlinks, "ROS"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "link", "30y-130s", "schools_children", "GJLS"),
                path_dest=os.path.join(rootpath_symlinks, "GJLS"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "link", "git_repos", "ROS", "cws_utakata"),
                path_dest=os.path.join(rootpath_symlinks, "cws_utakata"),
                is_symlink=True),
            ]
        return pairs_symlinks


class MacOsSetup(AbstCompSetupFactory):
    _OS_TYPE = "MacOS"
    def __init__(self, os_name=_OS_TYPE):
        super().__init__(os_name)


class CompInitSetup():
    """
    @summary TBD
    """
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
        parser.add_argument("--os", required=True, help=f"Type of OS. Options: {ChromeOsSetup._OS_TYPE} | {DebianSetup._OS_TYPE} | {UbuntuOsSetup._OS_TYPE}")
        parser.add_argument("--path_base_conf", required=False, help=self._MSG_ARG_BASE_CONF_PATH, default=self._PATH_FOLDER_CONF)
        parser.add_argument("--path_local_conf_repo",
                            help=self._MSG_PATH_PERMCONF_REPO,
                            default=self._PATH_DEFAULT_PERMANENT_CONF_REPO)
        parser.add_argument("--path_conf_dir",
                            help=self._MSG_PATH_CONF_DIR,
                            default=self._PATH_DEFAULT_CONFIG_CONFDIR)
        parser.add_argument("--path_symlinks_dir", required=False, help=self._MSG_ARG_PATH_COMMON_SYMLINKS, default=self._PATH_SYMLINKS_DIR)
        parser.add_argument("--user_id", required=False, help=self._MSG_ARG_USERID, default="")
        parser.add_argument("--skip_setup_docker", required=False, help="Skip docker", action="store_true")

        args = parser.parse_args()
        self._logger.info("args: {}".format(args))

        self._logger.info("If 'user_id' is not passed, get the user id of the current process.")
        if not args.user_id:
            args.user_id = pwd.getpwuid(os.getuid())[0]

        self._logger.info("If 'hostname' is not passed, get the host name from the OS.")
        if not args.hostname:
            args.hostname = os.uname()[1]

        return args

    def main(self):
        _args = self._cli_args()
        # Builder pattern
        _os_builder = None
        if _args.os == ChromeOsSetup._OS_TYPE:
            _os_builder = ChromeOsSetup(args_in=_args)
        elif _args.os == DebianSetup._OS_TYPE:
            _os_builder = DebianSetup(args_in=_args)
        elif _args.os == UbuntuOsSetup._OS_TYPE:
            _os_builder == UbuntuOsSetup(args_in=_args)
        else:
            raise NotImplementedError(f"Chosen OS '{_args.os}' is either not implemented or invalid.")

        # Env vars per host: Bash, Emacs
        _host_cfg = None
        BASH_CONFIG_NAME =  ""
        EMACS_CONFIG_NAME = ""
        if _args.hostname == "130s-p16s":
            _host_cfg = HostConf(_args.hostname, "bashrc_130s-p16s", "emacs_130s-p16s.el", "id_rsa_130s-p16s", "id_rsa_130s-p16s.pub")
        elif _args.hostname == "130s-brya":
            _host_cfg = HostConf(_args.hostname, "130s-brya.bash", "emacs_130s-brya.el", "id_rsa_130s-brya", "id_rsa_130s-brya.pub")
        elif _args.hostname == "130s-C13-Morph":
            _host_cfg = HostConf(_args.hostname, "130s-brya.bash", "emacs_130s-brya.el", "id_rsa_130s-c13-morph", "id_rsa_130s-c13-morph.pub")
        else:
            raise UserWarning(f"user_id: '{_args.hostname}' not matching any host. This needs to be set.")

        # Ref. "_MSG_ARG_BASE_CONF_PATH"
        _conf_base_path = OsUtil.tilde_to_expand(_args.path_base_conf) if _args.path_base_conf else ""
            
        _os_builder.run(_args,
                        _host_cfg,
                        conf_repo_remote=self._URL_CONFREPO,
                        conf_base_path=_conf_base_path)

        _msg_endroll = _args.msg_endroll if _args.msg_endroll else "Setup finished."
        self._logger.info(_msg_endroll)
        _os_builder.listup_runtime_issues()
        

if __name__ == '__main__':
    comp_setup = CompInitSetup()
    comp_setup.main()
