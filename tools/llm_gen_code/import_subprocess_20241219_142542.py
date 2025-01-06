import subprocess
import sys

def install_packages():
    packages = ['remi', 'matplotlib', 'pandas']
    
    try:
        # Use subprocess to call pip and install packages
        for package in packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"Successfully installed {package}")
    except subprocess.CalledProcessError as e:
        # Catch and print any installation errors without stopping script execution
        print(f"Error installing packages: {e}")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")

# Run the installation function
install_packages()