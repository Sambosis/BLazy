import os
import subprocess
import pathlib

# Change to the specified directory
repo_path = pathlib.Path(r"C:\repo\remi")
os.chdir(repo_path)

# List of packages to install
packages = [
    "remi", 
    "matplotlib", 
    "pandas", 
    "pillow", 
    "numpy"
]

try:
    # Install packages using pip
    subprocess.run([
        "pip", "install"] + packages, 
        check=True, 
        capture_output=True, 
        text=True
    )
    
    # Run the Python script
    subprocess.run([
        "python", "modern_app.py"
    ], check=True)

except subprocess.CalledProcessError as e:
    # Handle potential errors without stopping entire execution
    print(f"An error occurred: {e}")
    print(f"Error output: {e.stderr}")