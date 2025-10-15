#! /usr/bin/env python3

# Copyright (C) 2025 Kinu Garage
# Licensed under Apache 2

try:
    import apt
except ModuleNotFoundError as e:
    print(f"This module isn't available at the moment but will be installed later.\n{str(e)}")
import ast
from datetime import datetime
import logging
import os
import pathlib
import platform
import re
import shutil
import socket
import subprocess
import sys
from typing import Dict, List


class OsUtil:
    """
    @summary: Utility for Operating System handling.
    """
    SUFFIX_BACKUP = ".bk"
    _LOGGER_NAME = "OsUtil-logger"
    _MSG_EXEC_NOT_FOUND = "Cannot find '{}' executable."

    ERRORCOCDE_APTCACHE_NOCANDIDATE = -1001
    ERRORCOCDE_APTCACHE_CANDIDATE_NOTINSTALLED = -1002

    TYPE_OS_CHROMEOS = "ChromeOS"
    TYPE_OS_LINUX = "Linux"
    TYPE_OS_MACOS = "MacOS"
    TYPE_OS_MACOS_DARWIN = "Darwin"
    TYPE_LINUX_DISTRO_DEBIAN = "Debian"
    TYPE_LINUX_DISTRO_UBUNTU = "Ubuntu"

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
        OsUtil.subproc_bash(f"rosdep init", does_sudo=True)
        OsUtil.subproc_bash(f"rosdep update")
        OsUtil.subproc_bash(f"apt update", does_sudo=True)

    @staticmethod
    def apt_install(deb_pkg_names: list[str], logger=None):
        """
        @exception LookupError: If 'apt' executable is not found on the OS.
        """
        if not logger:
            logger = OsUtil._gen_logger()
        logger.info(f"Installing by apt: {deb_pkg_names}")
        OsUtil._apt_install_bash(deb_pkg_names, logger)

    @staticmethod
    def _apt_cache_policy(debpkg_name: str, logger=None):
        """
        @rtype: str, str, int
        @return: This method returns 3 things and by default they are what Python's subprocess returns. However, when the following conditions are met, this method might overwrite 'error' and ret_code' before returning.
          - When a candidate for 'debpkg_name' not found, ret_code = -1001
          - When a candidate found but not found installed, ret_code = -1002
        """
        output, error, ret_code = OsUtil.subproc_bash(f"apt-cache policy {debpkg_name}")
        if not output:
            ret_code = OsUtil.ERRORCOCDE_APTCACHE_NOCANDIDATE
            error = f"'{debpkg_name}' is not found on this OS, even as an install candidate. Check if it is really available."
        elif f"{debpkg_name}:\n  Installed: (none)" in output:
            ret_code = OsUtil.ERRORCOCDE_APTCACHE_CANDIDATE_NOTINSTALLED
            error = f"The install candidate of the pkg '{debpkg_name}' found on this OS, but 'apt-cache policy' didn't find it installed."
        return output, error, ret_code

    @staticmethod
    def apt_cache_policy(debpkg_names: list[str], logger=None):
        """
        @brief: Prints the apt-cache policy for the given deb package names.
        @param debpkg_names: List of deb package names to check.
        @exception RuntimeWarning: When one or more pkgs found not installed.
        """
        if not logger:
            logger = OsUtil._gen_logger()
        if not debpkg_names:
            raise ValueError("No deb package names passed to 'apt_cache_policy' method.")
        if (type(debpkg_names) is not list):
            debpkg_names = OsUtil._encapsulate_if_string(debpkg_names)
        if " " in debpkg_names:
            raise ValueError(f"Space found in the input that is supposed to be a list of pkg names: {debpkg_names}")

        errors = []
        pkgs_success = []
        for pkg_name in debpkg_names:
            output, error, ret_code = OsUtil._apt_cache_policy(pkg_name)
            if ret_code != 0:
                errors.append(f"Failed to get apt-cache policy for '{pkg_name}'. Error: {error}")
            else:
                logger.info(f"'apt-cache policy' result for '{pkg_name}':\n\t{output}")
        _msg_result_header = f"Report: Package installation status:\n"
        _msg_result_header_success = f"- Packages found installed: {pkgs_success}"
        _msg_all = f"{_msg_result_header}\n{_msg_result_header_success}"
        if errors:
            _str_errors = ""
            for error in errors:
                _str_errors += "\t- " + error + "\n"
            raise RuntimeWarning(f"{_msg_all}\n- The following pkgs didn't get installed:\n {_str_errors}")
        return _msg_all

    @staticmethod
    def _encapsulate_if_string(var) -> List[str]:
        """
        @summary: If 'var' is a string, encapsulate it in a list.
        """
        if (type(var) is str) and (" " not in var):
            var = [var]
        return var

    @staticmethod
    def _apt_install_bash(deb_pkgs_name: list[str], logger=None):
        if (type(deb_pkgs_name) is not list):
            deb_pkgs_name = OsUtil._encapsulate_if_string(deb_pkgs_name)

        # 'deb_pkgs_name' is a list of strings, while subprocess takes an input literally
        # so if a list is spplied then it'd take square brackets and would return an error.
        # Thus need to expand as a non-list, single string.
        deb_pkg_names_str = " ".join(deb_pkgs_name)

        OsUtil.subproc_bash(f"apt update", does_sudo=True)
        OsUtil.subproc_bash(f"apt install -y {deb_pkg_names_str}", does_sudo=True, non_interactive=True)
        # Just to verify, print 'apt-cache policy' output for the 'deb_pkg_names_str'.
        OsUtil.apt_cache_policy(deb_pkgs_name)

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
    def install_pip_adhoc(pip_pkgs=[], logger=None, allow_break=False):
        """
        @param allow_break: If True, `pip` runs with '--break-system-packages' option.
        """
        if not logger:
            logger = OsUtil._gen_logger()
        if not pip_pkgs:
            logger.warning(f"No pip pkgs requested to be installed, so skpping. Passed: {pip_pkgs}")
            return
        _PIP_OPTION_BREAK = "--break-system-packages"
        cmd_list = ['pip', 'install', *pip_pkgs]
        
        if allow_break:
            cmd_list.append(_PIP_OPTION_BREAK)
            _msg = f"Cmd: {cmd_list}."            
            _msg = _msg + " See https://stackoverflow.com/questions/75602063 for the risk of passing '--break-system-packages' option."
        else:
            _msg = f"Cmd: {cmd_list}."
        logger.info(_msg)
        _attempts = 0
        _ret_code = -1
        while (not _ret_code) and (_attempts < 3):
            try:
                _ret_code = subprocess.check_call(cmd_list)
            except subprocess.CalledProcessError as e:
                _err_msg = f"{_attempts}-th 'pip install' attempt failed. Often network issue. Re-trying. Error: {str(e)}"
                if allow_break:
                    _err_msg += f"\n\tAnother possible reason is 'pip' is too old so that an option {_PIP_OPTION_BREAK} is not available (see https://stackoverflow.com/a/78600962/577001). Re-trying without that."
                    cmd_list.pop()  # Popping the last element is not super robust way to get rid of '_PIP_OPTION_BREAK'...
                logger.error(_err_msg)

            _attempts += 1        

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

        bash_full_cmd.append(cmd)
        _env = os.environ.copy()
        if non_interactive:
            _env["DEBIAN_FRONTEND"] = "noninteractive"

        logger.info(f"subprocess: About to execute the cmd: {bash_full_cmd}")
        _subproc = None
        if print_stdout_err:
            _subproc = subprocess.Popen(bash_full_cmd, env=_env)
        else:
            while not _subproc:  # TODO Afraid this look could lead an infinite loop.
                try:
                    _subproc = subprocess.Popen(bash_full_cmd, env=_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except FileNotFoundError as e:
                    # Remove 'sudo' from the command set and retry.
                    if 'sudo' in bash_full_cmd:
                        bash_full_cmd.remove('sudo')
                        logger.warning(f"If 'sudo' is not found on this env, remove that from the command set. \
                                   New command: {bash_full_cmd}. Retry now.")
                    else:
                        raise RuntimeError(f"'sudo' not found on this env but removing that didn't help. Error: {str(e)}")

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
        logger.info(f"{bash_return_code=}, {output=}, {error=}")
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
    def copy_a_file(path_source: str, path_dest: str, is_symlink=False, overwrite=False, backup_suffix=".org", logger=None):
        """
        @summary A tool to take the list of conf files, place them at the designated location so that each application can find them.
        @param backup_suffix: Only used when 'overwrite' is True, NOTE if no string is passed, the original dest file will be DELETED.
        @return: 
        - True if dest exists after the process.
        - Timestamp of the file copied.
        @todo Remove dependency on ConfigDispatch. This method can be written with just taking str.
        @raise FileExistsError: When 'overwrite' is False and the destination file already exists.
        @raise FileNotFoundError: When a file at 'path_source' does not exist.
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

        _timestamp = datetime.today().strftime("%Y%m%d-%H%M%S")
        if overwrite:
            if backup_suffix:
                _backup_file_path = os.path.join(path_dest + "_" + _timestamp + backup_suffix)
                shutil.copyfile(path_dest, _backup_file_path)
                logger.info(f"File '{path_dest}' is backed up at '{_backup_file_path}'")
            os.remove(path_dest)
            logger.info(f"File '{path_dest} was deleted without backup per instruction.")

        if is_symlink:
            os.symlink(path_source, path_dest)
            logger.info("Created symlink at {}".format(path_dest))
        else:
            shutil.copyfile(path_source, path_dest)
            logger.info("Moved a file at {}".format(path_dest))

        return pathlib.Path(path_dest).exists(), _timestamp

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
    def which(executable_name: str, throw_exception=False) -> str:
        """
        @return: None when `throw_exception` is False AND the path to `executable_name` is not found.
        @raise ReferenceError: When `executable_name` not available, only when `throw_exception` is True.
        """
        path = shutil.which(executable_name)
        if (not path) and throw_exception:
            raise ReferenceError(f"The executable '{executable_name}' not found.")
        return path

    @staticmethod
    def get_os_type(logger=None) -> tuple[str, str]:
        _FILEPATH_OS_RELEASE = "/etc/os-release"
        _FILEPATH_LSB_RELEASE = "/etc/lsb-release"
        _type_os = ""
        _type_distro = "None"
        if not logger:
            logger = OsUtil._gen_logger()
        if platform.system() == OsUtil.TYPE_OS_LINUX:
            _type_os = OsUtil.TYPE_OS_LINUX
            try:
                with open(_FILEPATH_OS_RELEASE, "r") as f:
                    content = f.read()
                    if f"ID={OsUtil.TYPE_LINUX_DISTRO_DEBIAN.lower()}" in content or f"ID_LIKE={OsUtil.TYPE_LINUX_DISTRO_DEBIAN.lower()}" in content:
                        _type_distro = OsUtil.TYPE_LINUX_DISTRO_DEBIAN
                    elif f"ID={OsUtil.TYPE_LINUX_DISTRO_UBUNTU.lower()}" in content or f"ID_LIKE={OsUtil.TYPE_LINUX_DISTRO_UBUNTU.lower()}" in content:
                        _type_distro = OsUtil.TYPE_LINUX_DISTRO_UBUNTU
                    else:
                        raise RuntimeError(f"Running on another Linux distribution SUCO does not support. Content of {_FILEPATH_OS_RELEASE}: {content}")
            except FileNotFoundError as e:
                try:
                    with open(_FILEPATH_LSB_RELEASE, "r") as f:
                        content = f.read()
                        if f"DISTRIB_ID={OsUtil.TYPE_LINUX_DISTRO_DEBIAN}" in content:
                            _type_distro = OsUtil.TYPE_LINUX_DISTRO_DEBIAN
                        elif f"DISTRIB_ID={OsUtil.TYPE_LINUX_DISTRO_UBUNTU}" in content:
                            _type_distro = OsUtil.TYPE_LINUX_DISTRO_UBUNTU
                        else:
                            raise RuntimeError(f"Running on another Linux distribution SUCO does not support. Content of {_FILEPATH_LSB_RELEASE}: {content}")
                except FileNotFoundError:
                    raise RuntimeError(f"Could not determine the Linux distribution type. Neither '{_FILEPATH_OS_RELEASE}' nor '{_FILEPATH_LSB_RELEASE}' found.")
        elif (platform.system() == OsUtil.TYPE_OS_MACOS) or (platform.system() == OsUtil.TYPE_OS_MACOS_DARWIN):
            _type_os = OsUtil.TYPE_OS_MACOS
        if not _type_os:
            raise RuntimeError(f"OS type undetected or unsupported type found: '{platform.system()}'")
        return _type_os, _type_distro

    @staticmethod
    def is_ssh_server(host='127.0.0.1', port=22, timeout=1):
        """
        @summary: Checks if an SSH server is running on the specified host and port.
        @raise RuntimeError: When server is not confirmed to be running.
        """
        try:
            with socket.create_connection((host, port), timeout=timeout) as sock:
                # If the connection is successful, the server is likely running
                # You could add further checks here, like reading a banner
                return True
        except (socket.timeout, ConnectionRefusedError) as e:
            raise RuntimeError(f"An error regarding socket occurred while verifying ssh server operation: {e}")
        except Exception as e:
            raise RuntimeError(f"An error occurred while verifying ssh server operation: {e}")

    @staticmethod
    def read_conf(path: str, path_alternative: str="", logger=None) -> Dict[str, str]:
        """
        @summary: Reads, parses a text file where a set of attribute and the value pairs are 
          e.g. `/etc/os-release`, and returns a dict of the pairs.
        @param path: Primarily `/etc/os-release` is intended.
        @param path_alternative: Alternative path to try when `path` not found.
        """
        if not logger:
            logger = OsUtil._gen_logger()        
        try:
            filename = path
            f = open(filename)
        except FileNotFoundError:
            if path_alternative:
                return OsUtil.read_conf(path=path_alternative)

        os_release_data = {}
        for line_number, line in enumerate(f, start=1):
            line = line.rstrip()
            if not line or line.startswith('#'):
                continue

            m = re.match(r'([A-Z][A-Z_0-9]+)=(.+)', line)
            if m:
                name, val = m.groups()
                # Handle quoted values
                if val and val[0] in '\"\'':
                    try:
                        val = ast.literal_eval(val)
                    except (SyntaxError, ValueError):
                        # Fallback for simple cases or errors in literal_eval
                        val = val.strip('\"\'')
                os_release_data[name] = val
        f.close()
        return os_release_data
