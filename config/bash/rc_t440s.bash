DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source $DIR_THIS/ubuntu_common.bash

source $DIR_THIS/../ros/setup_ros_t440s.bash
#export JAVA_HOME=/usr/lib/jvm/java-6-openjdk-amd64
export JAVA_HOME="/usr/lib/jvm/java-7-openjdk-amd64/jre"  # By Amazon EC2

# 20160716 git ssh issue https://github.com/130s/compenv_ubuntu/issues/64
# Added in https://github.com/130s/compenv_ubuntu/pull/65
if [ -f ~/.ssh/id_rsa]; then ssh-add ~/.ssh/id_rsa_130s-t440s; fi  # Key is for github
