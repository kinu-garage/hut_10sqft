DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export CMAKE_ECLIPSE_VERSION=4.4 # Eclipse Luner
export DISTRO_ROS_LINUX=kinetic  # Folder name of ROS work spaces at ~/link/ROS/

source $DIR_THIS/ubuntu_common.bash

# 20241220 Unreal Engine https://github.com/kinu-garage/hut_10sqft/issues/861 this path is only available on p16s as of now.
#export PATH=~/pg/unreal-engine/UnrealEngine/Engine/Binaries/Linux/:$PATH
# 20250120 Switched to prebuilt UE5.1 https://github.com/kinu-garage/hut_10sqft/issues/1147#issuecomment-2602321043
export PATH=~/pg/unreal-engine/prebuilt_UE/unreal-engine-5.1.1_prebuilt/Engine/Binaries/Linux/:$PATH
