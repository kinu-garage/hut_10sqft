#/bin/sh

# Copyright 2017 Isaac I. Y. Saito.
# Copyright 2014-2015 kinugarage.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

PKGS="libopenni2-0 libopenni2-dev mongodb python-bson python-gridfs python-pymongo ros-hydro-bfl ros-hydro-bond ros-hydro-bondcpp ros-hydro-depth-image-proc ros-hydro-image-proc ros-hydro-nodelet ros-hydro-nodelet-topic-tools ros-hydro-openni2-camera ros-hydro-openni2-launch ros-hydro-pcl-ros ros-hydro-rgbd-launch ros-hydro-robot-pose-ekf ros-hydro-smclib ros-hydro-actionlib ros-hydro-actionlib-msgs ros-hydro-camera-calibration-parsers ros-hydro-camera-info-manager ros-hydro-collada-parser ros-hydro-collada-urdf ros-hydro-control-msgs ros-hydro-control-toolbox ros-hydro-controller-interface ros-hydro-cv-bridge ros-hydro-diagnostic-aggregator ros-hydro-diagnostic-msgs ros-hydro-diagnostic-updater ros-hydro-dynamic-reconfigure ros-hydro-eigen-conversions ros-hydro-ethercat-trigger-controllers ros-hydro-filters ros-hydro-gencpp ros-hydro-genlisp ros-hydro-genmsg ros-hydro-genpy ros-hydro-geometric-shapes ros-hydro-geometry-msgs ros-hydro-hardware-interface ros-hydro-hironx-moveit-config ros-hydro-hironx-ros-bridge ros-hydro-household-objects-database-msgs ros-hydro-hrpsys ros-hydro-hrpsys-ros-bridge ros-hydro-hrpsys-tools ros-hydro-image-geometry ros-hydro-image-transport ros-hydro-interactive-markers ros-hydro-joint-trajectory-action ros-hydro-kdl-conversions ros-hydro-kdl-parser ros-hydro-laser-geometry ros-hydro-manipulation-msgs ros-hydro-map-msgs ros-hydro-message-filters ros-hydro-message-generation ros-hydro-message-runtime ros-hydro-moveit-commander ros-hydro-moveit-core ros-hydro-moveit-msgs ros-hydro-moveit-planners ros-hydro-moveit-planners-ompl ros-hydro-moveit-ros ros-hydro-moveit-ros-benchmarks ros-hydro-moveit-ros-benchmarks-gui ros-hydro-moveit-ros-manipulation ros-hydro-moveit-ros-move-group ros-hydro-moveit-ros-perception ros-hydro-moveit-ros-planning ros-hydro-moveit-ros-planning-interface ros-hydro-moveit-ros-robot-interaction ros-hydro-moveit-ros-visualization ros-hydro-moveit-ros-warehouse ros-hydro-moveit-setup-assistant ros-hydro-nav-msgs ros-hydro-nextage-description ros-hydro-nextage-moveit-config ros-hydro-nextage-ros-bridge ros-hydro-object-recognition-msgs ros-hydro-octomap-msgs ros-hydro-openhrp3 ros-hydro-openrtm-aist ros-hydro-openrtm-aist-core ros-hydro-openrtm-aist-python ros-hydro-openrtm-tools ros-hydro-pcl-conversions ros-hydro-pcl-msgs ros-hydro-pluginlib ros-hydro-pr2-calibration-controllers ros-hydro-pr2-controller-interface ros-hydro-pr2-controller-manager ros-hydro-pr2-controllers ros-hydro-pr2-controllers-msgs ros-hydro-pr2-description ros-hydro-pr2-gripper-action ros-hydro-pr2-hardware-interface ros-hydro-pr2-head-action ros-hydro-pr2-mechanism-controllers ros-hydro-pr2-mechanism-diagnostics ros-hydro-pr2-mechanism-model ros-hydro-pr2-mechanism-msgs ros-hydro-pr2-moveit-plugins ros-hydro-pr2-msgs ros-hydro-python-qt-binding ros-hydro-qt-gui ros-hydro-qt-gui-py-common ros-hydro-realtime-tools ros-hydro-resource-retriever ros-hydro-robot-mechanism-controllers ros-hydro-robot-state-publisher ros-hydro-rosbag ros-hydro-rosbuild ros-hydro-rosconsole ros-hydro-rosconsole-bridge ros-hydro-roscpp ros-hydro-rosgraph-msgs ros-hydro-roslang ros-hydro-roslaunch ros-hydro-roslib ros-hydro-rosmsg ros-hydro-rosnode ros-hydro-rosout ros-hydro-rospack ros-hydro-rospy ros-hydro-rosservice ros-hydro-rostest ros-hydro-rostopic ros-hydro-rosunit ros-hydro-roswtf ros-hydro-rqt-console ros-hydro-rqt-gui ros-hydro-rqt-gui-py ros-hydro-rqt-logger-level ros-hydro-rqt-nav-view ros-hydro-rqt-py-common ros-hydro-rqt-robot-dashboard ros-hydro-rqt-robot-monitor ros-hydro-rtctree ros-hydro-rtmbuild ros-hydro-rtmros-nextage ros-hydro-rtshell ros-hydro-rtsprofile ros-hydro-rviz ros-hydro-sensor-msgs ros-hydro-shape-msgs ros-hydro-shape-tools ros-hydro-single-joint-position-action ros-hydro-std-msgs ros-hydro-std-srvs ros-hydro-tf ros-hydro-tf-conversions ros-hydro-tf2 ros-hydro-tf2-msgs ros-hydro-tf2-py ros-hydro-tf2-ros ros-hydro-topic-tools ros-hydro-trajectory-msgs ros-hydro-urdf ros-hydro-visualization-msgs ros-hydro-warehouse-ros ros-hydro-xacro"

for pkg in $PKGS
do
  PKG_NAME=$(echo $pkg)
  PKG_VER=$(dpkg -p $pkg | grep Ver)
  echo $PKG_NAME $PKG_VER
done