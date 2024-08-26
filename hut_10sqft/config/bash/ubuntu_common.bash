DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR_THIS/rc_debian.bash

# https://askubuntu.com/a/1144039/24203 via https://github.com/kinu-garage/hut_10sqft/issues/1077
xbindkeys -p

source $DIR_THIS/../ros/setup_ros_ubuntu_common.bash  # This uses env var DISTRO_ROS_LINUX.
