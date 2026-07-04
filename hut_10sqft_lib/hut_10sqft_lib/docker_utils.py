#! /usr/bin/env python3

# Copyright (C) 2026 Kinu Garage
# Licensed under Apache 2

import logging
import subprocess
from typing import List, Tuple

from hut_10sqft_lib.os_util import OsUtil


class DockerUtil:
    """
    @summary: Utility for Docker container handling.
    """
    _LOGGER_NAME = "DockerUtil-logger"

    # Field delimiter used with `docker ps --format`.
    _FIELD_DELIM = "\t"

    def __init__(self, logger=None):
        if logger:
            self._logger = logger
        else:
            self._logger = DockerUtil._gen_logger()

    @staticmethod
    def _gen_logger(logger_name=_LOGGER_NAME, log_level=logging.DEBUG):
        logger = logging.getLogger(logger_name)
        log_handler = logging.StreamHandler()
        logger.setLevel(log_level)
        if not logger.hasHandlers():
            logger.addHandler(log_handler)
        return logger

    @staticmethod
    def _container_info(container_name: str, logger=None) -> Tuple[str, str, str]:
        """
        @summary: Returns metadata of a container so that a human-readable message
            can be composed.
        @return: (container_id, created, status). Any field that cannot be
            resolved is returned as an empty string.
        """
        if not logger:
            logger = DockerUtil._gen_logger()
        _fmt = "{{.ID}}" + DockerUtil._FIELD_DELIM + "{{.RunningFor}}" + DockerUtil._FIELD_DELIM + "{{.Status}}"
        output, error, ret_code = OsUtil.subproc_bash(
            f'docker ps -a --filter "name=^{container_name}$" --format "{_fmt}"', logger=logger)
        if ret_code != 0 or not output:
            logger.warning(f"Could not resolve metadata for container '{container_name}'. Error: {error}")
            return "", "", ""
        # A single container matches; take the first line just in case.
        fields = output.splitlines()[0].split(DockerUtil._FIELD_DELIM)
        # Pad in case docker omitted trailing fields.
        while len(fields) < 3:
            fields.append("")
        return fields[0], fields[1], fields[2]

    @staticmethod
    def _pid_of(container_name: str, logger=None) -> int:
        """
        @return: The host PID of a container's main process, or 0 when it cannot
            be resolved (e.g. the container is already gone).
        """
        if not logger:
            logger = DockerUtil._gen_logger()
        output, error, ret_code = OsUtil.subproc_bash(
            f"docker inspect --format '{{{{.State.Pid}}}}' {container_name}", logger=logger)
        try:
            return int(output.strip())
        except (ValueError, AttributeError):
            return 0

    @staticmethod
    def stop_container(container_name: str, logger=None) -> bool:
        """
        @summary: Attempts to stop a single container gracefully. If it does not
            respond to 'docker stop', its host process is forcefully killed.
        @return: True if the container was stopped gracefully, False if it had to
            be forcefully terminated (or could not be resolved).
        """
        if not logger:
            logger = DockerUtil._gen_logger()

        _output, _error, ret_code = OsUtil.subproc_bash(f"docker stop {container_name}", logger=logger)
        if ret_code == 0:
            logger.info(f"'docker stop {container_name}' succeeded, moving on to the next container.")
            return True

        # Not responding to 'docker stop'; gather info and forcefully terminate.
        cont_id, created, status = DockerUtil._container_info(container_name, logger=logger)
        logger.info(f'Container {container_name}, ID: {cont_id}, created {created}, {status}, '
                    f'is not responding to "docker stop". About to be forcifully stopped')

        pid = DockerUtil._pid_of(container_name, logger=logger)
        if pid > 0:
            logger.info(f"Forcifully terminating a dead container (name = {container_name}) on the PID: {pid}")
            OsUtil.subproc_bash(f"kill -9 {pid}", does_sudo=True, logger=logger)
        else:
            logger.warning(f"Could not resolve a valid PID for '{container_name}' (got {pid}); nothing to kill.")
        return False

    @staticmethod
    def _run_interactive(cmd: str, logger=None) -> int:
        """
        @summary: Runs a command while inheriting the current terminal's stdio so
            that the user can respond to prompts (e.g. 'docker container prune')
            and see the output directly.
        @return: The command's return code.
        """
        if not logger:
            logger = DockerUtil._gen_logger()
        logger.info(f"About to execute the interactive cmd: {cmd}")
        completed = subprocess.run(["/bin/bash", "-c", cmd])
        return completed.returncode

    @staticmethod
    def clean_dead_containers(container_names: List[str], logger=None) -> None:
        """
        @summary: For each given container name, stop it gracefully or forcefully,
            then prune stopped containers and print the resulting 'docker ps -a'.
        @param container_names: List of container names to stop.
        @raise ValueError: When no container names are passed.
        """
        if not logger:
            logger = DockerUtil._gen_logger()
        if not container_names:
            raise ValueError("No container names passed to 'clean_dead_containers'.")
        container_names = OsUtil._encapsulate_if_string(container_names)

        for container_name in container_names:
            DockerUtil.stop_container(container_name, logger=logger)

        # 'docker container prune' may prompt for approval, which the user should
        # react to, so run it interactively.
        DockerUtil._run_interactive("docker container prune", logger=logger)

        logger.info("Docker ps result")
        DockerUtil._run_interactive("docker ps -a", logger=logger)
