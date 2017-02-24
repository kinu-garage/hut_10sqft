## http://askubuntu.com/questions/21657/show-apt-get-installed-packages-history-via-commandline
### pars for fun: install | remove | rollback
function apt-history(){
      case "$1" in
        install)
              cat /var/log/dpkg.log | grep 'install '
              ;;
        upgrade|remove)
              cat /var/log/dpkg.log | grep $1
              ;;
        rollback)
              cat /var/log/dpkg.log | grep upgrade | \
                  grep "$2" -A10000000 | \
                  grep "$3" -B10000000 | \
                  awk '{print $4"="$5}'
              ;;
        *)
              cat /var/log/dpkg.log
              ;;
      esac
}

DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR_THIS/bash_setup_common.bash

source $DIR_THIS/../ros/setup_ros_ubuntu_common.bash  # This uses env var DISTRO_ROS_LINUX.

# 20160716 git ssh issue https://github.com/130s/10sqft_hut/issues/64
eval $(ssh-agent)  # This doesn't complete the solution to https://github.com/130s/10sqft_hut/issues/64. In the downstream bash config, ssh-add needs to be run with the path of specific ssh key files.

# For git
export EDITOR=emacs
