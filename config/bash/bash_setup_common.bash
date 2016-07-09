# For Mac, .bach_profile gets called.
# http://stackoverflow.com/questions/7780030/how-to-fix-terminal-not-loading-bashrc-on-os-x-lion

# 2016/05/18 http://stackoverflow.com/questions/59895/can-a-bash-script-tell-what-directory-its-stored-in
DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# BEGIN: commands to be run regardless interactiveness.

# 11/14/2012 To move pictures taken on android and synched via dropbox, to certain folder.
androidpic_mv() {
  TARGET_FOLDER=`date -d "$D" '+%m'`;  # This requires the ~/link/Current is set to the year folder (e.g. ~/data/Dropbox/GoogleDrive/gm130s_other/Periodic/GooglePhotos/2016/)
  mv ~/data/Dropbox/Camera\ Uploads/*.jpg ~/data/Dropbox/Camera\ Uploads/*.mp4 ~/link/Current/"${TARGET_FOLDER}";  # For some reason mv command does not like a whole directory as a variable, leading to this error http://stackoverflow.com/questions/26519301/bash-error-renaming-files-with-spaces-mv-target-is-not-a-directory

  # We like to discern files from Mio's folder so rename, simply just replacing whitespace with underscore.
  TMP_FOLDER_MIO='/tmp/mvimgfrommio'
  mkdir ${TMP_FOLDER_MIO};
  cd ${TMP_FOLDER_MIO};
  ##cp ~/data/Dropbox/SharedFromOthers/Camera\ Uploads\ from\ Mio/*.jpg ~/data/Dropbox/SharedFromOthers/Camera\ Uploads\ from\ Mio/*.mp4 ~/link/Current/${TARGET_FOLDER}/;
  mv -n ~/data/Dropbox/SharedFromOthers/Camera\ Uploads\ from\ Mio/*.jpg ~/data/Dropbox/SharedFromOthers/Camera\ Uploads\ from\ Mio/*.png ~/data/Dropbox/SharedFromOthers/Camera\ Uploads\ from\ Mio/*.mp4 ~/data/Dropbox/SharedFromOthers/Camera\ Uploads\ from\ Mio/*.mov ${TMP_FOLDER_MIO};
  counter=0
  for f in *; do mv "$f" "${f// /_}"; ((counter++)); done;
  mv -n * ~/link/Current/"${TARGET_FOLDER}" && echo "#${counter} files moved to ~/link/Current/${TARGET_FOLDER}";
  cd -;
}

# 3/3/2014 to include rm_dropbox_conflictfiles.bash
#export PATH=~/data/Dropbox/pg/Lateeye/bashapp:$PATH
export PATH=~/link/github_repos/130s/compenv_ubuntu/util:$PATH

# 6/9/2016 Workaround for tmux issue https://github.com/130s/compenv_ubuntu/issues/3
export DISPLAY=:0

# END: commands to be run regardless interactiveness.

# If not running interactively, don't do anything
[ -z "$PS1" ] && return  # 20160810  http://askubuntu.com/questions/352866/why-default-bashrc-is-set-to-return-immediately-if-not-running-interactively

# don't put duplicate lines in the history. See bash(1) for more options
# ... or force ignoredups and ignorespace
HISTCONTROL=ignoredups:ignorespace

# append to the history file, don't overwrite it
shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
#HISTSIZE=1000
#HISTFILESIZE=2000
#
# 2/21/2012/Change size of history: the commands previously used.
#  http://www.sacoskun.com/2011/10/how-to-enlarge-bash-history-size.html
HISTSIZE=5000
HISTFILESIZE=500000 #500KB
# 8/13/2013 For the length of scrollback on terminal, there might be no way to set it via bash script.
#           Follow http://ubuntuforums.org/showthread.php?t=1989298 or modify
#           /home/n130s/.gconf/apps/gnome-terminal/profiles/Default/%gconf.xml

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "$debian_chroot" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
#force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
	# We have color support; assume it's compliant with Ecma-48
	# (ISO/IEC-6429). (Lack of such support is extremely rare, and such
	# a case would tend to support setf rather than setaf.)
	color_prompt=yes
    else
	color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*)
    ;;
esac

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    #alias dir='dir --color=auto'
    #alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# some more ls aliases
#alias ll='ls -alF' # Original
alias ll='ls -aFhlt'
alias la='ls -A'
alias l='ls -CF'

# Add an "alert" alias for long running commands.  Use like so:
#   sleep 10; alert
alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi
if [ -f $DIR_THIS/bash_alias ]; then
    . $DIR_THIS/bash_alias ## 9/12/2011/Isaac. Updated 5/18/2016
fi

# 20160807 Following portion is updated by copying from Ubuntu 14.04 today.
# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

# Ignore cases on command line
#  http://www.unix.com/ubuntu/121570-set-completion-ignore-case-doesnt-work-bash.html
bind 'set completion-ignore-case on'
