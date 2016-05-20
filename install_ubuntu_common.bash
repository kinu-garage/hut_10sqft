#!/bin/bash

set -x

#######################################
# Default error handling method that should be used throughout the script. With this function the process exits.
# http://stackoverflow.com/questions/64786/error-handling-in-bash
# Globals:
#   (None)
# Arguments:
#   _LINENO: Cane be obtained from envvar LINENO.
#   _ERR_MSG: Msg to explain the situation that error occurs.
#   _ERR_CODE: Posix error code. If -1 then won't exit.
# Returns:
#   None
#######################################
function error() {
  local _LINENO="$1"
  local _ERR_MSG="$2"
  local _ERR_CODE="${3:-1}"
  if [[ -n "$_ERR_MSG" ]] ; then
      echo "Error on or near line ${_LINENO}: ${_ERR_MSG}; Exiting with status code: ${_ERR_CODE}"
  else
      echo "Error on or near line ${_LINENO}; Exiting with status code: ${_ERR_CODE}"
  fi
  if [ $_ERR_CODE -ne "-1" ]; then exit "${_ERR_CODE}"; fi
}

function show_usage {
    echo >&2 "usage: $0 [hostname (default:130s-serval)] $1 [user accout (default:n130s)]"
    echo >&2 " [-h|--help] print this message"
    exit 0
}

function tmux_setup {
    FILENAME_TMUX_CONF_DEFAULT=~/.tmux.conf
    TMUXCONF_URL=https://raw.githubusercontent.com/130s/compenv_ubuntu/master/config/dot_tmux.conf
    TMUXCONF_FILENAME="${TMUXCONF_URL##*/}"
    cd ~ && wget $TMUXCONF_URL
    if [ -f $FILENAME_TMUX_CONF_DEFAULT ]; then
	echo "${FILENAME_TMUX_CONF_DEFAULT} already exists, so skipping using the downloaded conf."
    else
        mv $TMUXCONF_FILENAME $FILENAME_TMUX_CONF_DEFAULT
    fi
}

function install_eclipse() {
    TARBALL_ECLIPSE_URL=http://eclipse.mirror.rafal.ca/technology/epp/downloads/release/mars/2/eclipse-cpp-mars-2-linux-gtk-x86_64.tar.gz  # This needs to be updated whenever we want to use new version.
    TARBALL_ECLIPSE_NAME="${TARBALL_ECLIPSE_URL##*/}"
    NICKNAME_ECLIPSE="${TARBALL_ECLIPSE_NAME%.*}"
    TEMPDIR_ECLIPSE_DL=/tmp/eclipse_install
    mkdir $TEMPDIR_ECLIPSE_DL
    wget $TARBALL_ECLIPSE_URL -P $TEMPDIR_ECLIPSE_DL || error $LINENO "Failed to download Eclipse tarball from URL: ${TARBALL_ECLIPSE_URL}. Skipping Eclipse installation." -1
    cd $TEMPDIR_ECLIPSE_DL && tar xfvz $TARBALL_ECLIPSE_NAME
    (sudo mkdir /usr/share/eclipse && sudo mv $TEMPDIR_ECLIPSE_DL/eclipse /usr/share/eclipse/$NICKNAME_ECLIPSE) || error $LINENO "Failed to create eclipse folder under /usr/share. Skipping Eclipse installation." -1
    sudo ln -sf /usr/share/eclipse/$NICKNAME_ECLIPSE/eclipse /bin/eclipse || error $LINENO "Failed to create eclipse symlink. Skipping Eclipse installation." -1
}

# command line parse
OPT=`getopt -o h -l help -- $*`
if [ $? != 0 ]; then
    # If no arg, run show_usage function.
    show_usage
fi

trap 'error ${LINENO}' ERR SIGHUP SIGINT SIGTERM

export CI_SOURCE_PATH=$(pwd)
DIST_TRUSTY="Trusty"
DISTRO=$DIST_TRUSTY
HOSTNAME=${1-"130s-serval"}
PKG_TO_INSTALL=""

# For Japanese input.
##TODO if DISTRO < Saucy
PKG_JP_INPUT="ibus ibus-el ibus-mozc mozc-server emacs-mozc"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_JP_INPUT"
##TODO if Saucy <= DISTRO install fcitx

