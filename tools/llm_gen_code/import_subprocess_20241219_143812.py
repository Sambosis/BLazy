import subprocess
import sys

# List of packages to install
packages = ['remi', 'matplotlib', 'pandas', 'pillow']

def install_packages():
    """
    Install specified Python packages using pip
    """
    try:
        # Use subprocess to run pip install command
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + packages)
        print("Successfully installed packages:", ', '.join(packages))
    except subprocess.CalledProcessError as e:
        # Catch and print installation errors without stopping script execution
        print(f"Error installing packages: {e}")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error during package installation: {e}")

# Run the package installation
install_packages()