import sys

from hut_10sqft.init_setup import CompInitSetup


def main():
    # Check Python environment
    print("Python sys.path: {}".format(sys.path))
    comp_setup = CompInitSetup()
    comp_setup.main()

if __name__ == "__main__":
    main()
