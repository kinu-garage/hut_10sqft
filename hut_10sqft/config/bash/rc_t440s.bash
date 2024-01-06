DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export DISTRO_ROS_LINUX=kinetic  # Folder name of ROS work spaces at ~/link/ROS/

source $DIR_THIS/ubuntu_common.bash

source $DIR_THIS/../ros/setup_ros_t440s.bash
#export JAVA_HOME=/usr/lib/jvm/java-6-openjdk-amd64
export JAVA_HOME="/usr/lib/jvm/java-7-openjdk-amd64/jre"  # By Amazon EC2
