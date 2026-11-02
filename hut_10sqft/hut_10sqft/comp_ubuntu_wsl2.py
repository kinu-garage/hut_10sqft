#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage

from hut_10sqft.comp_debian import DebianSetup
from hut_10sqft.comp_ubuntu import UbuntuOsSetup


class UbuntuOnWsl2Setup(UbuntuOsSetup):
    """Ubuntu setup tailored for WSL2 hosts."""

    def _setup_git_config_local(self):
        return "dot_gitconfig_local_il80d4kk"

    def setup_swapfile(self, size_gb: int=DebianSetup.SIZE_SWAPFILE_GB_DEFAULT, path_swapfile: str=DebianSetup.PATH_SWAPFILE, skip=False) -> bool:
        self._logger.warning("Skipping swapfile setup on WSL2, as swap is configured in '.wslconfig' on the Windows host.")
        return False
