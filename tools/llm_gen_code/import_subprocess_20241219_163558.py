import subprocess
import sys
import pathlib

# Define the full absolute path to the Python script
script_path = pathlib.Path(r"C:\repo\budget\analyze_budget.py")

try:
    # Run the Python script using subprocess
    result = subprocess.run([sys.executable, str(script_path)], 
                             capture_output=True, 
                             text=True, 
                             check=True)
    
    # Print standard output if any
    if result.stdout:
        print(result.stdout)
    
    # Print standard error if any
    if result.stderr:
        print("Error output:", result.stderr)

except subprocess.CalledProcessError as e:
    # Handle execution errors without terminating the script
    print(f"Error running script: {e}")
    print(f"Return code: {e.returncode}")
    print(f"Standard output: {e.stdout}")
    print(f"Error output: {e.stderr}")
except FileNotFoundError:
    # Handle case where script file doesn't exist
    print(f"Script not found: {script_path}")
except Exception as e:
    # Catch any other unexpected errors
    print(f"An unexpected error occurred: {e}")