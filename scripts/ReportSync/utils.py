"""
Utility module for the ReportSync package.
Contains general utility functions.
"""

import sys
import subprocess


def ensure_dependencies():
    """
    Check if required packages are installed and install them if they're not.
    """
    required_packages = ['requests']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("All required packages installed successfully.")
        except Exception as e:
            print(f"Error installing packages: {str(e)}")
            print("Please install the following packages manually: " + ", ".join(missing_packages))
            sys.exit(1)


def get_user_confirmation(prompt):
    """
    Ask the user for confirmation.

    Returns:
        bool: True if the user confirms, False otherwise
    """
    while True:
        response = input(f"{prompt} (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'.")
