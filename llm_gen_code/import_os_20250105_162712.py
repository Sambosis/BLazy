import os
import venv
import pathlib
import subprocess

def create_project_environment():
    try:
        # Create the project directory
        project_path = pathlib.Path(r"C:\repo\testsite2")
        
        # Create directory if it doesn't exist
        project_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {project_path}")
        
        # Change current working directory
        os.chdir(project_path)
        print(f"Changed current directory to: {project_path}")
        
        # Create virtual environment
        venv_path = project_path / "venv"
        venv.create(venv_path, with_pip=True)
        print(f"Created virtual environment in: {venv_path}")
        
        # Activate virtual environment (Python equivalent)
        # Note: In Python, activation is typically done by modifying sys.path and environment
        activate_this = venv_path / "Scripts" / "activate_this.py"
        exec(open(activate_this).read(), {'__file__': str(activate_this)})
        print("Virtual environment activated")
        
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the function
if __name__ == "__main__":
    create_project_environment()