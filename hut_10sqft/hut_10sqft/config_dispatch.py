#! /usr/bin/env python3

# Licensed under Apache 2
# Copyright (C) 2025 Kinu Garage


class ConfigDispatch():
    """Need for the setter of each entry is questionable in the beginning though"""
    def __init__(self, path_source, path_dest=None, is_symlink=False, necessary=True, hint_enable=""):
        """
        @param necessary: If True, when the path in `path_source` not found then the accessor should raise an error.
        @param hint_enable: Hint to enable the symlink creation, e.g. how to set up a mount on to Google Drive directory from Linux container on ChromeOS.
        """
        self._path_source = path_source
        self._path_dest = path_dest
        self._is_symlink = is_symlink
        self._necessary = necessary
        self._hint_enable = hint_enable

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

    @property
    def necessary(self) -> bool:
        return self._necessary

    @necessary.setter
    def necessary(self, v: bool):
        self._necessary = v

    @property
    def hint_enable(self) -> str:
        return self._hint_enable
