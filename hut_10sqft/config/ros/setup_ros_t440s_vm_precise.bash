# setup for ROS common for all 130s machines.
source ~/link/ROS/setup_ros_common.bash

#source ~/link/ROS/fuerte_precise/setup_ros_dist.bash
source ~/link/ROS/groovy_precise/setup_ros_dist.bash
#source ~/link/ROS/groovy_precise_rb/setup_ros_dist.bash
#source ~/link/ROS/groovy_quantal/setup_ros_dist.bash
#source ~/link/ROS/hydro_precise/setup_ros_dist.bash
#source ~/link/ROS/hydro_raring/setup_ros_dist.bash

export CMAKE_ECLIPSE_VERSION=4.3 # Eclipse Kepler

#rosjava 3/10/2013
#export PATH=$JAVA_HOME/bin:/opt/google/android/adt-bundle-linux-x86_64-20130219/sdk/tools:/opt/google/android/adt-bundle-linux-x86_64-20130219/sdk/platform-tools:$PATH
#source /home/n130s/data/Dropbox/ROS/groovy_quantal/catkin_ws/src/rosjava_work/setup.bash
#export CLASSPATH=$CLASSPATH:/opt/google/android/adt-bundle-linux-x86_64-20130219/sdk/tools
#sudo killall java

# Android rosjava 4/29/2013
##export ANDROID_HOME=/opt/google/android/adt-bundle-linux-x86_64-20130219/sdk
##export PATH=$ANDROID_HOME/tools:$PATH
##export PATH=$ANDROID_HOME/platform-tools:$PATH
