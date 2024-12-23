DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export CMAKE_ECLIPSE_VERSION=4.4 # Eclipse Luner
export DISTRO_ROS_LINUX=kinetic  # Folder name of ROS work spaces at ~/link/ROS/

source $DIR_THIS/ubuntu_common.bash

# 20241220 Unreal Engine https://github.com/kinu-garage/hut_10sqft/issues/861 this path is only available on p16s as of now.
export PATH=~/pg/unreal-engine/UnrealEngine/Engine/Binaries/Linux/:$PATH