# oss dev
PKG_OSS_DEV="freecad git gitk iftop ipython meld mesa-utils meshlab ntp openjdk-7-jre python-catkin-tools"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_OSS_DEV"
# For ROS related tool
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu `lsb_release -sc` main" > /etc/apt/sources.list.d/ros-latest.list'
wget http://packages.ros.org/ros.key -O - | sudo apt-key add -

# Setup git account
cd ~
ln -sf ./config/dot_gitconfig ~/.gitconfig
ln -sf ./dot_gitignore_global ~/.gitignore_global

# Random tools
PKG_RANDOM_TOOLS="ack-grep aptitude dconf-editor debtree gnome-tweak-tool googleearth-package gtk-recordmydesktop indicator-multiload libavahi-compat-libdnssd1 nmap pdftk pidgin psensor ptex-base ptex-bin ssh sysinfo synaptic texlive-fonts-recommended texlive-latex-base tmux tree whois"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_RANDOM_TOOLS"

echo Installing $PKG_TO_INSTALL
sudo apt-get update
for i in $PKG_TO_INSTALL; do
  sudo apt-get install -y $i || error $i "apt-get install" -1
done

# Install synergy separately
FILENAME_SYNERGY_INSTALLER=synergy-v1.7.6-stable-bcb9da8-Linux-x86_64.deb?dl=0
wget https://www.dropbox.com/s/5d8vnnd0g72jfah/$FILENAME_SYNERGY_INSTALLER # stored in 130s private dropbox
sudo dpkg -i $FILENAME_SYNERGY_INSTALLER

# Install Dropbox
wget https://www.dropbox.com/download?dl=packages/ubuntu/dropbox_2015.10.28_amd64.deb && sudo dpkg -i download?dl=packages%2Fubuntu%2Fdropbox_2015.10.28_amd64.deb

# Install Google-Chrome
wget https://www.dropbox.com/s/8fc4z0zyea0wz5h/google-chrome-stable_current_amd64.deb?dl=0 && sudo dpkg -i google-chrome-stable_current_amd64.deb?dl=0

# Setup initial directory structure
cd ~
rm -fr Documents Music Pictures Public Templates Video # These folders are never used.
mkdir -p data
mkdir link && cd link && ln -sf ~/data/Dropbox/GoogleDrive/gm130s_other/Periodic/GooglePhotos/2016/ Current && ln -sf ~/data/Dropbox/GoogleDrive/1.TORK_Internal TORK && ln -sf ~/data/Dropbox/pg/myDevelopment/repo_tork_start github_repos && ln -sf ~/data/Dropbox/ROS ROS && ln -sf ~/data/Dropbox/GoogleDrive/gm130s_other/30y-130s 30y-130s

## App configs
# Autostart config
AUTOSTART_CONFIGS='gnome-system-monitor.desktop indicator-multiload.desktop'
AUTOSTART_CONFIGS_DIR=.config/autostart
for i in $AUTOSTART_CONFIGS; do
  wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/config/$i
done
if [ ! -d ~/$AUTOSTART_CONFIGS_DIR ]; then mkdir -p ~/$AUTOSTART_CONFIGS_DIR; fi
mv $AUTOSTART_CONFIGS ~/.config/autostart

# terminal config
cd ~/.gconf/apps && mv gnome-terminal gnome-terminal.default
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/config/gnome-terminal.config.tgz && tar xfvz gnome-terminal.config.tgz

# Setup terminal
cd ~
BASH_CONFIG_NAME=  # Initializing.
EMACS_CONFIG_NAME=  # Initializing.
case $HOSTNAME in
    "130s-serval")
	BASH_CONFIG_NAME="rc_130s-serval.bash"
	EMACS_CONFIG_NAME="emacs_130s-serval.el"
	;;
esac	
ln -sf $CI_SOURCE_PATH/config/bash/$BASH_CONFIG_NAME ~/.bashrc	

# Setup emacs
cd ~ && wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/dot_emacs_default && mv dot_emacs_default .emacs

# Setup tmux
tmux_setup

# DL and put Eclipse binary in PATH
install_eclipse
