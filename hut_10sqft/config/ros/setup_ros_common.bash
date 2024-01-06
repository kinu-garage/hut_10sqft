# Easily modify ROS_MASTER_URI
# Usage: set_pr2 pri
function set_roscore ()  {
if [ ! -z $1 ]
then
   export ROS_MASTER_URI="http://$1:11311"
fi
echo $ROS_MASTER_URI
}

# For default editor for rosed
export EDITOR='emacs -nw &'

# This doesn't work with metapackage that is introduced since ROS Groovy
function rosgitsha ()  {
if [ ! -z $1 ]
then
   more `rospack find $1`/.git/FETCH_HEAD
fi
}

# 11/7/2012 Util @ Willow
grep_cpp() { grep -r --include=*.{cpp,h} "$1" `pwd`; }
grep_py() { grep -r --include=*.py "$1" `pwd`; }
grep_launch() { grep -r --include=*.launch "$1" `pwd`; }
grep_xml() { grep -r --include=*.xml "$1" `pwd`; }
