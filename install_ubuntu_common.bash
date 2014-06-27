#!/bin/bash

DIST_TRUSTY="Trusty"
DISTRO=$DIST_TRUSTY

#sudo apt-get update

PKG_TO_INSTALL=""

# For Japanese input.
##TODO if DISTRO < Saucy
PKG_JP_INPUT="ibus mozc-server emacs-mozc"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_JP_INPUT"
##TODO if Saucy <= DISTRO install fcitx

# oss dev
PKG_OSS_DEV="git gitk meld"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_OSS_DEV"
# Setup git account
cd ~
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/dot_gitconfig && mv dot_gitconfig .gitconfig
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/dot_gitignore_global && mv dot_gitignore_global .gitignore_global

# Random tools
PKG_RANDOM_TOOLS="googleearth-package sysinfo synaptic"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_RANDOM_TOOLS"

echo Installing $PKG_TO_INSTALL
sudo apt-get install -y $PKG_TO_INSTALL

# Setup terminal

# Setup emacs
