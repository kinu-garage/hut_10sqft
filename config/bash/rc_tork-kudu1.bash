DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR_THIS/ubuntu_common.bash

source $DIR_THIS/../ros/setup_ros_tork-kudu1.bash

# 20160716 git ssh issue https://github.com/130s/compenv_ubuntu/issues/64
# https://github.com/130s/compenv_ubuntu/pull/65
ssh-add ~/.ssh/id_rsa  # This key is for github
