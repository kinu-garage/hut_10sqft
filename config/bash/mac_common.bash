DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source $DIR_THIS/bash_setup_common.bash

# Enable git tab-completion
# http://apple.stackexchange.com/questions/55875/git-auto-complete-for-branches-at-the-command-line
if [ -f $DIR_THIS/git-completion.bash ]; then
  . $DIR_THIS/git-completion.bash
fi
