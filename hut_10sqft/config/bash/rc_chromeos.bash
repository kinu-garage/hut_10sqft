# This line needs to be absolute path.
source ~/.config/hut_10sqft/hut_10sqft/config/bash/rc_debian.bash

# 202401 Dumb solution to https://github.com/kinu-garage/hut_10sqft/issues/985#issuecomment-1911905752
PATH="/usr/lib/mozc/:$PATH"
alias mozc_conf_tool="mozc_tool --mode=config_dialog"
