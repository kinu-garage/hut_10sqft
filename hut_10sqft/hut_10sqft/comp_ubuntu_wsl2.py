#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage

from hut_10sqft.comp_ubuntu import UbuntuOsSetup


class UbuntuOnWsl2Setup(UbuntuOsSetup):
    """Ubuntu setup tailored for WSL2 hosts."""

    def _setup_git_config_local(self):
        return "dot_gitconfig_local_il80d4kk"
