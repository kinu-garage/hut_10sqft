#!/bin/bash

set -x

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
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/dot_bashrc_default && mv dot_bashrc_default .bashrc

# Setup emacs
cd ~
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/dot_emacs_default && mv dot_emacs_default .emacs

# For Japanese input.
##TODO if DISTRO < Saucy
PKG_JP_INPUT="ibus ibus-el ibus-mozc mozc-server emacs-mozc"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_JP_INPUT"
##TODO if Saucy <= DISTRO install fcitx

# oss dev
PKG_OSS_DEV="freecad git gitk iftop ipython meld mesa-utils meshlab ntp openjdk-7-jre python-catkin-tools"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_OSS_DEV"
# Setup git account
cd ~
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/dot_gitconfig && mv dot_gitconfig .gitconfig
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/dot_gitignore_global && mv dot_gitignore_global .gitignore_global

# Random tools
PKG_RANDOM_TOOLS="ack-grep aptitude dconf-editor debtree gnome-tweak-tool googleearth-package gtk-recordmydesktop indicator-multiload libavahi-compat-libdnssd1 nmap pdftk pidgin psensor ptex-base ptex-bin ssh sysinfo synaptic texlive-fonts-recommended texlive-latex-base tmux tree whois"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_RANDOM_TOOLS"

echo Installing $PKG_TO_INSTALL
for i in $PKG_TO_INSTALL; do
  sudo apt-get install -y $i
done

# Install synergy separately
FILENAME_SYNERGY_INSTALLER=synergy-v1.7.6-stable-bcb9da8-Linux-x86_64.deb?dl=0
wget https://www.dropbox.com/s/5d8vnnd0g72jfah/$FILENAME_SYNERGY_INSTALLER # stored in 130s private dropbox
sudo dpkg -i $FILENAME_SYNERGY_INSTALLER

# Install Dropbox
wget https://www.dropbox.com/download?dl=packages/ubuntu/dropbox_2015.10.28_amd64.deb && sudo dpkg -i download?dl=packages%2Fubuntu%2Fdropbox_2015.10.28_amd64.deb

# Setup initial directory structure
cd ~
rm -fr Documents Music Pictures Public Templates Video # These folders are never used.
mkdir -p data
mkdir link && cd link && ln -sf ~/data/Dropbox/GoogleDrive/gm130s_other/Periodic/GooglePhotos/2016/ Current && ln -sf ~/data/Dropbox/GoogleDrive/1.TORK_Internal TORK && ln -sf ~/data/Dropbox/pg/myDevelopment/repo_tork_start github_repos && ln -sf ~/data/Dropbox/ROS ROS && ln -sf ~/data/Dropbox/GoogleDrive/gm130s_other/30y-130s 30y-130s

# Autostart config
AUTOSTART_CONFIGS='gnome-system-monitor.desktop indicator-multiload.desktop'
for i in $AUTOSTART_CONFIGS; do
  wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/config/$i
done
mv $AUTOSTART_CONFIGS 
~/.config/autostart

# terminal config
cd ~/.gconf/apps && mv gnome-terminal gnome-terminal.default
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/config/gnome-terminal.config.tgz && tar xfvz gnome-terminal.config.tgz
