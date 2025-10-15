#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage

from hut_10sqft.comp_debian import AbstCompSetupFactory


class WindowsSetup(AbstCompSetupFactory):
    def __init__(self, os_name):
        raise NotImplementedError()
