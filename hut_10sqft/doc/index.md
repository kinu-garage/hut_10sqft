# Package `hut_10sqft`

## Usecase: Setting up computer OS

Prerequisite:
- Any shell/terminal where an executable [`curl`](https://curl.se/), `python3` are available.

### Steps for Linux (Debian incl. ChromeOS / Ubuntu)

1. Execute the following command. Note: Above command set assumes `bash` and `apt`. TBD for other platform and package managers.
   ```
   $ export PATH_TMP_SUCO=~/.local/share/tmp_suco && \
     export PATH_VENV=~/.local/share/tmp_suco/venv && \
     sudo apt update && sudo apt install python3-venv && \
     mkdir -p $PATH_TMP_SUCO && cd $PATH_TMP_SUCO && python3 -m venv $PATH_VENV && source $PATH_VENV/bin/activate
   $ export SUCO_INSTALLER=/tmp/suco.py &&  \
     export VERSION=0.3.0 &&  \
     sudo apt update && sudo apt install -y curl git python3 python3-pip &&  \
     curl --output $SUCO_INSTALLER https://raw.githubusercontent.com/kinu-garage/hut_10sqft/$VERSION/hut_10sqft/hut_10sqft/suco_installer.py && chmod 755 $SUCO_INSTALLER && \
     export GIT_CONFIG_GLOBAL=''; export GIT_CONFIG_SYSTEM=''; $SUCO_INSTALLER --git_branch $VERSION
   $ export PATH_TMP_WS=~/.local/share/tmp_suco/colconws &&  \
     export HOST_NAME=130s-p16s-4 &&  \
     export OS_DiSTRO=Ubuntu &&  \
     source $PATH_TMP_WS/install/setup.bash && \
     cd $PATH_TMP_WS/src/hut_10sqft/hut_10sqft && python -m pip install setuptools && python setup.py install && cd $PATH_TMP_WS
   $ suco --hostname $HOST_NAME --os_distro $OS_DISTRO --conf_repo_version $VERSION
   $ echo "Removing a temp colcon ws dir".; rm -fr $PATH_TMP_WS
   ```
   Note as of v0.3.1, when re-running SUCO, running the whole set of lines, instead of resuming at certain line in the middle, is recommended.

   Customization:
   - `VERSION`: if you want to use non-standard branch/version.
   - `HOST_NAME`: Must be already defined in the code (e.g. 130s-p16s). Otherwise execution fails.
   - `OS_DISTRO`: Must be already defined in the code. Currently available options: [`ChromeOS` | `Debian` | `Ubuntu`]
1. At the end of the execution of the above command you should see the list of runtime issues that are captured during the run. Address those if possible.
1. Should be ready to start using the OS.

## Usecase: Run a "Developer's Test on the actual targeted environment"
Sometimes a deveoper may want to keep coding while testing on the actual targeted env.
1. Push the code change to the git remote server.
1. On the execution command, swap `VERSION` with the name of your branch e.g.:
   ```
   export VERSION=%YOUR_DEV_BRANCHNAME% &&  \
   ```
1. Execute the OS setup command.

Troubleshoot-1: Sometimes the downloaded execution .py file may not get updated even though you're sure you updated your branch on the remote.
This may happen with Github sends cache/old state. Dumb solution is to update the branch name on the remote.

### Steps for macOS

TBD

## Usecase: Run a "Developer's Unit Test"

"Developer Test" here refers to the tests that the developers run to verify the functionality of the package `hut_10sqft`.
In the future the test steps may change (e.g. as of now test relies on the entire package being packaged by `pip`) but for now do the following in order to conduct dev test.

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
   apt update && apt install -y git python3-pip && echo "Upgrading pip seems necessary in order to allow building in editable mode."; python3 -m pip install --upgrade pip
   cd /cws/src/hut_10sqft/hut_10sqft && echo "This is not duplicated, go to hut_10sqft/hut_10sqft."
   ```
1. Install the `hut_10sqft` pkg locally.
   ```
   pip install -e . hut_10sqft[dev]
   ```
1. Execute dev test for SUCO.
   ```
   pytest -v test/test_suco.py
   ```
   
EoF