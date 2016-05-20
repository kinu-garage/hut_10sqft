DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# setup for ROS common for all 130s machines.
source $DIR_THIS/setup_ros_common.bash

source ~/link/ROS/indigo_trusty/setup_ros_dist.bash
#source ~/link/ROS/jade_trusty/setup_ros_dist.bash

export CMAKE_ECLIPSE_VERSION=4.4 # Eclipse Lunar
