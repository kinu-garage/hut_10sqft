#! /usr/bin/env python3

# Copyright (C) 2026 Kinu Garage
# Licensed under Apache 2

import argparse

from hut_10sqft_lib.docker_utils import DockerUtil


def _cli_args():
    """
    @rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Stop the given Docker containers, forcefully terminating any "
                    "that do not respond to 'docker stop', then prune and list containers.")
    parser.add_argument(
        "container_names",
        nargs="+",
        help="Space-delimited list of Docker container names to stop and clean up.")
    return parser.parse_args()


def main():
    args = _cli_args()
    DockerUtil.clean_dead_containers(args.container_names)


if __name__ == "__main__":
    main()
