DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export CMAKE_ECLIPSE_VERSION=4.4 # Eclipse Luner
export DISTRO_ROS_LINUX=kinetic  # Folder name of ROS work spaces at ~/link/ROS/

source $DIR_THIS/ubuntu_common.bash

source $DIR_THIS/../ros/setup_ros_serval.bash

# 20160716 git ssh issue https://github.com/130s/hut_10sqft/issues/64
# Added in https://github.com/130s/hut_10sqft/pull/65
if [ -f ~/.ssh/id_rsa]; then ssh-add ~/.ssh/id_rsa; fi  # Key is for github

