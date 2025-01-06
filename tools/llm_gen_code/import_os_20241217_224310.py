import os
import subprocess
import sys
import pathlib

# Define the project directory
project_dir = pathlib.Path(r"C:/repo/testsite")

# Change to the project directory
try:
    os.chdir(project_dir)
    print(f"Changed directory to: {project_dir}")
except Exception as e:
    print(f"Error changing directory: {e}")
    # Continue execution despite directory change error

# Activate virtual environment
venv_path = project_dir / "venv" / "Scripts" / "activate_this.py"
try:
    # Use exec() to activate the virtual environment in-place
    exec(open(venv_path).read(), {'__file__': str(venv_path)})
    print("Virtual environment activated successfully")
except Exception as e:
    print(f"Error activating virtual environment: {e}")
    # Continue execution despite venv activation error

# Install requirements
try:
    requirements_path = project_dir / "requirements.txt"
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)], 
                   check=True, 
                   capture_output=True, 
                   text=True)
    print("Requirements installed successfully")
except subprocess.CalledProcessError as e:
    print(f"Error installing requirements: {e.stderr}")
    # Continue execution despite pip install error