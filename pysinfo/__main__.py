"""
Main entry point for PySinfo package. Allows running as a module with 'python -m pysinfo'.
"""

from . import print_system_info

if __name__ == "__main__":
    print_system_info()