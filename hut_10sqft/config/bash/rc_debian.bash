## http://askubuntu.com/questions/21657/show-apt-get-installed-packages-history-via-commandline
### pars for fun: install | remove | rollback
function apt-history(){
      case "$1" in
        install)
              cat /var/log/dpkg.log | grep 'install '
              ;;
        upgrade|remove)
              cat /var/log/dpkg.log | grep $1
              ;;
        rollback)
              cat /var/log/dpkg.log | grep upgrade | \
                  grep "$2" -A10000000 | \
                  grep "$3" -B10000000 | \
                  awk '{print $4"="$5}'
              ;;
        *)
              cat /var/log/dpkg.log
              ;;
      esac
}

DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR_THIS/bash_setup_common.bash

# 20160716 git ssh issue https://github.com/130s/hut_10sqft/issues/64
eval $(ssh-agent) >> /dev/null  # This doesn't complete the solution to https://github.com/130s/hut_10sqft/issues/64. In the downstream bash config, ssh-add needs to be run with the path of specific ssh key files.

# For git
export EDITOR=emacs

# 20160716 git ssh issue https://github.com/130s/hut_10sqft/issues/64
# Added in https://github.com/130s/hut_10sqft/pull/65
# 20170916 To workaround https://github.com/130s/hut_10sqft/issues/67#issuecomment-330153887 upon scp, tentatively decided to comment this out. Each time accessing remote server that requires password (e.g. github.com), manually run ssh-add command (only once per terminal).
#if [ -f ~/.ssh/id_rsa ]; then ssh-add ~/.ssh/id_rsa; fi  # Key is for github

# 20210518 Temp workaround(?) for pip install not adding binary to PATH. See https://gitlab.com/git-org/git-group/sub-group/-/merge_requests/71/diffs#note_577327855
PATH="$HOME/.local/bin/:$PATH"
