# Willow Garage ROS
## 9/15/2012 ROS' setup is delegated to setup_ros.bash
###source /opt/ros/diamondback/setup.bash
###source /opt/ros/electric/setup.bash
###source /opt/ros/fuerte/setup.bash

## 4/1/2012/For cram_ros  ROS_Workspace/Shared_MultiHosts_ROS_Workspace/
##  This shouldn't come later than other .bash file that add environmental variable esp. ROS_PACKAGE_PATH.
## source ~/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/3rdParty_ROS/cram_ros/setup.bash ## 5/14/2012 commented out since we don't use this often, moreover, this statement causes ENV VARs to become electric for some reason.

##for 130s' work
###source /home/n130s/data/Dropbox/contents_nomadic/Career/JobTaken/Toyota-ITC/ROS_OpenCV_Toyota-ITC/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/setup_ros.bash

export JAVA_HOME=/usr/lib/jvm/java-1.7.0-openjdk-amd64

# For git
export EDITOR=emacs
