import os
import subprocess
import sys
import venv
from pathlib import Path

def create_project():
    try:
        # Define the project directory path
        project_path = Path(r'C:\repo\testsite2')
        
        # Create the project directory (equivalent to mkdir -p)
        project_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {project_path}")
        
        # Change current working directory
        os.chdir(project_path)
        print(f"Changed working directory to: {project_path}")
        
        # Create virtual environment
        venv_path = project_path / 'venv'
        venv.create(venv_path, with_pip=True)
        print(f"Created virtual environment in: {venv_path}")
        
        # Upgrade pip
        venv_python = venv_path / 'Scripts' / 'python.exe'
        subprocess.run([str(venv_python), '-m', 'pip', 'install', '--upgrade', 'pip'], 
                       check=True)
        print("Upgraded pip")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        # We don't use sys.exit() to allow main program to continue

if __name__ == '__main__':
    create_project()