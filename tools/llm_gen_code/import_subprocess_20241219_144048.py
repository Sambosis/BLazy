import subprocess
import sys

def install_package(package_name):
    """
    Install a Python package using pip with error handling
    
    Args:
        package_name (str): Name of the package to install
    """
    try:
        # Use subprocess to run pip install command
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package_name], 
            capture_output=True, 
            text=True
        )
        
        # Check if installation was successful
        if result.returncode == 0:
            print(f"Successfully installed {package_name}")
        else:
            print(f"Error installing {package_name}:")
            print(result.stderr)
    
    except Exception as e:
        print(f"An unexpected error occurred while installing {package_name}: {e}")

# Install remi package
install_package('remi')