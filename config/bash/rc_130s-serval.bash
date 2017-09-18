DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export CMAKE_ECLIPSE_VERSION=4.4 # Eclipse Luner
export DISTRO_ROS_LINUX=kinetic  # Folder name of ROS work spaces at ~/link/ROS/

source $DIR_THIS/ubuntu_common.bash

source $DIR_THIS/../ros/setup_ros_serval.bash
