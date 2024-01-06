DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# setup for ROS common for all 130s machines.
source $DIR_THIS/setup_ros_common.bash

if [ -z ${DISTRO_ROS_LINUX} ]; then DISTRO_ROS_LINUX=indigo_trusty; fi

if [ -e ~/link/ROS/$DISTRO_ROS_LINUX/setup_ros_dist.bash ]; then
  source ~/link/ROS/$DISTRO_ROS_LINUX/setup_ros_dist.bash
fi
