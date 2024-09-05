# Package `hut_10sqft`

## Usecase: Setting up computer OS

Prerequisite:
- Any shell/terminal where an executable [`curl`](https://curl.se/), `python3` are available.

Usage

1. Execute the following command. Note: Above command set assumes `bash` and `apt`. TBD for other platform and package managers.
   ```
   $ export INITOS=/tmp/hut_10sqft_os-setup.py &&  \
     export VERSION=develop  \
     export HOST_NAME=130s-C14-Morph  \
     export OSTYPE=ChromeOS  \
     export USERID=n130s  \
     sudo apt install -y curl python3  \
     curl --output $INITOS https://raw.githubusercontent.com/kinu-garage/hut_10sqft/$VERSION/hut_10sqft/src/hut_10sqft/init_setup.py && \
       chmod 755 $INITOS \
       $INITOS --hostname $HOST_NAME --os $OSTYPE --user_id $USERID
   ```
   Customization:
   - `VERSION`: if you want to use non-standard branch/version.
   - `HOST_NAME`: Must be already defined in the code (e.g. 130s-p16s). Otherwise execution fails.
   - `OSTYPE` Must be already defined in the code. Currently available options: [`ChromeOS` | `Debian` | `Ubuntu`]
1. At the end of the execution of the above command you should see the list of runtime issues that are captured during the run. Address those if possible.
1. Should be ready to start using the OS.

EoF