DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR_THIS/ubuntu_common.bash

source $DIR_THIS/../ros/setup_ros_tork-kudu1.bash

# 20160716 git ssh issue https://github.com/130s/10sqft_hut/issues/64
# Added in https://github.com/130s/10sqft_hut/pull/65
if [ -f ~/.ssh/id_rsa ]; then ssh-add ~/.ssh/id_rsa; fi  # Key is for github
