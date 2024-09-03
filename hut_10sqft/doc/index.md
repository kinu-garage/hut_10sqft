# Package `hut_10sqft`

## Usecase: Setting up computer OS

1. Open any shell/terminal that can run [`curl`](https://curl.se/). If it's not available on Debian/Ubuntu, get it installed by executing `sudo apt install -y curl`.
1. Execute the following command:
   ```
   $ export INITOS=/tmp/hut_10sqft_os-setup.py && \
     export VERSION=feat-inittool-chromeos
     curl --output $INITOS https://raw.githubusercontent.com/kinu-garage/hut_10sqft/$VERSION/hut_10sqft/src/hut_10sqft/init_setup.py && \
     chmod 755 $INITOS
     $INITOS --hostname chrome-test --os ChromeOS --user_id n130s
   ```
1. TBD

EoF