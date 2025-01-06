import subprocess
import pathlib

# Define the full path to the Python script
script_path = pathlib.Path(r"C:\repo\budget\analyze_budget.py")

# Verify the script exists before attempting to run it
if script_path.exists():
    try:
        # Run the Python script using subprocess
        result = subprocess.run(
            ["python", str(script_path)], 
            capture_output=True, 
            text=True
        )
        
        # Print stdout if there's any output
        if result.stdout:
            print("Script Output:")
            print(result.stdout)
        
        # Print stderr if there are any errors
        if result.stderr:
            print("Script Errors:")
            print(result.stderr)
        
    except Exception as e:
        # Catch and print any unexpected errors
        print(f"An error occurred while running the script: {e}")
else:
    print(f"Error: Script not found at {script_path}")