import os
import venv
from pathlib import Path

# Define the base directory path
base_path = Path("C:/repo/testsite")

# Create the directory if it doesn't exist
try:
    # Create the directory with parents (equivalent to mkdir -p)
    base_path.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {base_path}")
except Exception as e:
    print(f"Error creating directory: {e}")

# Change current working directory
try:
    os.chdir(base_path)
    print(f"Changed working directory to: {base_path}")
except Exception as e:
    print(f"Error changing directory: {e}")

# Create virtual environment
try:
    # Use venv to create a virtual environment
    venv.create(base_path / "venv", with_pip=True)
    print(f"Created virtual environment in: {base_path}/venv")
except Exception as e:
    print(f"Error creating virtual environment: {e}")