# setup for ROS common for all 130s machines.
source ~/link/ROS/setup_ros_common.bash

if [ -e ~/link/ROS/jade_trusty/setup_ros_dist.bash ]; then
  source ~/link/ROS/jade_trusty/setup_ros_dist.bash
fi

export CMAKE_ECLIPSE_VERSION=4.3 # Eclipse Kepler
