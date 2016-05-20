DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# setup for ROS common for all 130s machines.
source $DIR_THIS/setup_ros_common.bash

if [ -e ~/link/ROS/jade_trusty/setup_ros_dist.bash ]; then
  source ~/link/ROS/jade_trusty/setup_ros_dist.bash
fi

export CMAKE_ECLIPSE_VERSION=4.3 # Eclipse Kepler
