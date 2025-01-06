import subprocess
import sys
from pathlib import Path

def run_python_script():
    """
    Execute a Python script using subprocess
    
    Args:
        script_path (str): Full path to the Python script to execute
    """
    try:
        # Convert path to a Path object for better cross-platform handling
        script_path = Path('C:/repo/remi/modern_app.py')
        
        # Check if the script exists before attempting to run
        if not script_path.exists():
            print(f"Error: Script {script_path} does not exist.")
            return
        
        # Run the Python script using subprocess
        result = subprocess.run([sys.executable, str(script_path)], 
                                capture_output=True, 
                                text=True)
        
        # Print output if any
        if result.stdout:
            print("Script Output:")
            print(result.stdout)
        
        # Print any errors if they occurred
        if result.stderr:
            print("Script Errors:")
            print(result.stderr)
        
    except Exception as e:
        print(f"An error occurred while running the script: {e}")

# Execute the script
if __name__ == "__main__":
    run_python_script()