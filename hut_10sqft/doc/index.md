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

## Usecase: Run a "Developer Test"

"Developer Test" here refers to the tests that the developers run to verify the functionality of the package `hut_10sqft`.

In the future the test steps may change but for now do the following in order to conduct dev test.

1. Open a Docker container.
   ```
   # export DOCKERIMG=python:3.12.5-slim-bullseye  # Docker images from `python` org doesn't seem to refer to the Python pkgs installed from `apt`, which is not great in my usecase so swtiched to Ubuntu image.
   export DOCKERIMG=ubuntu:jammy-20240808
   export PATH_LOCAL_WS=/home/n130s/workspace      # workspace is where the `hut_10sqft` repo is placed at.
   docker run -it --network host  \
     --volume $PATH_LOCAL_WS:/cws/src  \
     --volume /dev:/dev  \
     $DOCKERIMG bash
   ```
1. In the container, prepare for local installation using `pip`.
   ```
   cd /cws/src/hut_10sqft/hut_10sqft
   apt update && apt install -y python3-pip && echo "Upgrading pip seems necessary in order to allow building in editable mode."; python3 -m pip install --upgrade pip
   ```
1. Install the `hut_10sqft` pkg locally.
   ```
   pip install -e . hut_10sqft[dev]
   ```
1. Execute dev test for SUCO.
   ```
   pytest-3 -v test/test_suco.py
   ```
   
EoF