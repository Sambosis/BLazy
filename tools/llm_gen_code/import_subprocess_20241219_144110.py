import subprocess
import sys

# List of packages to install
packages = ['matplotlib', 'pandas', 'numpy', 'pillow']

def install_packages(packages):
    """
    Install Python packages using pip
    
    Args:
        packages (list): List of package names to install
    """
    try:
        # Use subprocess to run pip install command
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + packages)
        print(f"Successfully installed: {', '.join(packages)}")
    except subprocess.CalledProcessError as e:
        # Print error message if installation fails, but don't terminate script
        print(f"Error installing packages: {e}")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error during package installation: {e}")

# Execute package installation
install_packages(packages)