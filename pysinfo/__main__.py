"""
Main entry point for PySinfo package. Allows running as a module with 'python -m pysinfo'.
"""

import argparse

from . import print_system_info


def main():
    parser = argparse.ArgumentParser(
        prog="pysinfo",
        description="Display system information with a platform logo.",
    )
    parser.add_argument(
        "-l", "--logo", metavar="OS",
        help="force a platform logo for preview: linux, windows, macos, bsd, default",
    )
    args = parser.parse_args()
    print_system_info(logo_os=args.logo)


if __name__ == "__main__":
    main()
