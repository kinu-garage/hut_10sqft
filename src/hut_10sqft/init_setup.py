#! /usr/bin/env python3

# Copyright (C) 2023 Kinu Garage
# Licensed under Apache 2

import apt
import argparse
import logging
import os
import pathlib
import pkg_resources
import pwd
import shlex
import shutil
import subprocess
import sys


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
        OsUtil.subproc_bash("apt update", does_sudo=True)
        OsUtil.subproc_bash("apt install -y {}.format(deb_pkg_name)", does_sudo=True)

    @staticmethod
    def _apt_install_py(deb_pkg_name, logger=None):
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
            print_stdout_err=False):
        bash_type = '/bin/sh'
        bash_arg = '-c'
        bash_full_cmd = [bash_type, bash_arg]
        if does_sudo == True:
            bash_full_cmd.insert(0, 'sudo')

        if bash_extra:
            bash_full_cmd.append(bash_extra)

        if cmd:
            bash_full_cmd.append(cmd)

        _subproc = None
        if print_stdout_err:
            _subproc = subprocess.Popen(bash_full_cmd)
        else:
            _subproc = subprocess.Popen(bash_full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = _subproc.communicate()
        bash_return_code = _subproc.returncode

        if (output or error) is not None:
            try:
                output = output.decode("utf-8").rstrip('\n')
                error = error.decode("utf-8").rstrip('\n')
            except UnicodeDecodeError:
                output = None
                error = None
        return output, error, bash_return_code

    def setup_config_location(self, poku):
        """
        @summary A tool to take the list of conf files, place them at the designated location so that each application can find them.
        @param poku: Type of 'ConfigDispach'
        @return: True if dest exists after the process.
        """
        self._logger.debug("poku.path_dest: {}".format(poku.path_dest))
        if pathlib.Path(poku.path_dest).exists():
            raise FileExistsError("'{}' already exists.".format(poku.path_dest))        
        if not os.path.exists(poku.path_source):
            raise FileNotFoundError("Source file '{}' not found.".format(poku.path_source))

        path_dir_dest = pathlib.Path(poku.path_dest).parent
        self._logger.info("If the directory of the target for {} doesn't exist (i.e. {}), create it".format(poku.path_dest, path_dir_dest))
        if not os.path.exists(path_dir_dest):
            os.mkdir(path_dir_dest)

        if poku.is_symlink:
            os.symlink(poku.path_source, poku.path_dest)
            self._logger.info("Created symlink at {}".format(poku.path_dest))
            return pathlib.Path(poku.path_dest).exists()  # Testing
        else:
            shutil.copyfile(poku.path_source, poku.path_dest)
            self._logger.info("Moved a file at {}".format(poku.path_dest))
            return pathlib.Path(poku.path_dest).exists()  # Testing

class CompInitSetup():
    """
    @summary TBD
    """
    _LOGGER_NAME = "CompInitSetup-logger"
    # Name of the local repo that stores the config and will have to be
    # available for the entire life time of the OS. 
    _REPO_PERMANENT_CONFIG = "hut_10sqft"
    _FOLDER_CONF_PERM_REPO = "config"
    _PATH_DEFAULT_PERMANENT_CONF_REPO = "~/.config/{}".format(_REPO_PERMANENT_CONFIG)
    _PATH_DEFAULT_PERMANENT_CONFIG_CONFDIR = "~/.config/{}/{}".format(_REPO_PERMANENT_CONFIG, _FOLDER_CONF_PERM_REPO)
    _PATH_SYMLINKS_DIR = "link"
    # Messages for stdout
    _MSG_CONSOLE_TOOL_INTRO = """This tool is for setting up a Linux-based personal computer.
     It does the following: 1) Installs dependency (which must be defined in package.xml). 
     2) Create symlinks to config files, which are provided in hut_10sqft local git
       repo i.e. (Having Khut_10sqft somewhere on the host is required)."""
    _MSG_PATH_PERMANENT_CONFIG = "Path to the FINAL location of '{}' local repo. If not passed then the path will be {}.".format(
        _REPO_PERMANENT_CONFIG,
        _PATH_DEFAULT_PERMANENT_CONFIG_CONFDIR)
    _MSG_ARG_USERID = """User ID on the OS that will be mainly used. While this
is optional, it is recommened to specify. If nothing passed, then the tool
treats the user ID tha is used to execute this tool as the main user."""

    def __init__(self):
        self._logger = logging.getLogger(self._LOGGER_NAME)
        log_handler = logging.StreamHandler()
        self._logger.setLevel(logging.DEBUG)  # Needs changed
        self._logger.addHandler(log_handler)
        
        self._os_util = OsUtil(logger=self._logger)

        self._apt_updated = False

    def _apt_update(self):
        if self._apt_updated:
            self._logger.info("'apt update' was already done before. Skipping")
            return
        OsUtil.subproc_bash("apt update", does_sudo=True)
        self._apt_updated = True

    def _cli_args(self):
        parser = argparse.ArgumentParser(description=self._MSG_CONSOLE_TOOL_INTRO)
        # Optional but close to required args
        parser.add_argument("--hostname", help="Specify in case you need to modify the host name.")
        parser.add_argument("--msg_endroll", help="Specify the message string that will be printed at the end in case of need.")
        parser.add_argument("--path_local_conf_repo",
                            help=self._MSG_PATH_PERMANENT_CONFIG,
                            default=self._PATH_DEFAULT_PERMANENT_CONF_REPO)
        parser.add_argument("--user_id", help=self._MSG_ARG_USERID, default="")

        args = parser.parse_args()
        # Check args format
        self._logger.info("args: {}".format(args))
        for arg in vars(args):
            self._logger.info("Printing an arg: {}".format(arg))
            # NOTE: This 'arg' only shows the arg key, not value, so the following check doesn't work.
            if "~" in arg:
                self._logger.warning("Updating an arg's value '{}' by expanding user ID")
                arg = pathlib.Path(arg).expanduser()

        self._logger.info("If 'user_id' is not passed, get the user id of the current process.")
        if not args.user_id:
            args.user_id = pwd.getpwuid(os.getuid())[0]

        self._logger.info("If 'hostname' is not passed, get the host name from the OS.")
        if not args.hostname:
            args.hostname = os.uname()[1]

        return args

    def _install_deps_adhoc(self, deb_pkgs=[], pip_pkgs={}):
        """
        @summary: Install the packages that cannot be installed by batch using
            'rosdep install'. Example is 'python3-rosdep' itself.
        @param pip_pkgs: Set format. 
        """
        #for deb_pkg in deb_pkgs:
        #    OsUtil.apt_install(deb_pkg, self._logger)
        OsUtil._apt_install_bash(deb_pkgs, self._logger)
        OsUtil.install_pip_adhoc(pip_pkgs)

    def setup_file(self, file_dispatch):
        """
        @param file_dispatch: 'ConfigDispatch' obj.
        """
        try:
            self._os_util.setup_config_location(file_dispatch)
        except FileExistsError as e:
            self._logger.warning("Target already exists. Moving on. \n{}".format(str(e)))

    def _setup_rosdep(self):
        cmd_set_apt_source_rosdep = 'echo "deb http://packages.ros.org/ros/ubuntu `lsb_release -sc` main" > /etc/apt/sources.list.d/ros-latest.list'
        cmd_obtain_apt_key_rosdep = "wget http://packages.ros.org/ros.key"
        cmd_set_apt_key_rosdep = "apt-key add ros.key"
        OsUtil.subproc_bash(cmd_set_apt_source_rosdep, does_sudo=True)
        OsUtil.subproc_bash(cmd_obtain_apt_key_rosdep)
        OsUtil.subproc_bash(cmd_set_apt_key_rosdep, does_sudo=True)

    def _setup_git_config(self, path_local_perm_conf):
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

    def _setup_dropbox(self):
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

    def setup_docker(self, userid_ubuntu):
        try:
            self._is_docker_setup()
            return
        except RuntimeWarning as e:
            self._logger.info("{} Continuing docker setup.".format(str(e)))

        OsUtil.subproc_bash("groupadd docker", does_sudo=True)
        OsUtil.subproc_bash("usermod -aG docker {}".format(userid_ubuntu), does_sudo=True)

        # From https://docs.docker.com/engine/installation/linux/ubuntulinux/
        OsUtil.subproc_bash("apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D", does_sudo=True)
        OsUtil.subproc_bash('echo "deb https://apt.dockerproject.org/repo ubuntu-`lsb_release -sc` main" > /etc/apt/sources.list.d/docker.list', does_sudo=True)
        self._apt_update()
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
                path_source=os.path.join(path_user_home, "data", "Dropbox", "GoogleDrive"),
                path_dest=os.path.join(rootpath_symlinks, "GoogleDrive"),
                is_symlink=True),
            ConfigDispach(  # Some others depend on this symlink.
                path_source=os.path.join(path_user_home, "data", "Dropbox", "GoogleDrive", "30y-130s"),
                path_dest=os.path.join(rootpath_symlinks, "30y-130s"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "data", "Dropbox", "pg", "myDevelopment", "git_repo"),
                path_dest=os.path.join(rootpath_symlinks, "git_repos"),
                is_symlink=True),
            ConfigDispach(  # Only backward compatibility
                path_source=os.path.join(path_user_home, "data", "Dropbox", "pg", "myDevelopment", "git_repo"),
                path_dest=os.path.join(rootpath_symlinks, "github_repos"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "data", "Dropbox", "GoogleDrive", "Career", "JobSuchen"),
                path_dest=os.path.join(rootpath_symlinks, "JobSuchen"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "data", "Dropbox", "periodic", "2023"),
                path_dest=os.path.join(rootpath_symlinks, "Current"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "data", "Dropbox", "periodic", "2022"),
                path_dest=os.path.join(rootpath_symlinks, "2022"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "data", "Dropbox", "GoogleDrive", "Career", "Engineering", "ARIAC"),
                path_dest=os.path.join(rootpath_symlinks, "ARIAC"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "data", "Dropbox", "GoogleDrive", "Career", "MOOC"),
                path_dest=os.path.join(rootpath_symlinks, "MOOC"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "data", "Dropbox", "GoogleDrive", "Career", "academicDoc"),
                path_dest=os.path.join(rootpath_symlinks, "academicDoc"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "data", "Dropbox", "pg", "ansible"),
                path_dest=os.path.join(rootpath_symlinks, "ansible_apps"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "link", "git_repos", "ROS", "cws_base"),
                path_dest=os.path.join(rootpath_symlinks, "ROS"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "link", "academicDoc", "article_surveyed", "_robotics_article"),
                path_dest=os.path.join(rootpath_symlinks, "article_robotics-automation"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "link", "30y-130s", "schools_children", "GJLS"),
                path_dest=os.path.join(rootpath_symlinks, "GJLS"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(path_user_home, "link", "git_repos", "ROS", "cws_utakata"),
                path_dest=os.path.join(rootpath_symlinks, "cws_utakata"),
                is_symlink=True)
            ]
        for pair in pairs_symlinks:
            self.setup_file(pair)

    def directory_ubuntu_user(self, user_home_dir):
        dirs_tobe_removed = ["Documents", "Music", "Pictures", "Public", "Templates", "Videos"]
        self._logger.info("Deleting Ubuntu's default directories: {}".format(dirs_tobe_removed))
        for dir in dirs_tobe_removed:
            try:
                shutil.rmtree(dir)
            except FileNotFoundError as e:
                self._logger.warning("File/Dir '{}' does not exist. Moving on without deleting it.".format(dir))

        dirs_tobe_made = ["data", self._PATH_SYMLINKS_DIR]
        self._logger.info("Making directories historically been in use: {}".format(dirs_tobe_made))
        for dir in dirs_tobe_made:
            try:
                os.mkdir(dir)
            except FileExistsError as e:
                self._logger.warning("{}\nIgnore and moving on for now.".format(str(e)))

        self.common_symlinks(user_home_dir, path_dir_symlinks=self._PATH_SYMLINKS_DIR)

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
        
    def _update_hostname(self, hostname):
        raise NotImplementedError("Updating hostname feature is not yet implemented.")

    def setup_rosdep_and_run(self, path_ws, init_rosdep=False):
        if init_rosdep:
            self._os_util.setup_rosdep()
        os.chdir(path_ws)
        self._logger.info("Changed directory to '{}' to run 'rosdep install' against the manifest that defines dependencies".format(path_ws))
        OsUtil.subproc_bash("rosdep install --from-paths . --ignore-src -r -y")

    def setup_oracle_java(self):
        self._logger.warning("""The following should be done manually, mainly due to license operation that is hard to automate, in order to set up Oracle Java that is required by Eclipse:

    # Refs:
    # - http://askubuntu.com/a/651045/24203
    # - http://superuser.com/a/939651/106974
    ## sudo add-apt-repository ppa:webupd8team/java
    ## apt update && apt-get install -y oracle-java8-installer
    ## sudo apt install oracle-java8-set-default
""")

    def main(self):
        _args = self._cli_args()

        self._logger.info("Set a member var of the path of local permanent conf repo.")
        self._path_local_conf_repo = pathlib.Path(_args.path_local_conf_repo).expanduser()
        self._path_local_permanent_conf_repo_confdir = pathlib.Path(os.path.join(self._path_local_conf_repo, self._FOLDER_CONF_PERM_REPO)).expanduser()
        # Check if perm conf repo is already available on the host.
        if not os.path.exists(self._path_local_conf_repo):
            raise FileNotFoundError("At '{}', a local repo {} is expected to be present in order to continue.".format(
                self._path_local_conf_repo,
                self._REPO_PERMANENT_CONFIG))

        self._hostname = _args.hostname
        self._logger.info("Update the host name as '{}'".format(self._hostname))
        try:
            self._update_hostname(self._hostname)
        except NotImplementedError as e:
            self._logger.warning("{}\nIgnore and moving on for now.".format(str(e)))

        self._logger.info("""Set home dir of the user that will be the main user account on this computer.
            For now the user account that is used to execute this process will be the main account.""")
        self._user_home_dir = pwd.getpwuid(os.getuid()).pw_dir

        self._user_id_ubuntu = _args.user_id

        # Install deb dependencies that cannot be installed in the batch
        # installation step that is planned later in this sequence.
        # TODO Hardcoded here is not easy.
        _deb_pkgs = [
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
            "whois",
            ]
        
        _pip_pkgs = {""}
        self._install_deps_adhoc(deb_pkgs=_deb_pkgs, pip_pkgs=_pip_pkgs)

        # Setting up rosdep
        OsUtil.setup_rosdep()

        self._setup_git_config(path_local_perm_conf=self._path_local_permanent_conf_repo_confdir)

        # Skip Google Chrome specific setting as it might come bundled already
        # on Ubuntu.

        # Skip synergy setting.

        # Install Dropbox
        self._setup_dropbox()

        self.setup_docker(userid_ubuntu=self._user_id_ubuntu)

        self.directory_ubuntu_user(self._user_home_dir)

        # Env vars per host: Bash, Emacs
        BASH_CONFIG_NAME =  ""
        EMACS_CONFIG_NAME = ""
        if self._hostname == "130s-p50":
            BASH_CONFIG_NAME = "bashrc_130s-p50"
            EMACS_CONFIG_NAME = "emacs_130s-serval.el"
            SSH_KEY_PRV = "id_rsa_130s-p50"
            SSH_KEY_PUB = "id_rsa_130s-p50.pub"
        elif self._hostname == "130s-p16s":
            BASH_CONFIG_NAME = "bashrc_130s-p16s"
            EMACS_CONFIG_NAME = "emacs_130s-p16s.el"
            SSH_KEY_PRV = "id_rsa_130s-p16s"
            SSH_KEY_PUB = "id_rsa_130s-p16s.pub"
        elif self._hostname == "130s-serval":
            BASH_CONFIG_NAME = "bashrc_130s-serval"
            EMACS_CONFIG_NAME = "emacs_130s-serval.el"
            SSH_KEY_PRV = "id_rsa_130s-serval"
            SSH_KEY_PUB = "id_rsa_130s-serval.pub"
        elif self._hostname == "130s-kudu1":
            BASH_CONFIG_NAME = "bashrc_130s-kudu1"
            EMACS_CONFIG_NAME = "emacs_130s-kudu1.el"
            SSH_KEY_PRV = "id_rsa_130s-kudu1"
            SSH_KEY_PUB = "id_rsa_130s-kudu1.pub"
        else:
            raise UserWarning("user_id: '{}' not matching any host. This needs to be set.".format(self._hostname))

        pairs_conf_autostart = [
            ConfigDispach(
                path_source=os.path.join(self._path_local_permanent_conf_repo_confdir, "gnome-system-monitor.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".gconf/apps"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(self._path_local_permanent_conf_repo_confdir, "indicator-multiload.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".config", "autostart"),
                is_symlink=True),
            ]
        for conf in pairs_conf_autostart:
            self.setup_file(conf)

        pairs_conf_bash = [
            ConfigDispach(
                path_source=os.path.join(self._path_local_permanent_conf_repo_confdir, "bash", BASH_CONFIG_NAME),
                path_dest=os.path.join(self._user_home_dir, ".bashrc"),
                is_symlink=True),
            ]
        for c in pairs_conf_bash:
            self.setup_file(c)

        pairs_conf_tools = [
            ConfigDispach(
                path_source=os.path.join(self._path_local_permanent_conf_repo_confdir, "gnome-system-monitor.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".gconf/apps"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(self._path_local_permanent_conf_repo_confdir, "indicator-multiload.desktop"),
                path_dest=os.path.join(self._user_home_dir, ".gconf/apps"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(self._path_local_permanent_conf_repo_confdir, "tmux_default.conf"),
                path_dest=os.path.join(self._user_home_dir, ".tmux.conf"),
                is_symlink=True),
            ConfigDispach(
                path_source=os.path.join(self._path_local_permanent_conf_repo_confdir, "emacs", EMACS_CONFIG_NAME),
                path_dest=os.path.join(self._user_home_dir, ".emacs"),
                is_symlink=True),
            ]
        for c in pairs_conf_tools:
            self.setup_file(c)

        self.setup_oracle_java()

        # Installation by batch based on the list defined in package.xml.
        self.setup_rosdep_and_run(self._path_local_conf_repo)

        _msg_endroll = _args.msg_endroll if _args.msg_endroll else "Setup finished."
        self._logger.info(_msg_endroll)
        

if __name__ == '__main__':
    comp_setup = CompInitSetup()
    comp_setup.main()
