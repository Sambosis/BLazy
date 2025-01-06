import os
import subprocess
import sys
from pathlib import Path

# Create directories
paths = [
    r"C:\repo\budget"
]

# Create directories with error handling
for path in paths:
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    except Exception as e:
        print(f"Error creating directory {path}: {e}")

# Install Python packages
try:
    # Use subprocess to run pip install command
    subprocess.run([sys.executable, "-m", "pip", "install", "pandas", "openpyxl", "numpy"], 
                   check=True, 
                   capture_output=True, 
                   text=True)
    print("Successfully installed pandas, openpyxl, and numpy")
except subprocess.CalledProcessError as e:
    print(f"Error installing packages: {e.stderr}")