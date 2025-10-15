#! /usr/bin/env python3

# Copyright (C) 2025 Kinu Garage
# Licensed under Apache 2


class HostConf():
    def __init__(self, hostname, bash_cfg, emacs_cfg, sshkey_prv, sshkey_pub):
        self._hostname = hostname
        self._bash_cfg = bash_cfg
        self._emacs_cfg = emacs_cfg
        self._sshkey_prv = sshkey_prv
        self._sshkey_pub = sshkey_pub

    @property
    def hostname(self) -> str:
        return self._hostname

    @hostname.setter
    def hostname(self, v: str):
        self._hostname = v

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
