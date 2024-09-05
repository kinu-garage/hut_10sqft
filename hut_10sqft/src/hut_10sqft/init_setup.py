#! /usr/bin/env python3

# Copyright (C) 2023 Kinu Garage
# Licensed under Apache 2

import argparse
try:
    import apt
    import git
    import pkg_resources
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
    def _gen_logger():
        logger = logging.getLogger(OsUtil._LOGGER_NAME)
        log_handler = logging.StreamHandler()        
        logger.setLevel(logging.DEBUG)
        logger.addHandler(log_handler)
        return logger

    @staticmethod
    def setup_rosdep():
        OsUtil.subproc_bash("rosdep init", does_sudo=True)
        OsUtil.subproc_bash("rosdep update")
        OsUtil.subproc_bash("apt update", does_sudo=True)

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
        # 'deb_pkg_name' is a list while subprocess takes it literally with square brackets and woudl return an error,
        # so need to expand as a non-list, single string.
        deb_pkg_names_str = " ".join(deb_pkg_name)

        OsUtil.subproc_bash("apt update", does_sudo=True)
        OsUtil.subproc_bash(f"apt install -y {deb_pkg_names_str}", does_sudo=True)

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
    def install_pip_adhoc(self, pip_pkgs={}, logger=None):
        if not logger:
            logger = OsUtil._gen_logger()
        if not pip_pkgs:
            logger.info("No pip pkgs requested to be installed, so skpping.")
            return
        installed = {pkg.key for pkg in pkg_resources.working_set}
        logger.info("List of installed pip pkgs: {}\nList of pip pkgs TO BE installed: {}".format(installed, pip_pkgs))
        missing   = pip_pkgs - installed
        if missing:
            # implement pip as a subprocess:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])

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
            bash_extra="",
            print_stdout_err=False,
            logger=None):
        if not logger:
            logger = OsUtil._gen_logger()  
        
        bash_type = '/bin/sh'
        bash_arg = '-c'
        bash_full_cmd = [bash_type, bash_arg]
        if does_sudo == True:
            bash_full_cmd.insert(0, 'sudo')

        if bash_extra:
            bash_full_cmd.append(bash_extra)

        if cmd:
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
                output = None
                error = None
        logger.info(f"output: {output}, error: {error}, bash_return_code: {bash_return_code}")
        return output, error, bash_return_code

    @staticmethod
    def setup_config_location(poku, logger=None):
        """
        @summary A tool to take the list of conf files, place them at the designated location so that each application can find them.
        @param poku: Type of 'ConfigDispach'
        @return: True if dest exists after the process.
        """
        if not logger:
            logger = OsUtil._gen_logger()        
        logger.debug("poku.path_dest: {}".format(poku.path_dest))
        if pathlib.Path(poku.path_dest).exists():
            raise FileExistsError("'{}' already exists.".format(poku.path_dest))        
        if not os.path.exists(poku.path_source):
            raise FileNotFoundError("Source file '{}' not found.".format(poku.path_source))

        path_dir_dest = pathlib.Path(poku.path_dest).parent
        logger.info("If the directory of the target for {} doesn't exist (i.e. {}), create it".format(poku.path_dest, path_dir_dest))
        if not os.path.exists(path_dir_dest):
            os.mkdir(path_dir_dest)

        if poku.is_symlink:
            os.symlink(poku.path_source, poku.path_dest)
            logger.info("Created symlink at {}".format(poku.path_dest))
            return pathlib.Path(poku.path_dest).exists()  # Testing
        else:
            shutil.copyfile(poku.path_source, poku.path_dest)
            logger.info("Moved a file at {}".format(poku.path_dest))
            return pathlib.Path(poku.path_dest).exists()  # Testing

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


class AbstCompSetupFactory():
    """
    @description: Applyig Abstract Factory pattern.
    """
    _DIR_DROXBOX_CONTAINER = "data"  # This is beyond programming, something that sticks with 130s' computer usage for decades.

    def __init__(self, os_name=""):
        self._os = os_name
        self.init_logger(logger_name=__name__)
        self._list_runtime_issues = []

    @property
    def list_runtime_issues(self):
        return self._list_runtime_issues

    def add_runtime_issue(self, value):
        """
        @param value: Although the type of this not strictly enforced, recommended to be Exption type.
        """
        self._list_runtime_issues.append(value)

    def listup_runtime_issues(self):
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

    def install_deps_adhoc(self, deb_pkgs=[]):
        raise NotImplementedError()

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


