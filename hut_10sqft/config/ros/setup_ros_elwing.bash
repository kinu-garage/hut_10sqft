###source /opt/ros/diamondback/setup.bash
###source /opt/ros/electric/setup.bash
source /opt/ros/fuerte/setup.bash

export PYTHONPATH=$ROS_ROOT/core/roslib/src:$PYTHONPATH

# Includes ROS host setup. This bash file should be host independent.
## source /home/t130s/.ros/setup_ros.bash
## 10/21/2011 decided to write directly in .bashrc for now since it's difficult to write host independent info and share automatically via dropbox.

##export ROS_PACKAGE_PATH=~/link/bosch-ros-pkg-sourceforge:~/link/bosch-ros-pkg:~/link/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/3rdParty_ROS/bosch-stack/bosch-ros-pkg-sourceforge:~/link/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/Tutorial_ROS:~/link/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/3rdParty_ROS:~/link/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/ROS-stack-custom:$ROS_PACKAGE_PATH
export ROS_PACKAGE_PATH=~/data/Dropbox/pg/Lateeye/ProvingGround_C++/qtRosTest:~/data/Dropbox/pg/Lateeye/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/3rdParty_ROS/bosch-stack/remote_farming/remotefarming_ui:~/data/Dropbox/pg/Lateeye/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/3rdParty_ROS/tum/mapping:~/data/Dropbox/pg/Lateeye/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/3rdParty_ROS/bosch-stack/bosch-ros-pkg/stacks/pr2_laundrybot:~/data/Dropbox/pg/Lateeye/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/3rdParty_ROS/bosch-stack/prove_bosch/pr2_gazebo_bosch_test:~/link/bosch-ros-pkg-sourceforge:~/link/bosch-ros-pkg:~/link/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/3rdParty_ROS/bosch-stack/bosch-ros-pkg-sourceforge:$ROS_PACKAGE_PATH

## 4/1/2012/For cram_ros  ROS_Workspace/Shared_MultiHosts_ROS_Workspace/
##  This shouldn't come later than other .bash file that add environmental variable esp. ROS_PACKAGE_PATH.
## source ~/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/3rdParty_ROS/cram_ros/setup.bash ## 5/14/2012 commented out since we don't use this often, moreover, this statement causes ENV VARs to become electric for some reason.
