#!/bin/bash

export CI_SOURCE_PATH=$(pwd)
DIST_TRUSTY="Trusty"
DISTRO=$DIST_TRUSTY
HOSTNAME=${1-"130s-serval"}
DIR_ACTUALHOSTS_LINK=link/github_repos/130s  # This is the arbitrary directory path that 130s likes to use to the folder of this package.
export MSG_ENDROLL=  # Set of messages to be echoed at the end.
REPOSITORY_NAME="${TRAVIS_REPO_SLUG##*/}"
PKG_TO_INSTALL=""  # Initializing.
USER_UBUNTU="n130s"
USER_CI="travis"  # I'd want to use env vars, like $USER, but it's not recommended to depend on it. So user hardcoded. https://docs.travis-ci.com/user/environment-variables/#Default-Environment-Variables

set -x

echo "[DEBUG] ls: "; ls
mkdir -p ~/$DIR_ACTUALHOSTS_LINK
ln -sf $CI_SOURCE_PATH ~/$DIR_ACTUALHOSTS_LINK/$REPOSITORY_NAME  # As a workaround an issue e.g. https://travis-ci.org/130s/compenv_ubuntu/jobs/131835176#L3951, enable to access files at /home/travis/link/github_repos/130s/compenv_ubuntu.

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
    echo >&2 "usage: $0 [hostname (default:130s-serval)] $1 [user accout (default:${USER_UBUNTU})]"
    echo >&2 " [-h|--help] print this message"
    exit 0
}

function tmux_setup {
    FILENAME_TMUX_CONF_DEFAULT=dot_tmux.conf
    FILENAME_TMUX_CONF_TOBE_READ=.tmux.conf
    ln -sf $CI_SOURCE_PATH/conf/$FILENAME_TMUX_CONF_DEFAULT ~/$FILENAME_TMUX_CONF_TOBE_READ
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
    cd ~  # At the end of whatever the operation, we always go back to home.
}

#######################################
# This func copies ssh public and private keys from dropbox folder to ~/.ssh.
# With the potential of multiple key pairs on a single host, we're using specific name for pairs so that the commonly used default { id_rsa, id_rsa.pub } name is not encouraged (but still valid).
# This method returns 1 when key files are not available in the dropbox folder so that error handling may be needed by consumer scripts.
#
# Globals:
#   (None)
# Arguments:
#   (None)
# Returns:
#   1 if key files are not available in the dropbox folder.
#######################################
function ssh_github_setup() {
    SSH_KEY_PUB=${1:-id_rsa_tork-kudu1.pub}
    SSH_KEY_PRV=${2:-id_rsa_tork-kudu1}
    FILE_PATH_SSH_KEY_PUB=~/data/Dropbox/app/ssh/$SSH_KEY_PUB
    FILE_PATH_SSH_KEY_PRV=~/data/Dropbox/app/ssh/$SSH_KEY_PRV

    SSH_KEY_DIR=~/.ssh
    if [ ! -d ${SSH_KEY_DIR} ]; then mkdir -p ${SSH_KEY_DIR}; fi

    if [ -f ${FILE_PATH_SSH_KEY_PUB} ] && [ -f ${FILE_PATH_SSH_KEY_PRV} ]; then
        ln -sf ${FILE_PATH_SSH_KEY_PUB} ${SSH_KEY_DIR}
        ln -sf ${FILE_PATH_SSH_KEY_PRV} ${SSH_KEY_DIR}
    else
        _msg_failure="Seems like necessary files (~/data/Dropbox/app/ssh/${SSH_KEY_PUB} and ~/data/Dropbox/app/ssh/${SSH_KEY_PRV}) are not yet downloaded from Dropbox."
        echo $_msg_failure
        MSG_ENDROLL+=$_msg_failure
        return 1
    fi

    # Create ~/.ssh/config file to enable customized filenames.
    echo "Host github.com
      Port 22
        IdentityFile ~/.ssh/${SSH_KEY_PRV}
    " >> ~/.ssh/config

    #TODO test, exception handling
}