class WindowsSetup(AbstCompSetupFactory):
    def __init__(self, os_name):
        raise NotImplementedError()


class ShellCapableOsSetup(AbstCompSetupFactory):
    """
    @summary: Operating system that is capable of bash, zsh or any *sh shell that meets this tool's requirement.
    """
    def __init__(self, os_name):
        super().__init__(os_name)

    def setup_file(self, file_dispatch):
        """
        @param file_dispatch: 'ConfigDispatch' obj.
        """
        try:
            OsUtil.setup_config_location(file_dispatch)
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

    def _is_docker_setup(self):
        output, error, bash_return_code = OsUtil.subproc_bash("docker images")
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

    def clone(self, repo_to_clone, dir_cloned_at):
        """
        @raise ValueError when some input is null
        """
        if not dir_cloned_at:
            raise ValueError(f"Var 'dir_cloned_at' cannot be null.")
        _abs_path_local = os.path.join(dir_cloned_at, OsUtil.get_repo_basename_from_url(repo_to_clone))
        if os.path.exists(_abs_path_local):
            self._logger.info(f"Skppig to git clone '{repo_to_clone}' as a local path '{_abs_path_local}' already exists.")

        self._logger.info(f"Cloning '{repo_to_clone}' into a local dir: '{dir_cloned_at}' so the abs local path will be '{_abs_path_local}.")
        self._import_git()
        git.Repo.clone_from(repo_to_clone, dir_cloned_at)

        # Check if perm conf repo is already available on the host.
        if not os.path.exists(dir_cloned_at):
            raise FileNotFoundError(
                f"At '{dir_cloned_at}', a local repo '{repo_to_clone}' is expected to be present in order to continue.")

    def setup_docker(self, userid_ubuntu):
        try:
            self._is_docker_setup()
            return
        except RuntimeWarning as e:
            self._logger.info("{} Continuing docker setup.".format(str(e)))
            self.add_runtime_issue(e)

        OsUtil.subproc_bash("groupadd docker", does_sudo=True)
        OsUtil.subproc_bash("usermod -aG docker {}".format(userid_ubuntu), does_sudo=True)

        # From https://docs.docker.com/engine/installation/linux/ubuntulinux/
        OsUtil.subproc_bash("apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D", does_sudo=True)
        OsUtil.subproc_bash('echo "deb https://apt.dockerproject.org/repo ubuntu-`lsb_release -sc` main" > /etc/apt/sources.list.d/docker.list', does_sudo=True)
        self.apt_update()
        OsUtil.subproc_bash("apt purge lxc-docker", does_sudo=True)
        OsUtil.subproc_bash("apt-cache policy docker-engine")
        OsUtil.subproc_bash("apt install linux-image-extra-$(uname -r)", does_sudo=True)
        # Workaround found at http://stackoverflow.com/questions/22957939/how-to-answer-an-apt-get-configuration-change-prompt-on-travis-ci-in-this-case
        OsUtil.subproc_bash('DEBIAN_FRONTEND=noninteractive apt-get -q -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confnew" install docker-engine', does_sudo=True)
        OsUtil.subproc_bash("service docker start", does_sudo=True)
        OsUtil.subproc_bash("unset $DEBIAN_FRONTEND")
        OsUtil.subproc_bash('docker run hello-world && echo "docker seems to be installed successfully." || (echo "Something went wrong with docker installation."; RESULT=1', does_sudo=True)


    def common_symlinks(self, path_user_home, path_dir_symlinks):
        rootpath_symlinks = os.path.join(path_user_home, path_dir_symlinks)
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
                path_source=os.path.join(path_user_home, self._DIR_DROXBOX_CONTAINER, "git_repos", "ROS", "cws_base"),
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
        for pair in pairs_symlinks:
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
        @deprecated: Use 'OsUtil.setup_config_location' instead.
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
        OsUtil.subproc_bash("rosdep install --from-paths . --ignore-src -r -y")


