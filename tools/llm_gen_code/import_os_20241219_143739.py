import os
import pathlib

# Change current working directory
current_dir = pathlib.Path(r'C:\repo\remi')
os.chdir(current_dir)

# Function to recursively find Python and CSS files
def find_files(directory):
    try:
        # Use pathlib to recursively find .py and .css files
        for filepath in directory.rglob('*'):
            if filepath.suffix in ['.py', '.css']:
                print(filepath)
    except Exception as e:
        print(f"An error occurred while searching files: {e}")

# Execute file search
find_files(current_dir)