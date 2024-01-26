DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR_THIS/rc_debian.bash

source $DIR_THIS/../ros/setup_ros_ubuntu_common.bash  # This uses env var DISTRO_ROS_LINUX.
