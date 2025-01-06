from pathlib import Path
import os

# Define the base directory
base_dir = Path("C:/repo/testsite")

# Change to the base directory
os.chdir(base_dir)

# Create directories
directories = [
    "static/css",
    "static/js", 
    "static/uploads", 
    "templates"
]

# Create directories with error handling
for dir_path in directories:
    full_path = base_dir / dir_path
    try:
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    except PermissionError:
        print(f"Permission denied: Could not create {full_path}")
    except Exception as e:
        print(f"Error creating {full_path}: {e}")