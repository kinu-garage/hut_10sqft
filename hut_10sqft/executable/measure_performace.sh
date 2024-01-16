#/bin/sh

# Copyright 2017 Isaac I. Y. Saito.
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

iterate_command() {
  command=${1:-"rospack profile"};
  num_iteration=${2:-10000};
  for i in $(seq 1 ${num_iteration}); do
    echo "${i}th iteration.";
    $command;
  done
}

measure_performance() {
  command=${1:-"rospack profile"};
  num_iteration=${2:-100000};
  output_filename=${3:-"straceResult_${command// /-}_${num_iteration}_`date +%Y%m%d%H%M%S`.log"};
  echo "Command to be measured: ${command}";

  export ROS_CACHE_TIMEOUT=0.0 # Needed to not use cache.

  # strace doesn't easily call a function. http://unix.stackexchange.com/questions/339173/strace-not-finding-shell-function-with-cant-stat-error
  strace -o ${output_filename} -c -Ttt bash -c "$(typeset -f iterate_command); iterate_command '${command}' $num_iteration";
}

commando=${1:-"rospack profile"};
num_iteration=${2:-100000};
output_filename=${3:-straceResult_"${commando// /-}"_${num_iteration}_`date +%Y%m%d%H%M%S`.log};
measure_performance "$commando" $num_iteration $output_filename;
