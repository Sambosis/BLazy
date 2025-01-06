import os
import pathlib

# Define the base directory
base_dir = pathlib.Path(r'C:\repo\remi')

# Change current working directory
os.chdir(base_dir)

# Create directories
directories = ['components', 'uploads']
for dir_name in directories:
    try:
        # Create directories with parents if they don't exist
        (base_dir / dir_name).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_name}")
    except Exception as e:
        print(f"Error creating directory {dir_name}: {e}")

# Create __init__.py file in components directory
init_file_path = base_dir / 'components' / '__init__.py'
try:
    # Create the file if it doesn't exist, or update its timestamp if it does
    init_file_path.touch(exist_ok=True)
    print(f"Created or updated file: {init_file_path}")
except Exception as e:
    print(f"Error creating __init__.py: {e}")