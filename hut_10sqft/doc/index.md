# Package `hut_10sqft`

## Usecase: Setting up computer OS

Prerequisite:
- Any shell/terminal where `python3` and `git` (or `curl`) are available.

### Quickstart (Fresh Machine or Remote Setup)

1. Clone or update the configuration repository to `~/.config/hut_10sqft` using the standard Python installer:
   ```bash
   $ export VERSION=develop  # Or a release version e.g. "0.6.0"
   $ curl -sSL https://raw.githubusercontent.com/kinu-garage/hut_10sqft/$VERSION/hut_10sqft/hut_10sqft/suco_installer.py | python3 - --git_branch $VERSION
   ```

2. Execute SUCO. Specify the target `OS_DISTRO` (`ChromeOS`, `Debian`, or `Ubuntu`):
   ```bash
   $ export OS_DISTRO=Ubuntu  # [ChromeOS | Debian | Ubuntu | MacOS]
   $ cd ~/.config/hut_10sqft && python3 -m hut_10sqft.suco_main --os_distro $OS_DISTRO
   ```

   *Notes on OS and Host identification:*
   - `OS_DISTRO` is required to distinguish ChromeOS from generic Debian (since ChromeOS Crostini runs inside a Debian container that identifies as Debian at the OS level). On standard Ubuntu/Debian, it can also fall back to auto-detection if omitted.
   - `--hostname` is automatically detected from the system (e.g., `130s-p16s-4`), but can still be explicitly specified if needed (`--hostname $HOST_NAME`).

### Local Checkout or Development (Pip-Installable)

When working from a local clone of `hut_10sqft`:
```bash
$ pip install -e .
$ suco --os_distro $OS_DISTRO
```
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
