#!/bin/bash

function show_usage {
    echo >&2 "usage: $0 [user accout (default:n130s)]"
    echo >&2 " [-h|--help] print this message"
    exit 0
}

# command line parse
OPT=`getopt -o h -l help -- $*`
if [ $? != 0 ]; then
    # If no arg, run show_usage function.
    show_usage
fi

DIST_TRUSTY="Trusty"
DISTRO=$DIST_TRUSTY

sudo apt-get update

PKG_TO_INSTALL=""

# Setup terminal
cd ~
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/dot_bashrc_default .bashrc

# Setup emacs
cd ~
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/dot_emacs_default .emacs

# For Japanese input.
##TODO if DISTRO < Saucy
PKG_JP_INPUT="ibus ibus-el ibus-mozc mozc-server emacs-mozc"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_JP_INPUT"
##TODO if Saucy <= DISTRO install fcitx

# oss dev
PKG_OSS_DEV="git gitk ipython meld ntp openjdk-7-jre"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_OSS_DEV"
# Setup git account
cd ~
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/dot_gitconfig && mv dot_gitconfig .gitconfig
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/dot_gitignore_global && mv dot_gitignore_global .gitignore_global

# Random tools
PKG_RANDOM_TOOLS="ack-grep dconf-editor gnome-tweak-tool googleearth-package gtk-recordmydesktop indicator-multiload nmap pdftk pidgin psensor ssh sysinfo synaptic tree"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_RANDOM_TOOLS"

echo Installing $PKG_TO_INSTALL
sudo apt-get install -y $PKG_TO_INSTALL
