DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export CMAKE_ECLIPSE_VERSION=4.4 # Eclipse Lunar

# Requires the IP address statically assigned (by router/dhcp server etc.)
#export ROS_IP=192.168.0.15  # This gets tricky when a) multiple NICs are available b) dhcp isn't reliable.
