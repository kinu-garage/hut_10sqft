#!/bin/bash
echo "Taken from https://docs.ros.org/en/kilted/Installation/Ubuntu-Install-Debs.html#enable-required-repositories"
echo "Set up ROS2 apt source. Main purpose is to enable rosdep."

# Takes an arg to remove sudo for apt commands
if [ "$1" == "nosudo" ]; then
    SUDO_CMD=""
else
    SUDO_CMD="sudo"
fi
$SUDO_CMD apt update && $SUDO_CMD apt install curl -y
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
$SUDO_CMD dpkg -i /tmp/ros2-apt-source.deb