function ubuntu_set_autostart() {
    AUTOSTART_CONFIGS='gnome-system-monitor.desktop indicator-multiload.desktop'
    AUTOSTART_CONFIGS_DIR=.config/autostart
    for i in $AUTOSTART_CONFIGS; do
        wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/config/$i
    done
    if [ ! -d ~/$AUTOSTART_CONFIGS_DIR ]; then mkdir -p ~/$AUTOSTART_CONFIGS_DIR; fi
    mv $AUTOSTART_CONFIGS ~/.config/autostart
    #TODO test, exception handling
}

function install_docker() {
    RESULT=0  # success by default

    sudo groupadd docker
    sudo usermod -aG docker $USER_UBUNTU

    # http://answers.ros.org/question/212786/configure-python3-path-for-local-docker-prerelease-script/
    sudo apt-get install python3 python3-empy

    # From https://docs.docker.com/engine/installation/linux/ubuntulinux/
    sudo apt-get install apt-transport-https ca-certificates
    sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
    sudo sh -c 'echo "deb https://apt.dockerproject.org/repo ubuntu-`lsb_release -sc` main" > /etc/apt/sources.list.d/docker.list'
    sudo apt-get update
    sudo apt-get purge lxc-docker
    apt-cache policy docker-engine
    sudo apt-get install linux-image-extra-$(uname -r)
    # Workaround found at http://stackoverflow.com/questions/22957939/how-to-answer-an-apt-get-configuration-change-prompt-on-travis-ci-in-this-case
    sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confnew" install docker-engine
    sudo service docker start
    unset $DEBIAN_FRONTEND
    sudo docker run hello-world && echo "docker seems to be installed successfully." || (echo "Something went wrong with docker installation."; RESULT=1)

    return $RESULT
}

##
# Needed for running Eclipse, esp. pydev plugin. Otherwise not a desired resident on my machines.
#
function install_oraclejava() {
    # From http://askubuntu.com/a/55960/24203
    sudo apt-get install -y python-software-properties
    sudo apt-get update

    # Following probably needs to be done manually due to license sub window. Some tried but did not work:
    # - http://askubuntu.com/a/651045/24203
    # - http://superuser.com/a/939651/106974
    ## sudo add-apt-repository ppa:webupd8team/java
    ## apt-get install -y oracle-java8-installer
    ## sudo apt-get install oracle-java8-set-default
}

# Need to test https://github.com/130s/compenv_ubuntu/issues/3
function test_display_env() {
    # For Travis CI https://docs.travis-ci.com/user/gui-and-headless-browsers/#Using-xvfb-to-Run-Tests-That-Require-a-GUI
    sh -e /etc/init.d/xvfb start
    sleep 3  # give xvfb some time to start

    # If evince GUI can be run then return 0.
    evince . && return 0 || return 1
}

function _test_systems() {

    _test_commands
    retval_test_commands=$?
    if [ $retval_test_commands -ne 0 ]; then echo "Error: not all commands are installed yet. Exiting.o"; exit 1; fi
    
    if [ ! -z $MSG_ENDROLL ]; then printf $MSG_ENDROLL; else echo "Script ends."; fi

    #test_display_env  # 20160707 Comment out for now since the change in https://github.com/130s/compenv_ubuntu/pull/48 is really needed but don't yet know how to pass the test.
}

# command line parse
OPT=`getopt -o h -l help -- $*`
if [ $? != 0 ]; then
    # If no arg, run show_usage function.
    show_usage
fi

trap 'error ${LINENO}' ERR SIGHUP SIGINT SIGTERM

# For Japanese input.
##TODO if DISTRO < Saucy
PKG_JP_INPUT="ibus ibus-el ibus-mozc mozc-server emacs-mozc"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_JP_INPUT"
##TODO if Saucy <= DISTRO install fcitx

# oss dev
PKG_OSS_DEV="freecad gimp git gitk iftop ipython meld mesa-utils meshlab ntp openjdk-7-jre python-bloom python-catkin-tools python-rosdep python-wstool"
PKG_TO_INSTALL="$PKG_TO_INSTALL $PKG_OSS_DEV"
# For ROS related tool
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu `lsb_release -sc` main" > /etc/apt/sources.list.d/ros-latest.list'
wget http://packages.ros.org/ros.key -O - | sudo apt-key add -