class DebianSetup(ShellCapableOsSetup):
    _OS_TYPE = "Debian"

    def __init__(self, os_name=_OS_TYPE):
        super().__init__(os_name)
        self._path_base_conf = os.path.join(pathlib.Path.home(), ".config")
        self._apt_updated = False

    @property
    def apt_updated(self):
        return self._apt_updated

    @apt_updated.setter
    def apt_updated(self, value):
        self._apt_updated = value

    @property
    def path_base_conf(self):
        return self._path_base_conf

    @path_base_conf.setter
    def path_base_conf(self, value):
        self._path_base_conf = value

    def install_deps_adhoc(self, deb_pkgs=[], pip_pkgs={}):
        """
        @summary: Install the packages that cannot be installed by batch using
            'rosdep install'. Example is 'python3-rosdep' itself.

        @param pip_pkgs: Set format. 
        """
        #for deb_pkg in deb_pkgs:
        #    OsUtil.apt_install(deb_pkg, self._logger)
        if not deb_pkgs:
            deb_pkgs = [
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
                "python3-pip",
                "python3-rosdep", 
                "ptex-base",
                "ptex-bin",
                "sysinfo",
                "synaptic",
                "xdotool",  # https://github.com/kinu-garage/hut_10sqft/issues/1077
                "xsel",     # https://github.com/kinu-garage/hut_10sqft/issues/1077
                "whois",
                ]

        OsUtil.apt_install(deb_pkgs, self._logger)
        OsUtil.install_pip_adhoc(pip_pkgs)

    def setup_rosdep(self):
        cmd_set_apt_source_rosdep = 'echo "deb http://packages.ros.org/ros/ubuntu `lsb_release -sc` main" > /etc/apt/sources.list.d/ros-latest.list'
        cmd_obtain_apt_key_rosdep = "wget http://packages.ros.org/ros.key"
        cmd_set_apt_key_rosdep = "apt-key add ros.key"
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

    def setup_oracle_java(self):
        self._logger.warning("""The following should be done manually, mainly due to license operation that is hard to automate, in order to set up Oracle Java that is required by Eclipse:

    # Refs:
    # - http://askubuntu.com/a/651045/24203
    # - http://superuser.com/a/939651/106974
    ## sudo add-apt-repository ppa:webupd8team/java
    ## apt update && apt-get install -y oracle-java8-installer
    ## sudo apt install oracle-java8-set-default
""")

    def apt_update(self):
        if self.apt_updated:
            self._logger.info("'apt update' was already done before. Skipping")
            return
        OsUtil.subproc_bash("apt update", does_sudo=True)
        self.apt_updated = True

    def run(self, args, host_config, conf_repo_remote, conf_base_path=path_base_conf):
        """
        @type args: (argparse' output)
        @type host_cfg: HostConf
        @param conf_repo: Absolute path URL of the repo to clone that contains host config.
        @param conf_base_path: Path to a local location conf_repo to be cloned to.
          Default is defined in each OS type class by "_PATH_BASE_CONF" variable.
        """
        self._hostname = args.hostname
        self._logger.info("Update the host name as '{}'".format(self._hostname))

        # Git clone
        # This section relies on Python implementation of git, which might not be available at this point,
        # so installing manually here.
        self.install_deps_adhoc(deb_pkgs=["python3-git"])
        self._import_git()
        # Extract repo base name (e.g. 'xyz' from https://github.org/orgorg/xyz.git)
        _repo_basename = OsUtil.get_repo_basename_from_url(conf_repo_remote)
        _abs_path_repo_cloned_into = os.path.join(conf_base_path, _repo_basename)
        self._logger.info(f"_abs_path_repo_cloned_into: {_abs_path_repo_cloned_into}")
        self.clone(conf_repo_remote, _abs_path_repo_cloned_into)

        try:
            self.update_hostname(self._hostname)
        except NotImplementedError as e:
            self._logger.warning("{}\nIgnore and moving on for now.".format(str(e)))
            self.add_runtime_issue(e)

        self._logger.info("""Set home dir of the user that will be the main user account on this computer.
            For now the user account that is used to execute this process will be the main account.""")
        self._user_home_dir = pwd.getpwuid(os.getuid()).pw_dir
        self._os_user_id = args.user_id

        # Install deb dependencies that cannot be installed in the batch
        # installation step that is planned later in this sequence.
        self.install_deps_adhoc(deb_pkgs=[], pip_pkgs=[])

        # Setting up rosdep
        OsUtil.setup_rosdep()

        _abs_path_confdir = os.path.join(args.path_local_conf_repo, args.path_conf_dir)
        self._logger.info(f"Abs_path_confdir: '{_abs_path_confdir}")
        self.setup_git_config(path_local_perm_conf=_abs_path_confdir)

        # Skip Google Chrome specific setting as it might come bundled already
        # on Ubuntu.

        # Skip synergy setting.

        self.setup_dropbox()

        self.setup_docker(userid_ubuntu=self._os_user_id)

        self.create_data_dir([self._DIR_DROXBOX_CONTAINER, args.path_symlinks_dir])
        self.common_symlinks(self._user_home_dir, path_dir_symlinks=args.path_symlinks_dir)

        pairs_conf_autostart = [
            ConfigDispach(
                path_source=os.path.join(_abs_path_confdir, "gnome-system-monitor.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".gconf/apps"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(_abs_path_confdir, "indicator-multiload.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".config", "autostart"),
                is_symlink=True),
            ]
        for conf in pairs_conf_autostart:
            self.setup_file(conf)

        pairs_conf_bash = [
            ConfigDispach(
                path_source=os.path.join(_abs_path_confdir, "bash", host_config.bash_cfg),
                path_dest=os.path.join(self._user_home_dir, ".bashrc"),
                is_symlink=True),
            ]
        for c in pairs_conf_bash:
            self.setup_file(c)

        pairs_conf_tools = [
            ConfigDispach(
                path_source=os.path.join(_abs_path_confdir, "gnome-system-monitor.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".gconf/apps"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(_abs_path_confdir, "indicator-multiload.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".gconf/apps"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(_abs_path_confdir, "tmux_default.conf"),
                path_dest=os.path.join(self._user_home_dir, ".tmux.conf"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(_abs_path_confdir, "emacs", host_config.emacs_cfg),
                path_dest=os.path.join(self._user_home_dir, ".emacs"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(_abs_path_confdir, "dot_xbindkeysrc"),
                path_dest=os.path.join(self._user_home_dir, ".xbindkeysrc"),
                is_symlink=True),
            ]
        for c in pairs_conf_tools:
            self.setup_file(c)

        # Installation by batch based on the list defined in package.xml.
        self.setup_rosdep_and_run(args.path_local_conf_repo)

        _msg_endroll = args.msg_endroll if args.msg_endroll else "Setup finished."
        self._logger.info(_msg_endroll)
        for c in pairs_conf_tools:
            self.setup_file(c)

        self.setup_oracle_java()
        self.listup_runtime_issues()


class ChromeOsSetup(DebianSetup):
    _OS_TYPE = "ChromeOS"
    def __init__(self, os_name=_OS_TYPE):
        super().__init__(os_name)

    def setup_dropbox(self):
        self._logger.warn(
            f"Skipping Dropbox setup on {self._OS_TYPE}, as it runs on the Chrome OS host without allowing to mount the directory onto Linux mode.")


class UbuntuOsSetup(DebianSetup):
    _OS_TYPE = "Ubuntu"
    def __init__(self, os_name=_OS_TYPE):
        super().__init__(os_name)
        self.ubuntu_desktop_cleanup()

    def ubuntu_desktop_cleanup(self):
        dirs_tobe_removed = ["Documents", "Music", "Pictures", "Public", "Templates", "Videos"]
        self._logger.info("Deleting Ubuntu's default directories: {}".format(dirs_tobe_removed))
        for dir in dirs_tobe_removed:
            try:
                shutil.rmtree(dir)
            except FileNotFoundError as e:
                self._logger.warning("File/Dir '{}' does not exist. Moving on without deleting it.".format(dir))
                self.add_runtime_issue(e)


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
            _os_builder = ChromeOsSetup()
        elif _args.os == DebianSetup._OS_TYPE:
            _os_builder = DebianSetup()
        elif _args.os == UbuntuOsSetup._OS_TYPE:
            _os_builder == UbuntuOsSetup
        else:
            raise NotImplementedError(f"Chosen OS '{_args.os}' is either not implemented or invalid.")

        # Env vars per host: Bash, Emacs
        _host_cfg = None
        BASH_CONFIG_NAME =  ""
        EMACS_CONFIG_NAME = ""
        if _args.hostname == "130s-p16s":
            _host_cfg = HostConf(_args.hostname, "bashrc_130s-p16s", "emacs_130s-p16s.el", "id_rsa_130s-p16s", "id_rsa_130s-p16s.pub")
        elif _args.hostname == "130s-brya":
            _host_cfg = HostConf(_args.hostname, "bashrc_130s-brya", "emacs_130s-brya.el", "id_rsa_130s-brya", "id_rsa_130s-brya.pub")
        elif _args.hostname == "130s-C14-Morph":
            _host_cfg = HostConf(_args.hostname, "bashrc_130s-brya", "emacs_130s-brya.el", "id_rsa_130s-c14-morph", "id_rsa_130s-c14-morph.pub")
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
        

if __name__ == '__main__':
    comp_setup = CompInitSetup()
    comp_setup.main()
