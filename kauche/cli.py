"""Console entry point: `kauche` -> the same CLI as scripts/kauche.py."""
import os
import runpy
import sys


def main():
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "kauche.py")
    sys.argv[0] = script
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