# Setup git account
cd ~
ln -sf ./config/dot_gitconfig ~/.gitconfig
ln -sf ./dot_gitignore_global ~/.gitignore_global

# Random tools
PKG_RANDOM_TOOLS="ack-grep aptitude dconf-editor debtree evince gnome-tweak-tool googleearth-package gtk-recordmydesktop indicator-multiload libavahi-compat-libdnssd1 nmap pdftk pidgin psensor ptex-base ptex-bin ssh sysinfo synaptic texlive-fonts-recommended texlive-latex-base tmux tree whois"
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

# Install docker
install_docker
retval_install_docker=$?
if [ $retval_install_docker -ne 0 ]; then echo "Error: docker might have not been installed correctly. Skipping."; fi

# Setup initial directory structure
cd ~
rm -fr Documents Music Pictures Public Templates Videos # These folders are never used.
mkdir -p data
mkdir link && cd link && ln -sf ~/data/Dropbox/GoogleDrive/gm130s_other/Periodic/GooglePhotos/2016/ Current && ln -sf ~/data/Dropbox/GoogleDrive/1.TORK_Internal TORK && ln -sf ~/data/Dropbox/pg/myDevelopment/repo_tork_start github_repos && ln -sf ~/data/Dropbox/ROS ROS && ln -sf ~/data/Dropbox/GoogleDrive/gm130s_other/30y-130s 30y-130s

## App configs
ubuntu_set_autostart
# terminal config
cd ~/.gconf/apps && mv gnome-terminal gnome-terminal.default
wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/config/gnome-terminal.config.tgz && tar xfvz gnome-terminal.config.tgz

# Setup terminal
cd ~
BASH_CONFIG_NAME=  # Initializing.
EMACS_CONFIG_NAME=  # Initializing.
case $HOSTNAME in
    "130s-serval")
	BASH_CONFIG_NAME="bashrc_130s-serval"
	EMACS_CONFIG_NAME="emacs_130s-serval.el"

        SSH_KEY_PRV="id_rsa_130s-serval"
        SSH_KEY_PUB="id_rsa_130s-serval.pub"
	;;
    "130s-t440s")
	BASH_CONFIG_NAME="bashrc_130s-t440s"
	EMACS_CONFIG_NAME="emacs_130s-t440s.el"

        SSH_KEY_PRV="id_rsa_130s-t440s"
        SSH_KEY_PUB="id_rsa_130s-t440s.pub"
	;;
    "tork-kudu1")
	BASH_CONFIG_NAME="bashrc_tork-kudu1"
	EMACS_CONFIG_NAME="emacs_tork-kudu1.el"

        SSH_KEY_PRV="id_rsa_tork-kudu1"
        SSH_KEY_PUB="id_rsa_tork-kudu1.pub"
	;;
esac
cp $CI_SOURCE_PATH/config/bash/$BASH_CONFIG_NAME ~/.bashrc
ssh_github_setup
source ~/.bashrc

# Setup emacs
##cd ~ && wget https://raw.githubusercontent.com/130s/compenv_ubuntu/master/dot_emacs_default && mv dot_emacs_default .emacs
cp $CI_SOURCE_PATH/config/emacs/$EMACS_CONFIG_NAME ~/.emacs

# Setup display http://askubuntu.com/a/202481/24203
if [ -e ~/.dbus ]; then
    if [ -z ${TRAVIS} ]; then sudo chown -R $USER_UBUNTU:$USER_UBUNTU ~/.dbus;  # If this script does NOT run on Travis CI, we'll use pre-defined user.
    else sudo chown -R $USER_CI:$USER_CI ~/.dbus;
    fi
fi

# Setup tmux
tmux_setup

# setup ROS
sudo rosdep init && rosdep update
# symlink to cron job daily
sudo ln -sf $CI_SOURCE_PATH/config/ros/cron.daily_ros /etc/cron.daily

# DL and put Eclipse binary in PATH
install_oraclejava
install_eclipse

# Test some commands to check installation
source $CI_SOURCE_PATH/test/test_install.sh
