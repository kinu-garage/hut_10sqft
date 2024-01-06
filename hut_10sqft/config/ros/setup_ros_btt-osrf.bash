source ~/link/ROS/setup_ros_common.bash

#source ~/link/ROS/fuerte/setup_ros_dist.bash
source ~/link/ROS/groovy_quantal/setup_ros_dist.bash

export CMAKE_ECLIPSE_VERSION=4.2 # Eclipse Juno

# for dry pkgs
export ROS_PACKAGE_PATH=~/link/ROS/groovy_quantal/yet_catkinized_ws:$ROS_PACKAGE_PATH
